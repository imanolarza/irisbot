import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

from json_operations import load_json

logger = logging.getLogger('discord')

class SinVerificarView(discord.ui.LayoutView):
    def __init__(self, content, index=1):
        super().__init__()

        self.container = self.Container(self, content, index)
        self.add_item(self.container)

    class Container(discord.ui.Container):
        def __init__(self, parent_view, content, index=1):
            self.parent_view = parent_view

            # Guardamos referencia al texto
            self.header_text = discord.ui.TextDisplay(
                "# Miembros sin presentación"
            )

            description = "%(content)s"

            top_index, last_index = divmod(len(content), 10)

            if (index - 1) < top_index:
                members = "\n".join(f"- <@{c}>" for c in content[(index - 1) * 10:(top_index * 10) + 1])
            else:
                if top_index:
                    members = "\n".join(f"- <@{c}>" for c in content[1 + (index - 1) * 10:])
                else:
                    members = "\n".join(f"- <@{c}>" for c in content[:last_index + 1])

            self.description = discord.ui.TextDisplay(content=description % {"content": members})

            self.separator = discord.ui.Separator()

            self.action_row = self.ActionRow(self, content=content, index=index)
            self.page = discord.ui.TextDisplay("-# página **1** de **10**")
            self.quantity = discord.ui.TextDisplay("-# **15** usuarios")
            self.last_update = discord.ui.TextDisplay("-# Última actualización <t:1779556419:S>")

            super().__init__(
                self.header_text,
                self.description,
                self.quantity,
                self.last_update,
                self.separator,
                self.page,
                self.action_row
            )

        class ActionRow(discord.ui.ActionRow):
            def __init__(self, parent_view, content, index=1):
                self.index = index
                self.parent_view = parent_view
                self.content = content

                super().__init__()

                self.previous_page.disabled = not bool(self.index - 1)

                top_index, last_index = divmod(len(content), 10)
                self.next_page.disabled = not (top_index - (index - 1))

            @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="⬅️")
            async def previous_page(self, interaction: discord.Interaction, _1: discord.ui.button):
                await interaction.response.edit_message(view=SinVerificarView(content=self.content, index=self.index - 1))

            @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="➡️")
            async def next_page(self, interaction: discord.Interaction, _1: discord.ui.button):
                await interaction.response.edit_message(view=SinVerificarView(content=self.content, index=self.index + 1))

            @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="🔄")
            async def update(self, _: discord.Interaction, _1: discord.ui.button):
                logger.info("Update")

class CheckMiembros(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    check_miembros = app_commands.Group(name='check_miembros', description='Check de miembros')

    @check_miembros.command(name="sin_verificar")
    async def sin_verificar(self, interaction: discord.Interaction):
        logger.info("Sin verificar")
        unverified_members = load_json()["unverified_members"]
        view = SinVerificarView(content=unverified_members)
        await interaction.response.send_message(view=view)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(CheckMiembros(client))
