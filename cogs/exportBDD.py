import discord
from discord.ext import commands
from discord import app_commands
import os
import zipfile
import datetime

class ExportBDD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # On utilise le chemin relatif pour plus de flexibilité
        self.db_path = "data/economy.db"

    @app_commands.command(name="export_bdd", description="Exporte et compresse la base de données (Propriétaire du bot uniquement)")
    async def export_bdd(self, interaction: discord.Interaction):
        # 1. Vérification de sécurité : Seul le propriétaire du BOT peut l'utiliser (données sensibles)
        is_owner = await self.bot.is_owner(interaction.user)
        if not is_owner:
            embed = discord.Embed(
                title="❌ Accès refusé",
                description="Seul le propriétaire du bot peut exporter la base de données.",
                color=0xE74C3C
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not os.path.exists(self.db_path):
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Fichier de base de données introuvable à l'emplacement : `{self.db_path}`",
                color=0xE74C3C
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            file_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            limit_mb = 24  # Marge de sécurité par rapport aux 25 Mo de Discord

            # 2. Logique de compression si trop gros ou par défaut pour la sécurité
            if file_size_mb > limit_mb:
                zip_name = f"backup_db_{datetime.date.today()}.zip"
                # Création du ZIP avec zipfile (et non shutil)
                with zipfile.ZipFile(zip_name, 'w') as zipf:
                    zipf.write(self.db_path, arcname=os.path.basename(self.db_path))
                
                file_to_send = discord.File(zip_name)
                content = f"📦 La base de données était trop lourde ({file_size_mb:.2f} MB), voici une version compressée."
                
                await interaction.followup.send(content=content, file=file_to_send)
                
                # Supprimer le ZIP temporaire après envoi
                os.remove(zip_name)
            else:
                # Envoi direct du fichier .sqlite
                file_to_send = discord.File(self.db_path)
                await interaction.followup.send(content="📄 Voici l'export de la base de données :", file=file_to_send)

        except Exception as e:
            await interaction.followup.send(f"⚠️ Une erreur est survenue : {e}")

async def setup(bot):
    await bot.add_cog(ExportBDD(bot))
