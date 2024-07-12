# Favor mantener el orden con las importaciones de la siguiente manera en orden alfabético:
# 1er bloque; librerías de discord
import discord
from discord import app_commands
from discord.ext import commands, tasks

# 2do bloque; librerías nativas del python
from datetime import datetime, timedelta, timezone
import logging

# 3er bloque; otras librerías no nativas
import wikiquote

# 4to bloque; modulos del proyecto
from json_operations import load_json, update_json

logger  = logging.getLogger('discord')

class TemasCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    # Cron tema semanal (Recuperado)
    @tasks.loop(minutes=5)
    async def tema_diario_cron(self):
        logger.info('Chequeo de tema semanal')

        now = datetime.now().astimezone(tz=timezone.utc)
        enviar = False
        data = load_json()
        channel = self.client.get_channel(data['channel_id'])
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
            logger.info('sent tema semanal')

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
                logger.error(e)

            await channel.send(embed=embed, content=f'<@&{role_id}>' if role_id else None)

            used_tema = data['temas'][0]
            used_tema['id'] = len(data['used_temas']) + 1

            new_used_temas = data['used_temas'].copy()
            new_used_temas.append(used_tema)

            update_json('used_temas', new_used_temas)
            data['temas'].pop(0)
            update_json('temas', data['temas'])

    @commands.Cog.listener()
    async def on_ready(self):
        self.tema_diario_cron.start()

    temas = app_commands.Group(name='temas', description='Tema semanal')

    @temas.command(name='canal', description='Setear canal')
    @app_commands.describe(canal='¿En qué canal debería ir el tema semanal?')
    @app_commands.checks.has_permissions(administrator=True)
    async def canal(self, interaction: discord.Interaction, canal: discord.TextChannel = None):
        data = load_json()

        if canal:
            res = update_json('channel_id', canal.id)

            await interaction.response.send_message(
                'canal del tema semanal **actualizado a** <#%s>' % res['channel_id']
            )
        else:
            if data['channel_id']:
                await interaction.response.send_message('canal del tema semanal **actual es** <#%s>' % data['channel_id'])
            else:
                await interaction.response.send_message('¡canal del tema semanal sin especificar!')

    @temas.command(name='hora', description='Setear hora')
    @app_commands.describe(valor='Hora deseada. Formato hh:mm UTC')
    @app_commands.checks.has_permissions(administrator=True)
    async def hora(self, interaction: discord.Interaction, valor: str = ''):
        data = load_json()['execute_date']

        if valor != '':
            now = datetime.now().astimezone(tz=timezone.utc)

            new_hour = int(valor.split(':')[0])
            new_minute = int(valor.split(':')[1])

            if data:
                current_execute_date = datetime.fromtimestamp(data).astimezone(tz=timezone.utc)
                new_execute_date = current_execute_date.replace(hour=new_hour, minute=new_minute)

                update_json('execute_date', new_execute_date.timestamp())

                await interaction.response.send_message(new_execute_date)

            else:
                res = datetime.now().astimezone(tz=timezone.utc).replace(
                    hour=new_hour, minute=new_minute, second=0, microsecond=0
                )
                logger.info(res)

                if now.time() > res.time():
                    res = res + timedelta(days=7)

                update_json('execute_date', res.timestamp())
        else:
            if data:
                await interaction.response.send_message(
                    'El tema semanal se ejecutará el <t:%s:f>(<t:%s:R>)' % (int(data), int(data))
                )
            else:
                await interaction.response.send_message('Hora sin especificar')


    @temas.command(name='desactivar', description='Desactivar tema semanal')
    @app_commands.checks.has_permissions(administrator=True)
    async def desactivar(self, interaction: discord.Interaction):
        update_json('execute_date', False)

        await interaction.response.send_message('¡Tema semanal desactivado!')


    @temas.command(name='lista', description='Lista de temas a ejecutar')
    async def lista(self, interaction: discord.Interaction, usados: bool = False):
        data = load_json()['temas'] if not usados else load_json()['used_temas']

        if len(data):
            await interaction.response.send_message('\n'.join(['%s. %s' % (data.index(i) + 1, i['name']) for i in data]))
        else:
            await interaction.response.send_message('¡No hay temas %s!' % ('pendientes' if not usados else 'usados'))


    @temas.command(name='agregar', description='Agregar tema semanal')
    @app_commands.describe(tema='Título del tema semanal que desea')
    @app_commands.describe(channel_id='Canal a responder, ejemplo, #general')
    async def agregar(self, interaction: discord.Interaction, tema: str, channel_id: discord.TextChannel):
        data = load_json()['temas']

        new_id = len(data) + 1
        new_data = data.copy()

        new_data.append({'id': new_id, 'name': tema, 'channel_id': channel_id.id})

        update_json('temas', new_data)

        embed = discord.Embed(
            title='⚡ Tema de la semana',
            description=f'## "{tema}"\n' + '➜ Puedes responder en <#%s>' % channel_id.id
        )
        await interaction.response.send_message(
            embed=embed, content='# ¡Tema semanal agregado con éxito! \n previsualización:'
        )


    @temas.command(name='eliminar', description='Eliminar tema semanal')
    @app_commands.describe(posicion='Posición del tema')
    @app_commands.checks.has_permissions(administrator=True)
    async def eliminar(self, interaction: discord.Interaction, posicion: int):
        data = load_json()['temas']
        new_data = data.copy()

        if posicion and int(posicion):
            new_data.pop(int(posicion) - 1)

            res = update_json('temas', new_data)

            await interaction.response.send_message(res)

    @temas.command(name='forzar', description='Forzar tema semanal')
    @app_commands.describe(seguro='¿Está seguro de que desea forzar el tema semanal?')
    @app_commands.choices(seguro=[
        app_commands.Choice(name='Sí', value='Si'),
        app_commands.Choice(name='No', value='No')
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def forzar(self, interaction: discord.Integration, seguro: str):
        if seguro == 'Si':
            update_json('forced', True)

            await interaction.response.send_message('el tema semanal se enviará en breve :]')
        else:
            await interaction.response.send_message('Operación cancelada', ephemeral=True)


    @temas.command(name='rol', description='¿Qué rol debería mencionar al ejecutar tema semanal?')
    @app_commands.describe(rol='Rol a mencionar')
    @app_commands.checks.has_permissions(administrator=True)
    async def rol(self, interaction: discord.Integration, rol: discord.Role = None):
        data = load_json()['role_id']

        if rol:
            update_json('role_id', rol.id)

            await interaction.response.send_message(f'Rol cambiado a {rol}')
        else:
            if data:
                await interaction.response.send_message(f'Rol asignado: <@&{data}>')
            else:
                await interaction.response.send_message('¡Rol aún no seteado!')

async def setup(client: commands.Bot) -> None:
    await client.add_cog(TemasCog(client))
