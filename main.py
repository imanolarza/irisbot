# Favor mantener el orden con las importaciones de la siguiente manera en orden alfabético:
# 1er bloque; librerías de discord
import discord
from discord import app_commands
from discord.ext import commands, tasks

# 2do bloque; librerías nativas del python
from calendar import monthrange
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import logging
import os

# 3er bloque; otras librerías no nativas

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

logger  = logging.getLogger('discord')

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
    logger.info('INICIANDO: Proceso de miembros inactivos')
    guild_id = await bot.fetch_guild(1146162590163140668)
    members = guild_id.fetch_members(limit=None)
    now = datetime.now().astimezone(tz=timezone.utc)
    start_date = now - relativedelta(months=2, day=1)
    end_date = now - relativedelta(months=2)
    end_date = end_date.replace(day=monthrange(end_date.year, end_date.month)[1])
    end_date_history = now - relativedelta(months=1)
    end_date_history = end_date_history.replace(day=monthrange(end_date_history.year, end_date_history.month)[1])

    logger.info('Miembros desde y mensajes desde: %s Hasta miembros: %s Hasta mensajes:%s' % (
        start_date.strftime('%d/%m/%Y'), end_date.strftime('%d/%m/%Y'), end_date_history.strftime('%d/%m/%Y')
    ))

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

    logger.info('FINALIZADO: Proceso de miembros inactivos')

@tasks.loop(minutes=1)
async def bump_cron():
    try:
        logger.info('Chequeo de bump')
        data = load_json()
        now = datetime.now()

        if data['next_bump']:
            logger.info('Aviso de bump encontrado!')
            next_bump = datetime.fromtimestamp(data['next_bump'])

            if next_bump < now:
                update_json('next_bump', 0)

                embed = discord.Embed(
                    title='Hora de hacer bump!', color=info_color, description='</bump:947088344167366698>'
                )

                await bot.get_channel(1146178546771955803).send(embed=embed, content='@everyone')

                logger.info('Enviado aviso de bump')

        elif not data['next_bump']:
            logger.info('Aviso de bump no encontrado, apagando')

            bump_cron.stop()
    except Exception as e:
        bump_cron.restart()
        logger.error(e)

@bot.event
async def on_ready():
    synced = await bot.tree.sync()

    logger.info(f'sincronizado(s) {len(synced)} comando(s)')
    try:
        bump_cron.start()
        purgar_cron.start()
    except Exception as e:
        # Si hay un error, lo imprimirá
        logger.error(e)

    logger.info(f'Loggeado como {bot.user}')

@bot.event
async def on_message(msg):
    if (
        msg.type == discord.MessageType.chat_input_command and
        msg.author.id == 302050872383242240 and
        msg.channel.id == 1146178546771955803
    ):
        if len(msg.embeds):
            embed = msg.embeds[0]

            if embed.description.find('Bump done!') != -1:
                next_bump = int((datetime.now() + relativedelta(hours=2)).timestamp())

                if not bump_cron.is_running():
                    bump_cron.start()

                update_json('next_bump', next_bump)

                embed = discord.Embed(title="Avisador de bumps reiniciado!", color=success_color)
                embed.add_field(name='Próximo aviso', value='<t:%s:t>' % next_bump)

                await msg.channel.send(embed=embed)

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

@bot.tree.command(name='reiniciar_bump')
async def reiniciar_bump(interaction: discord.Interaction):
    data = load_json()
    next_bump = data['next_bump']

    embed = discord.Embed()

    if next_bump:
        embed.color = error_color
        embed.title = 'No es posible reiniciar manualmente, el próximo bump es <t:%s:R>' % next_bump
    elif not next_bump:
        update_json('next_bump', int((datetime.now() + relativedelta(hours=2)).timestamp()))
        embed.color = success_color
        embed.title = 'Avisador de bumps reiniciado!'
        embed.add_field(
            name='Próximo aviso', value='<t:%s:t>' % int((datetime.now() + relativedelta(hours=2)).timestamp())
        )

        if not bump_cron.is_running():
            bump_cron.start()

    await interaction.response.send_message(embed=embed, ephemeral=bool(next_bump))

# INICIAR BOT:
my_secret = os.environ['TOKEN']

bot.run(my_secret)