import discord
from discord import app_commands
from discord.ext import commands
from utils.database import set_config, get_config

class ConfigPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panneau_config", description="Ouvrir le panneau de configuration du bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def panneau_config(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚙️ Panneau de Configuration",
            description="Choisissez une catégorie à configurer ci-dessous.",
            color=discord.Color.blue()
        )
        
        # Vue avec un menu déroulant pour choisir quoi configurer
        view = ConfigMainView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ConfigMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Que souhaitez-vous configurer ?",
        options=[
            discord.SelectOption(label="Salons Photo", value="photos", emoji="📸", description="Gérer les fils automatiques"),
            discord.SelectOption(label="Réactions", value="reactions", emoji="💬", description="Ajouter/Supprimer des mots-clés"),
            discord.SelectOption(label="Accueil", value="accueil", emoji="👋", description="Changer le salon de bienvenue")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "photos":
            # Menu de sélection de salons
            channel_select = discord.ui.ChannelSelect(
                placeholder="Sélectionnez les salons photo...",
                channel_types=[discord.ChannelType.text],
                min_values=1,
                max_values=3
            )

            async def channel_callback(inter: discord.Interaction):
                ids = ",".join([str(c.id) for c in channel_select.values])
                set_config("salons_photo", ids)
                await inter.response.send_message(f"✅ Salons photo mis à jour !", ephemeral=True)

            channel_select.callback = channel_callback
            new_view = discord.ui.View()
            new_view.add_item(channel_select)
            await interaction.response.edit_message(content="Sélectionnez les salons :", view=new_view, embed=None)

async def setup(bot):
    await bot.add_cog(ConfigPanel(bot))