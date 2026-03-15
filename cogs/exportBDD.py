import discord
from discord.ext import commands
from discord import app_commands
import os
import shutil
import datetime

class ExportBDD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "/app/data/economy.db"  # <--- METS LE NOM DE TON FICHIER ICI

    @app_commands.command(name="export_bdd", description="Exporte et compresse la base de données (Propriétaire uniquement)")
    async def export_bdd(self, interaction: discord.Interaction):
        # 1. Vérification de sécurité : Seul le propriétaire du serveur peut l'utiliser
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Seul le propriétaire du serveur peut utiliser cette commande.", ephemeral=True)
            return

        if not os.path.exists(self.db_path):
            await interaction.response.send_message("❌ Fichier de base de données introuvable.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True) # On fait attendre Discord car le ZIP peut prendre du temps

        try:
            file_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            limit_mb = 24  # Marge de sécurité par rapport aux 25 Mo de Discord

            # 2. Logique de compression si trop gros ou par défaut pour la sécurité
            if file_size_mb > limit_mb:
                zip_name = f"backup_db_{datetime.date.today()}.zip"
                # Création du ZIP
                with shutil.ZipFile(zip_name, 'w') as zipf:
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