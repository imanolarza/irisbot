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

bot = commands.Bot(intents=intents)

# Definición de categoría de tema semanal. Demomento solo funciona un comando para testear
# TODO: Volverlo a implementar
temas = app_commands.Group(name='temas', description='Tema diario')

# Evento al iniciar bot
@bot.event
async def on_ready():
    try:
        # Añadir a la lista de comandos la categoría de tema semanal
        bot.tree.add_command(temas)

        synced = await bot.tree.sync()

        print(f'sincronizado(s) {len(synced)} comando(s)')
    except Exception as e:
        # Si hay un error, lo imprimirá
        print(e)

    print(f'Loggeado como {bot.user}')

# Definición de comandos
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