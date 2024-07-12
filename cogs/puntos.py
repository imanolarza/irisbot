# Favor mantener el orden con las importaciones de la siguiente manera en orden alfabético:
# 1er bloque; librerías de discord
import discord
from discord import app_commands
from discord.ext import commands

# 2do bloque; librerías nativas del python
import logging

# 3er bloque; otras librerías no nativas
from itertools import groupby

# 4to bloque; modulos del proyecto
from config import success_color, info_color, error_color, req_semana
from json_operations import load_json, update_json

logger  = logging.getLogger('discord')

class PuntosCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    puntos = app_commands.Group(name='puntos', description='Sistema de puntajes')

    # Funciones
    async def agregar_puntaje(self, data: dict, miembro_id: int, cantidad: int) -> dict | None:
        search_user = list(filter(lambda u: u['id'] == miembro_id, data['usuarios']))

        if len(search_user):
            user = search_user[0]
            new_user = user.copy()
            new_users = data['usuarios'].copy()

            new_user.update({'puntos_semana': user['puntos_semana'] + cantidad})
            new_users[new_users.index(user)] = new_user

            update_json('usuarios', new_users)

            return new_user
        else:
            return None

    # Comandos Puntos
    # Comando resumen de puntos de usuario
    @puntos.command(name='resumen')
    @app_commands.describe(usuario='Filtrar por usuario')
    async def resumen(self, interaction: discord.Interaction, usuario: discord.Member=None):
        data = load_json()

        usuarios_filter = tuple(
            filter(lambda u: u['id'] == usuario.id if usuario else interaction.user.id, data['usuarios'])
        )

        if len(usuarios_filter):
            select_usuario = usuarios_filter[0]

            embed = discord.Embed(color=info_color, title='Resumen de puntos')

            embed.add_field(name='Totales', value=f"𑁍 {select_usuario['puntos']}")
            embed.add_field(name='Pendientes', value=f"𑁍 {select_usuario['puntos_pendientes']}")
            embed.add_field(name='Semana', value=f"𑁍 {select_usuario['puntos_semana']}/{req_semana}")
            embed.set_author(
                name=usuario.name if usuario else interaction.user.name,
                icon_url=usuario.avatar.url if usuario else interaction.user.avatar.url
            )

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                'usuario "%s" no encontrado en la base de datos' % usuario.name if usuario else interaction.user.name
            )

    # Comando agregar puntos a usuario staff
    @puntos.command(name='agregar')
    @app_commands.describe(miembro='Miembro a agregar puntaje')
    @app_commands.describe(cantidad='Cantidad de puntos')
    @app_commands.checks.has_permissions(administrator=True)
    async def agregar(self, interaction: discord.Interaction, miembro: discord.Member, cantidad:int):
        data = load_json()

        agregar_puntaje = await self.agregar_puntaje(data, miembro.id, cantidad)

        # Crear embed
        if agregar_puntaje:
            embed = discord.Embed(title="Puntaje modificado", color=success_color)

            embed.set_author(name=miembro.name, icon_url=miembro.avatar.url)
            embed.add_field(name='Punto dado por', value=interaction.user.name)

            old_usuario = list(filter(lambda u: u['id'] == miembro.id, data['usuarios']))[0]

            embed.add_field(name='Puntos', value=f"**{old_usuario['puntos_semana']}** → **{agregar_puntaje['puntos_semana']}**")

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
    async def reclamar(self, interaction: discord.Interaction, accion: str, evidencia: str):
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
    async def pendientes(self, interaction: discord.Interaction, usuario: discord.Member = None):
        # Cargar columna de movimientos pendientes del json
        data = load_json()
        movimientos_pendientes = data['movimientos_pendientes']
        acciones = data['acciones']

        if usuario:
            movimientos_pendientes = list(filter(lambda a: a['user_id'] == usuario.id, movimientos_pendientes))

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
    @app_commands.checks.has_permissions(administrator=True)
    async def sincronizar(self, interaction: discord.Interaction):
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
                    'puntos_semana': usuario['puntos_semana'] + usuario['puntos_pendientes'], 'puntos_pendientes': 0
                })

                update_json('usuarios', new_usuarios)
                update_json('movimientos_pendientes', [])

        embed = discord.Embed(color=success_color, title='Sincronizado correctamente')

        await interaction.response.send_message(embed=embed)

    @puntos.command(name='finalizar_semana')
    @app_commands.describe(seguro='¿Está seguro de que desea finalizar la semana?')
    @app_commands.choices(seguro=[
        app_commands.Choice(name='No', value=0),
        app_commands.Choice(name='Sí', value=1)
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def finalizar_semana(self, interaction: discord.Interaction, seguro: int):
        if seguro:
            data = load_json().copy()

            usuarios = data['usuarios']

            for usuario in usuarios:
                if usuario['puntos_semana'] < req_semana:
                    usuario.update({'puntos_semana': 0, 'strikes': usuario['strikes'] + 1})
                elif usuario['puntos_semana'] >= req_semana:
                    usuario.update({
                        'puntos': usuario['puntos'] + req_semana,
                        'puntos_semana': usuario['puntos_semana'] - req_semana
                    })

            update_json('usuarios', usuarios)

            embed = discord.Embed(
                color=success_color,
                title='Semana finalizada!',
                description='Usa el comando </puntos resumen:1218012813134659634> para control de tus puntos!'
            )

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message('Operación cancelada', ephemeral=True)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(PuntosCog(client))
