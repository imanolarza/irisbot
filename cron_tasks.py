# Favor mantener el orden con las importaciones de la siguiente manera en orden alfabético:
# 1er bloque; librerías de discord
import discord
from discord.ext import tasks
# 2do bloque; librerías nativas del python
from calendar import monthrange
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

# 3er bloque; otras librerías no nativas
import wikiquote

# 4to bloque; modulos del proyecto
from json_operations import load_json, update_json
from main import bot

# CronJobs
@bot.event
async def on_ready():
    tema_diario_cron.start()
    purgar_cron.start()

# Cron tema semanal (Recuperado)
@tasks.loop(minutes=1)
async def tema_diario_cron():
    print('check tema diario')

    now = datetime.now().astimezone(tz=timezone.utc)
    enviar = False
    data = load_json()
    channel = bot.get_channel(data['channel_id'])
    role_id = data['role_id']
    execute_date = False

    if data['execute_date']:
        execute_date = datetime.fromtimestamp(data['execute_date']).astimezone(tz=timezone.utc)

        if now >= execute_date:
            enviar = True

    if data['forced']:
        update_json('forced', False)
        enviar = True

    if enviar and len(data['temas']):
        print('sent tema semanal')

        if execute_date:
            update_json('execute_date', execute_date.replace(day=(now + timedelta(days=7)).day).timestamp())

        embed = discord.Embed(
            title='⚡ Tema de la semana',
            description=f'## "{data["temas"][0]["name"]}"\n' +
                f'➜ Puedes responder en <#{data["temas"][0]["channel_id"]}>'
        )
        embed.set_footer(text='¡Recuerda seguir normas de convivencia e invitar a tus amigos!')

        try:
            quote = wikiquote.qotd(lang='es')

            embed.add_field(
                name='Frase de la semana',
                value=
                    '> [' + {quote[0].replace('\n', ' ').replace('»',' ').replace('«',' ')} +
                    f'](https://es.wikiquote.org/wiki/Portada)\n{quote[1]})'
            )

        except Exception as e:
            print(e)

        await channel.send(embed=embed, content=f'<@&{role_id}>' if role_id else None)

        used_tema = data['temas'][0]
        used_tema['id'] = len(data['used_temas']) + 1

        new_used_temas = data['used_temas'].copy()
        new_used_temas.append(used_tema)

        update_json('used_temas', new_used_temas)
        data['temas'].pop(0)
        update_json('temas', data['temas'])

# Cron de purgador
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
