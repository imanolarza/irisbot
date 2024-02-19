# Favor mantener el orden con las importaciones de la siguiente manera en orden alfabético:
# 1er bloque; librerías de discord
import discord
from discord import app_commands
from discord.ext import commands

# 2do bloque; librerías nativas del python
from itertools import groupby
import os

# 3er bloque; otras librerías no nativas


# 4to bloque; modulos del proyecto
from json_operations import load_json, update_json

# Inicialización del bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(intents=intents, command_prefix='ir!')

#Colores
error_color = 0xda661b
success_color = 0x5ec2bf
info_color = 0xe07978

# Definición de categoría de tema semanal. Demomento solo funciona un comando para testear
# TODO: Volverlo a implementar
temas = app_commands.Group(name='temas', description='Tema diario')
puntos = app_commands.Group(name='puntos', description='Comandos para puntos del staff')

# Evento al iniciar bot
@bot.event
async def on_ready():
    try:
        # Añadir a la lista de comandos la categoría de tema semanal
        bot.tree.add_command(temas)
        bot.tree.add_command(puntos)

        synced = await bot.tree.sync()

        print(f'sincronizado(s) {len(synced)} comando(s)')
    except Exception as e:
        # Si hay un error, lo imprimirá
        print(e)

    print(f'Loggeado como {bot.user}')

# Funciones


# Definición de comandos
# Coamndos de bot
@bot.tree.command(name='sync')
async def sync(interaction: discord.Interaction):
    synced = await bot.tree.sync()

    await interaction.response.send_message(f'sincronizado(s) {len(synced)} comando(s)')
# Puntos
# Comando agregar puntos a usuario staff
@puntos.command(name='resumen')
async def resumen(interaction: discord.Interaction):
    data = load_json()

    usuario = list(filter(lambda u: u['id'] == interaction.user.id, data['usuarios']))

    embed = discord.Embed(color=info_color, title='Resumen de puntos')

    embed.add_field(name='Totales', value=f"𑁍 {usuario[0]['puntos']}")
    embed.add_field(name='Pendientes', value=f"𑁍 {usuario[0]['puntos_pendientes']}")
    embed.add_field(name='Semana', value=f"𑁍 {usuario[0]['puntos_semana']}/35")
    embed.add_field(name='Strikes', value=f"0/3")
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)

    await interaction.response.send_message(embed=embed)

# Comando agregar puntos a usuario staff
@puntos.command(name='agregar')
@app_commands.describe(miembro='Miembro a agregar puntaje')
@app_commands.describe(cantidad='Cantidad de puntos')
async def agregar(interaction: discord.Interaction, miembro: discord.Member, cantidad:int):
    # Crear embed
    data = load_json()

    search_user = list(filter(lambda u: u['id'] == miembro.id, data['usuarios']))

    if len(search_user):
        user = search_user[0]
        new_user = user.copy()
        new_users = data['usuarios'].copy()

        new_user.update({'puntos': user['puntos'] + cantidad})
        new_users[new_users.index(user)] = new_user
        update_json('usuarios', new_users)

        embed = discord.Embed(title="Puntaje modificado", color=success_color)

        embed.set_author(name=miembro.name, icon_url=miembro.avatar.url)
        embed.add_field(name='Punto dado por', value=interaction.user.name)
        embed.add_field(name='Puntos', value=f"**{user['puntos']}** → **{new_user['puntos']}**")

        await interaction.response.send_message(embed=embed)

