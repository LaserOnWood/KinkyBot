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
        id_salon_str = get_config("salon_accueil")
        if not id_salon_str:
            return
            
        try:
            id_salon = int(id_salon_str)
        except ValueError:
            print(f"⚠️ Erreur : ID salon_accueil invalide ({id_salon_str})")
            return

        channel = self.bot.get_channel(id_salon)
        
        if channel:
            # Récupération des autres salons configurés
            id_presentation = get_config("salon_presentation")
            id_reglement = get_config("salon_reglement")
            
            # Préparation des mentions (fallback si non configuré)
            mention_pres = f"<#{id_presentation}>" if id_presentation and id_presentation.isdigit() else "*[Non configuré]*"
            mention_regle = f"<#{id_reglement}>" if id_reglement and id_reglement.isdigit() else "*[Non configuré]*"

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
                value=f"Rends-toi dans le salon {mention_pres} et présente-toi en suivant le modèle épinglé.",
                inline=False
            )
            embed.add_field(
                name="2️⃣ Règlement",
                value=f"Lis et valide le règlement dans le salon {mention_regle}.",
                inline=False
            )
            embed.add_field(
                name="3️⃣ Validation",
                value="Patiente un court instant, un membre du staff viendra valider ton profil pour t'ouvrir les accès.",
                inline=False
            )
            embed.add_field(
                name="4️⃣ Promotion",
                value="Fais nous savoir si nous nous sommes déjà rencontré afin d'obtenir le rôle adéquat",
                inline=False
            )

            # Image ou icône facultative
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID du membre : {member.id}")

            # Envoi du message
            try:
                await channel.send(content=f"Bienvenue {member.mention} !", embed=embed)
            except discord.Forbidden:
                print(f"⚠️ Erreur : Permissions insuffisantes pour envoyer le message de bienvenue dans {channel.name}")

async def setup(bot):
    await bot.add_cog(Accueil(bot))
