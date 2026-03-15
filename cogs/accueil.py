import discord
from discord.ext import commands
from utils.database import get_config

class Accueil(commands.Cog):
    """Gestion de l'accueil des nouveaux membres."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """S'active lorsqu'un membre rejoint le serveur."""
        
        # On récupère le salon de bienvenue via la config
        id_salon = get_config("salon_accueil")
        if not id_salon:
            return
            
        channel = self.bot.get_channel(int(id_salon))
        
        if channel:
            # Récupération des autres salons configurés
            id_presentation = get_config("salon_presentation", "ID_NON_CONFIGURE")
            id_reglement = get_config("salon_reglement", "ID_NON_CONFIGURE")
            
            # Création de l'Embed de bienvenue
            embed = discord.Embed(
                title=f"👋 Bienvenue sur le serveur, {member.display_name} !",
                description=f"Nous sommes ravis de te compter parmi nous, {member.mention} ! "
                            "Pour accéder à l'intégralité du serveur, merci de suivre les étapes ci-dessous.",
                color=0x2ecc71 # Vert émeraude
            )

            # Ajout des étapes
            embed.add_field(
                name="1️⃣ Présentation",
                value=f"Rends-toi dans le salon <#{id_presentation}> et présente-toi en suivant le modèle épinglé.",
                inline=False
            )
            embed.add_field(
                name="2️⃣ Règlement",
                value=f"Lis et valide le règlement dans le salon <#{id_reglement}>.",
                inline=False
            )
            embed.add_field(
                name="3️⃣ Validation",
                value="Patiente un court instant, un membre du staff viendra valider ton profil pour t'ouvrir les accès.",
                inline=False
            )

            # Image ou icône facultative
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID du membre : {member.id}")

            # Envoi du message
            await channel.send(content=f"Bienvenue {member.mention} !", embed=embed)

async def setup(bot):
    await bot.add_cog(Accueil(bot))
