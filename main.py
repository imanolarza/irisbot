# Favor mantener el orden con las importaciones de la siguiente manera en orden alfabético:
# 1er bloque; librerías de discord
import discord
from discord import app_commands
from discord.ext import commands

# 2do bloque; librerías nativas del python
import os

# 3er bloque; otras librerías no nativas


# 4to bloque; modulos del proyecto
from json_operations import load_json, update_json

# Inicialización del bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(intents=intents, command_prefix='!')

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

# Definición de comandos
# Puntos
@puntos.command(name='agregar')
@app_commands.describe(miembro='Miembro a ceder puntaje')
@app_commands.describe(cantidad='Cantidad de puntos')
async def agregar(interaction: discord.Interaction, miembro: discord.Member, cantidad:int):
    embed = discord.Embed(
        title=f"Staff {miembro} ha recibido",
        color=0x2F3136
    )
    embed.set_author(
        name="Punto staff",
        icon_url=miembro.avatar.url
    )
    embed.add_field(name='Punto dado por:', value=interaction.user.name)
    embed.add_field(name='Puntos:', value=cantidad)

    embed.set_footer(
        text=f"Requested by {interaction.user.name}",
        icon_url=interaction.user.avatar.url
    )

    await interaction.response.send_message(embed=embed)

# Temas
@temas.command(name='carlos')
async def carlos(interaction: discord.Interaction):
    # Retorna al usuario el mensaje de abajo
    await interaction.response.send_message('it\'s fucking carlos')

# TODO: Integrar de vuelta los comandos (adicionando información municiosamente a cada fragmento de código) hallados en ./main.py.old

# INICIAR BOT:
my_secret = os.environ['TOKEN']

# Inicia el servidor. Solamente disponible para REPLIT
# keep_alive()

bot.run(my_secret)