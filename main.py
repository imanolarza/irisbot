import os
import discord
from discord import app_commands
from discord.ui import Select, View
from discord.ext import commands, tasks

from json_operations import load_json, update_json
import datetime
from datetime import timezone
from calendar import monthrange
from dateutil.relativedelta import relativedelta

from datetime import time, timedelta
from webserver import keep_alive
import wikiquote


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
bot = commands.Bot(intents=intents, command_prefix='t!')

def gen_embed(name, quote, quote_author, quote_source, image_url, color):
    res = discord.Embed(description="# ⚡ Tema diario\n ## %s" % name,
                        color=int(color))

    res.add_field(name='Frase del día', value='> %s\n**%s**(%s)' % (quote, quote_author, quote_source), inline=False)
    res.set_footer(text="¡Recuerda seguir normas de convivencia e invitar a tus amigos!")
    res.set_image(url=image_url)

    return res

@tasks.loop(hours=24)
async def inactive_members():
    print('INICIANDO: Proceso de miembros inactivos')
    guild_id = await bot.fetch_guild(1146162590163140668)
    members = guild_id.fetch_members(limit=None)
    now = datetime.datetime.now().astimezone(tz=timezone.utc)
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
    update_json('last_inactive_members', datetime.datetime.now().astimezone(tz=timezone.utc).timestamp())

    print('FINALIZADO: Proceso de miembros inactivos')

@tasks.loop(minutes=1)
async def cronjob():
    print('check tema diario')
    enviar = False
    data = load_json()
    channel = bot.get_channel(data['channel_id'])
    role_id = data['role_id']
    execute_date = False

    if data['execute_date']:
        execute_date = datetime.datetime.fromtimestamp(data['execute_date']).astimezone(tz=timezone.utc)

        if datetime.datetime.now().astimezone(tz=timezone.utc) >= execute_date:
            enviar = True

    if data['forced']:
        update_json('forced', False)
        enviar = True

    if enviar and len(data['temas']):
        print('sent tema diario')

        if execute_date:
            update_json('execute_date', execute_date.replace(day=(execute_date + timedelta(days=1)).day).timestamp())

        quote = wikiquote.qotd(lang='es')
        embed = gen_embed(
            data['temas'][0]['name'],
            quote[0].replace('\n', ' ').replace('»',' ').replace('«',' '), quote[1],
            '[es.wikiquote.org](https://es.wikiquote.org/wiki/Portada)',
            data['temas'][0]['image_url'], int(data['temas'][0]['color'])
        )
        used_tema = data['temas'][0]
        used_tema['id'] = len(data['used_temas']) + 1

        new_used_temas = data['used_temas'].copy()
        new_used_temas.append(used_tema)

        update_json('used_temas', new_used_temas)
        data['temas'].pop(0)
        update_json('temas', data['temas'])

        await channel.send(embed=embed, content=f'<@&{role_id}>' if role_id else None)

temas = app_commands.Group(name='temas', description='Tema diario')
faq_admin = app_commands.Group(name='faq_admin', description='Preguntas Frecuentes admin')

@bot.event
async def on_ready():
    try:
        bot.tree.add_command(temas)
        bot.tree.add_command(faq_admin)

        synced = await bot.tree.sync()

        print(f'sincronizado(s) {len(synced)} comando(s)')
    except Exception as e:
        print(e)

    cronjob.start()
    inactive_members.start()

    print(f'Loggeado como {bot.user}')


@temas.command(name='canal', description='Setear canal')
@app_commands.describe(canal='¿En qué canal debería ir el tema diario?')
async def canal(interaction: discord.Interaction, canal: discord.TextChannel = None):
    data = load_json()

    if canal:
        res = update_json('channel_id', canal.id)

        await interaction.response.send_message(
            'canal del tema diario **actualizado a** <#%s>' % res['channel_id']
        )
    else:
        if data['channel_id']:
            await interaction.response.send_message('canal del tema diario **actual es** <#%s>' % data['channel_id'])
        else:
            await interaction.response.send_message('¡canal del tema diario sin especificar!')

