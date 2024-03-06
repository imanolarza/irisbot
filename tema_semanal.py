import discord
from datetime import datetime, timezone, timedelta
from discord import app_commands

from json_operations import load_json, update_json

temas = app_commands.Group(name='temas', description='Tema diario')

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
            print(res)

            if now.time() > res.time():
                res = res + timedelta(days=7)

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
@app_commands.describe(channel_id='Canal a responder, ejemplo, #general')
async def agregar(interaction: discord.Interaction, tema: str, channel_id: discord.TextChannel):
    data = load_json()['temas']

    new_id = len(data) + 1
    new_data = data.copy()

    new_data.append({
        'id': new_id,
        'name': tema,
        'channel_id': channel_id.id
    })

    update_json('temas', new_data)

    # embed = gen_embed(name=tema, quote='', quote_author='', quote_source='', image_url=imagen, color=int(color, 16))
    embed = discord.Embed(
        title='⚡ Tema de la semana',
        description=f'## "{tema}"\n' + '➜ Puedes responder en <#%s>' % channel_id.id
    )
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


@temas.command(name='rol', description='¿Qué rol debería mencionar al ejecutar tema diario?')
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

