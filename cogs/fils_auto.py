import discord
from discord.ext import commands

class GestionFils(commands.Cog):
    """Crée automatiquement des fils sous les images et nettoie le salon."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # IDs des salons où cette fonctionnalité est active
        self.SALONS_IMAGES = [123456789012345678] 

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 1. On ignore les messages des bots
        if message.author.bot:
            return

        # 2. On vérifie si le message est dans l'un des salons cibles
        if message.channel.id not in self.SALONS_IMAGES:
            return

        # --- EXCEPTION STAFF ---
        # Si l'auteur a la permission de gérer les messages (Modo/Admin), on ne supprime rien
        membre_staff = message.author.guild_permissions.manage_messages
        
        # 3. Logique pour les images (valable pour tout le monde)
        if message.attachments:
            nom_fil = f"Discussion de {message.author.display_name}"
            try:
                await message.create_thread(name=nom_fil, auto_archive_duration=1440)
            except Exception as e:
                print(f"❌ Erreur création fil : {e}")
            return # On s'arrête ici si c'est une image

        # 4. Logique pour le texte seul
        if not membre_staff:
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention}, ce salon est réservé aux images. "
                    "Pour discuter, utilise le **fil de discussion** sous une photo !",
                    delete_after=10
                )
            except Exception as e:
                print(f"❌ Erreur lors de la suppression : {e}")
        else:
            # Optionnel : On peut laisser un log console ou ne rien faire
            # Ici, le staff peut poster du texte sans que rien ne se passe.
            pass

async def setup(bot):
    await bot.add_cog(GestionFils(bot))