@temas.command(name='hora', description='Setear hora')
@app_commands.describe(valor='Hora deseada. Formato hh:mm UTC')
async def hora(interaction: discord.Interaction, valor: str = ''):
    data = load_json()['execute_date']

    if valor != '':
        now = datetime.datetime.now().astimezone(tz=timezone.utc)

        new_hour = int(valor.split(':')[0])
        new_minute = int(valor.split(':')[1])

        if data:
            current_execute_date = datetime.datetime.fromtimestamp(data).astimezone(tz=timezone.utc)
            new_execute_date = current_execute_date.replace(hour=new_hour, minute=new_minute)

            update_json('execute_date', new_execute_date.timestamp())

            await interaction.response.send_message(new_execute_date)

        else:
            res = datetime.datetime.now().astimezone(tz=timezone.utc).replace(
                hour=new_hour, minute=new_minute, second=0, microsecond=0
            )

            if now.time() > res.time():
                res = res.replace(day=(now + timedelta(days=1)).day)

            update_json('execute_date', res.timestamp())
    else:
        if data:
            await interaction.response.send_message(
                'El tema diario se ejecutará el <t:%s:f>(<t:%s:R>)' % (int(data), int(data))
            )
        else:
            await interaction.response.send_message('Hora sin especificar')


@temas.command(name='desactivar', description='Desactivar tema diario')
async def hora(interaction: discord.Interaction):
    update_json('execute_date', False)

    await interaction.response.send_message('¡Tema diario desactivado!')


@temas.command(name='lista', description='Lista de temas a ejecutar')
async def lista(interaction: discord.Interaction, usados: bool = False):
    data = load_json()['temas'] if not usados else load_json()['used_temas']

    if len(data):
        await interaction.response.send_message('\n'.join(['%s. %s' % (data.index(i) + 1, i['name']) for i in data]))
    else:
        await interaction.response.send_message('¡No hay temas %s!' % ('pendientes' if not usados else 'usados'))


@temas.command(name='agregar', description='Agregar tema diario')
@app_commands.describe(tema='Título del tema diario que desea')
@app_commands.describe(imagen='URL de la imagen')
@app_commands.describe(color='código de color HEX sin "#". Ejemplo: ff00ff')
async def agregar(interaction: discord.Interaction, tema: str, imagen: str, color: str):
    data = load_json()['temas']

    new_id = len(data) + 1
    new_data = data.copy()

    new_data.append({
        'id': new_id,
        'name': tema,
        'image_url': imagen,
        'color': int(color, 16)
    })

    update_json('temas', new_data)

    embed = gen_embed(name=tema, quote='', quote_author='', quote_source='', image_url=imagen, color=int(color, 16))

    await interaction.response.send_message(
        embed=embed, content='# ¡Tema diario agregado con éxito! \n previsualización:'
    )


@temas.command(name='eliminar', description='Eliminar tema diario')
@app_commands.describe(posicion='Posición del tema')
async def eliminar(interaction: discord.Interaction, posicion: int):
    data = load_json()['temas']
    new_data = data.copy()

    if posicion and int(posicion):
        new_data.pop(int(posicion) - 1)

        res = update_json('temas', new_data)

        await interaction.response.send_message(res)


@temas.command(name='forzar', description='Forzar tema diario')
@app_commands.describe(seguro='¿Está seguro de que desea forzar el tema diario?')
@app_commands.choices(seguro=[
    app_commands.Choice(name='Sí', value='Si'),
    app_commands.Choice(name='No', value='No')
])
async def forzar(interaction: discord.Integration, seguro: str):
    if seguro == 'Si':
        update_json('forced', True)

        await interaction.response.send_message('el tema diario se enviará en breve :]')
    else:
        await interaction.response.send_message('Operación cancelada', ephemeral=True)


@temas.command(
    name='rol',
    description='¿Qué rol debería mencionar al ejecutar tema diario?')
@app_commands.describe(rol='Rol a mencionar')
async def rol(interaction: discord.Integration, rol: discord.Role = None):
    data = load_json()['role_id']

    if rol:
        update_json('role_id', rol.id)

        await interaction.response.send_message(f'Rol cambiado a {rol}')
    else:
        if data:
            await interaction.response.send_message(f'Rol asignado: <@&{data}>')
        else:
            await interaction.response.send_message('¡Rol aún no seteado!')

@bot.tree.command(name='miembros')
async def miembros(interaction: discord.Interaction):
    data = load_json()

    inactive_members = data['inactive_members']
    not_found_members = data['not_found_members']
    last_inactive_members = data['last_inactive_members']

    embed = discord.Embed(
        colour=int('5ec2bf', 16), title='⛔ Usuarios inactivos',
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

# INICIAR BOT
my_secret = os.environ['TOKEN']
# keep_alive()

bot.run(my_secret)