# Comando reclamar puntaje
# Pone el reclamo del ejecutador del comando en movimientos pendientes(json)
@puntos.command(name='reclamar')
# Lista desplegable de acciones
# TODO Comando para agregar acciones
@app_commands.describe(accion='acción por reclamar puntaje')
@app_commands.choices(accion=[
    # Esto recorre cada acción cargada en el json y setea con choices al comando
    # Cada opción seleccionada retorna ID de acción.
    app_commands.Choice(name=acc['name'], value=str(acc['id'])) for acc in load_json()['acciones']
])
@app_commands.describe(evidencia='Link del mensaje evidencia')
async def reclamar(interaction: discord.Interaction, accion: str, evidencia: str):
    # Json a consumir
    data = load_json()

    # Cargar json de usuarios
    usuarios = data['usuarios']

    # Cargar en esta variable los anteriores movimientos
    old_movimientos_pendientes = data['movimientos_pendientes']

    # Buscar acción en json a partir del ID proporcionado en campo "acción"
    accion_json = list(filter(lambda a: a['id'] == int(accion), data['acciones']))[0]

    # Buscar en el json el usuario que ejecutó el comando
    usuario = list(filter(lambda u: u['id'] == interaction.user.id, usuarios))

    # Si el usuario se encuentra en el json, sumar el reclamo a movimientos pendientes
    if not len(usuario):
        old_usuarios = data['usuarios'].copy()
        new_usuarios = old_usuarios.append({'id': interaction.user.id, 'puntos': 0, 'puntos_pendientes': 0})
        usuarios = new_usuarios

        update_json('usuarios', new_usuarios)

        usuario = list(filter(lambda u: u['id'] == interaction.user.id, usuarios))

    # Carga de nueva información
    new_movimientos_pendientes = old_movimientos_pendientes.copy()

    # Conseguir actual id a base de cantidad de movimientos
    new_id = len(old_movimientos_pendientes) + 1

    # Actualizar columna del json con la nueva información
    new_movimientos_pendientes.append({
        'id': new_id,
        'accion_id': int(accion),
        'evidencia': evidencia,
        'user_id': usuario[0]['id']
    })

    update_json('movimientos_pendientes', new_movimientos_pendientes)

    # actualizar pendientes del usuario
    new_usuarios = usuarios.copy()

    new_usuarios[new_usuarios.index(usuario[0])].update({
        'puntos_pendientes': usuario[0]['puntos_pendientes'] + accion_json['value']
    })

    update_json('usuarios', new_usuarios)

    # Embed
    embed = discord.Embed(title=':Haz reclamado **%s**' % accion_json['name'], color=success_color)
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
    embed.add_field(name='Puntos:', value=accion_json['value'])
    embed.add_field(name='Link del mensaje:', value=evidencia)

    await interaction.response.send_message(embed=embed)

# Comando puntos pendientes
# Enviará los movimientos pendientes a aprobar por el autorizado correspondiente
@puntos.command(name='pendientes')
async def pendientes(interaction: discord.Interaction, usuario: discord.Member = None):
    # Cargar columna de movimientos pendientes del json
    data = load_json()
    movimientos_pendientes = data['movimientos_pendientes']
    acciones = data['acciones']
    if usuario:
        await interaction.response.send_message(usuario)

    # Si hay movimientos, los enviará al mensaje
    # Embed
    if len(movimientos_pendientes):
        movimientos_str = ''
        for movimiento in movimientos_pendientes:
            accion = list(filter(lambda a: a['id'] == movimiento['accion_id'], acciones))[0]

            movimientos_str += f"{movimiento['id']}. <@{movimiento['user_id']}>: [{accion['name']}]({movimiento['evidencia']}) - {accion['value']}P\n"

        embed = discord.Embed(title="Movimientos pendientes", color=info_color, description=movimientos_str)

        await interaction.response.send_message(embed=embed)

    # Si NO hay movimientos, enviará un mensaje indicando que no hay movimientos pendientes
    # TODO: Formatear el mensaje en un embed legible
    else:
        await interaction.response.send_message('Sin movimientos pendientes')

@puntos.command(name='sincronizar')
async def sincronizar(interaction: discord.Interaction):
    data = load_json()

    movimientos_pendientes = data['movimientos_pendientes']
    usuarios = data['usuarios']

    for usuario, movimientos_pendientes in groupby(
            sorted(movimientos_pendientes, key=lambda mp: mp['user_id']), 
            key=lambda mp: mp['user_id']
        ):
        usuario_search = list(filter(lambda u: u['id'] == usuario, usuarios))

        if len(usuario_search):
            usuario = usuario_search[0]

            new_usuarios = usuarios.copy()

            new_usuarios[new_usuarios.index(usuario)].update({
                'puntos': usuario['puntos'] + usuario['puntos_pendientes'], 'puntos_pendientes': 0
            })

            update_json('usuarios', new_usuarios)
            update_json('movimientos_pendientes', [])

    embed = discord.Embed(color=success_color, title='Sincronizado correctamente')

    await interaction.response.send_message(embed=embed)

# Temas
# TODO: Integrar de vuelta los comandos (adicionando información municiosamente a cada fragmento de código) hallados en ./main.py.old

# INICIAR BOT:
my_secret = os.environ['TOKEN']

# Inicia el servidor. Solamente disponible para REPLIT
# keep_alive()

bot.run(my_secret)