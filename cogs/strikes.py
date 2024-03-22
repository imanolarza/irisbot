# Favor mantener el orden con las importaciones de la siguiente manera en orden alfabético:
# 1er bloque; librerías de discord
import discord
from discord import app_commands
from discord.ext import commands

# 2do bloque; librerías nativas del python

# 3er bloque; otras librerías no nativas

# 4to bloque; modulos del proyecto
from json_operations import load_json, update_json
from config import error_color, info_color, success_color


class StrikesCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    strikes = app_commands.Group(name='strikes', description='Gestor de strikes')

    @strikes.command(name='lista')
    async def lista(self, interaction: discord.Interaction):
        data = load_json()

        usuarios = data['usuarios']

        embed = discord.Embed(
            color=info_color,
            title='Strikes',
            description='\n'.join('- <@%s> **%s/%s**' % (u['id'], u['strikes'], u['demote_strikes']) for u in usuarios)
        )

        await interaction.response.send_message(embed=embed)

    @strikes.command(name='agregar')
    @app_commands.describe(usuario='Usuario a agregar strike')
    async def agregar(self, interaction: discord.Interaction, usuario: discord.User):
        data = load_json()

        usuario_search = list(filter(lambda u: u['id'] == usuario.id, data['usuarios']))

        if len(usuario_search):
            usuario = usuario_search[0]

            new_usuario = usuario.copy()
            new_usuario.update({'strikes': usuario['strikes'] + 1})

            new_usuarios = data['usuarios']
            new_usuarios[data['usuarios'].index(usuario)] = new_usuario

            update_json('usuarios', new_usuarios)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(StrikesCog(client))
