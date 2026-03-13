import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    """Commandes générales du bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="aide", description="Affiche la liste de toutes les commandes disponibles")
    async def help(self, interaction: discord.Interaction):
        """Génère dynamiquement la liste des commandes par catégorie."""
        embed = discord.Embed(
            title="📖 Aide du Bot",
            description=f"Bonjour **{interaction.user.display_name}** ! Voici la liste des commandes disponibles sur le bot, classées par catégorie.",
            color=0x3498DB
        )

        # On parcourt tous les Cogs chargés dans le bot
        for cog_name, cog_object in self.bot.cogs.items():
            # On récupère les commandes slash (app_commands) du Cog
            commands_list = cog_object.get_app_commands()
            
            if commands_list:
                # On formate la liste des commandes pour cette catégorie
                # On affiche le nom de la commande et sa description
                category_commands = ""
                for cmd in commands_list:
                    category_commands += f"• `/{cmd.name}` : {cmd.description}\n"
                
                # On ajoute une section (field) à l'Embed pour cette catégorie
                # On utilise le nom du Cog comme titre de la section
                embed.add_field(
                    name=f"📂 {cog_name}",
                    value=category_commands,
                    inline=False
                )

        # Ajout d'un footer pour plus de style
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
