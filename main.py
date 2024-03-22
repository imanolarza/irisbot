# Favor mantener el orden con las importaciones de la siguiente manera en orden alfabético:
# 1er bloque; librerías de discord
import discord
from discord import app_commands
from discord.ext import commands, tasks

# 2do bloque; librerías nativas del python
from calendar import monthrange
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import os

# 3er bloque; otras librerías no nativas
import wikiquote

# 4to bloque; modulos del proyecto
from json_operations import load_json
# from cogs import temas, puntos, strikes
from config import info_color, error_color, success_color
from json_operations import load_json, update_json

# Inicialización del bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(intents=intents, command_prefix='ir!')

# Definición de categoría de tema semanal. Demomento solo funciona un comando para testear
# TODO: Volverlo a implementar

# Evento al iniciar bot
coglist = ['cogs.puntos', 'cogs.strikes', 'cogs.tema_semanal']

@bot.event
async def setup_hook():
    for ext in coglist:
        await bot.load_extension(ext)

@tasks.loop(hours=24)
async def purgar_cron():
    print('INICIANDO: Proceso de miembros inactivos')
    guild_id = await bot.fetch_guild(1146162590163140668)
    members = guild_id.fetch_members(limit=None)
    now = datetime.now().astimezone(tz=timezone.utc)
    start_date = now - relativedelta(months=2, day=1)
    end_date = now - relativedelta(months=2)
    end_date.replace(day=monthrange(end_date.year, end_date.month)[1])
    end_date_history = now - relativedelta(months=1)
    end_date_history.replace(day=monthrange(end_date_history.year, end_date_history.month)[1])

    new_members = {}
    async for member in members:
        if ((member.joined_at >= start_date and member.joined_at <= end_date) and not member.bot):
            new_members[str(member.id)] = []

    channel_id = await bot.fetch_channel(1146162590163140671)
    async for message in channel_id.history(limit=None, after=start_date, before=end_date_history):
        if str(message.author.id) in new_members.keys():
            new_members[str(message.author.id)].append(message)

    not_found_members = []
    inactive_members = []

    for new_member, messages in new_members.items():
        try:
            if messages[-1].type == discord.MessageType.new_member:
                inactive_members.append(new_member)
        except IndexError:
            not_found_members.append(new_member)

    update_json('inactive_members', inactive_members)
    update_json('not_found_members', not_found_members)
    update_json('last_inactive_members', datetime.now().astimezone(tz=timezone.utc).timestamp())

    print('FINALIZADO: Proceso de miembros inactivos')

@bot.event
async def on_ready():
    synced = await bot.tree.sync()

    print(f'sincronizado(s) {len(synced)} comando(s)')
    try:
        purgar_cron.start()
    except Exception as e:
        # Si hay un error, lo imprimirá
        print(e)

    print(f'Loggeado como {bot.user}')

# Definición de comandos
# Coamndos de bot

# Sincronizar
@bot.tree.command(name='sync')
async def sync(interaction: discord.Interaction):
    synced = await bot.tree.sync()

    await interaction.response.send_message(f'sincronizado(s) {len(synced)} comando(s)')

# Purgador (Restaurado)
@bot.tree.command(name='purgar')
async def miembros(interaction: discord.Interaction):
    data = load_json()

    inactive_members = data['inactive_members']
    not_found_members = data['not_found_members']
    last_inactive_members = data['last_inactive_members']

    embed = discord.Embed(
        colour=info_color, title='⛔ Usuarios inactivos',
        description=
            '**razón(copiar):** ||```Periodo de inactividad superado `(30 días)`. '
            'Si crees que fue un error, o consideras volver a ingresar al servidor, '
            'lo puedes hacer mediante esta invitación: https://discord.gg/rcKvswqgsH```||'
        )
    embed.add_field(name='Usuarios inactivos', value="%s" % '\n'.join(f'- <@{int(m)}>' for m in inactive_members))
    embed.add_field(
        name='Usuarios sin mensaje de bienvenida', value="%s" % '\n'.join(f'- <@{int(m)}>' for m in not_found_members)
    )
    embed.add_field(
        name='Actualizado por última vez', value='<t:%s:R>' % (int(last_inactive_members)),
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# Tema semanal (restaurado)
# temas = app_commands.Group(name='temas', description='Tema semanal')
# TODO: Integrar de vuelta los comandos (adicionando información municiosamente a cada fragmento de código) hallados en ./main.py.old

# INICIAR BOT:
my_secret = os.environ['TOKEN']

# Inicia el servidor. Solamente disponible para REPLIT
# keep_alive()

bot.run(my_secret)