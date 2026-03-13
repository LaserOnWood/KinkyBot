import discord
from discord import app_commands
from discord.ext import commands
import re

# --- Mots bannis pour l'auto-modération ---
# Ajoute ici tes mots interdits (en minuscules)
BANNED_WORDS: list[str] = [
    # "exemple_mot",
]

# Nombre de mentions simultanées avant de supprimer le message
MAX_MENTIONS = 5


class Moderation(commands.Cog):
    """Commandes de modération manuelle + auto-modération."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------------ #
    #  AUTO-MODÉRATION
    # ------------------------------------------------------------------ #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # Ignore les membres avec la permission de gérer les messages
        if isinstance(message.author, discord.Member) and message.author.guild_permissions.manage_messages:
            return

        content_lower = message.content.lower()

        # Anti-mots bannis
        for word in BANNED_WORDS:
            if word in content_lower:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention}, ce message enfreint les règles.", delete_after=5
                )
                return

        # Anti-mention spam
        if len(message.mentions) >= MAX_MENTIONS:
            await message.delete()
            await message.channel.send(
                f"⚠️ {message.author.mention}, trop de mentions d'un coup !", delete_after=5
            )
            return

        # Anti-lien (optionnel — décommenter pour activer)
        # URL_REGEX = re.compile(r"https?://\S+")
        # if URL_REGEX.search(message.content):
        #     await message.delete()
        #     await message.channel.send(f"⚠️ {message.author.mention}, les liens sont interdits ici.", delete_after=5)
        #     return

    # ------------------------------------------------------------------ #
    #  COMMANDES MANUELLES
    # ------------------------------------------------------------------ #

    @app_commands.command(name="kick", description="Expulser un membre")
    @app_commands.describe(membre="Membre à expulser", raison="Raison (optionnel)")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        await membre.kick(reason=raison)
        embed = discord.Embed(
            title="👢 Kick",
            description=f"**{membre}** a été expulsé.\n📝 Raison : {raison}",
            color=0xE67E22,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Bannir un membre")
    @app_commands.describe(membre="Membre à bannir", raison="Raison (optionnel)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        await membre.ban(reason=raison)
        embed = discord.Embed(
            title="🔨 Ban",
            description=f"**{membre}** a été banni.\n📝 Raison : {raison}",
            color=0xE74C3C,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban", description="Débannir un utilisateur")
    @app_commands.describe(user_id="L'ID Discord de l'utilisateur")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ **{user}** a été débanni.")
        except discord.NotFound:
            await interaction.response.send_message("❌ Utilisateur introuvable ou pas banni.", ephemeral=True)

    @app_commands.command(name="mute", description="Rendre muet un membre (timeout)")
    @app_commands.describe(membre="Membre à mute", minutes="Durée en minutes")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membre: discord.Member, minutes: int = 10):
        from datetime import timedelta, timezone, datetime
        until = discord.utils.utcnow() + timedelta(minutes=minutes)
        await membre.timeout(until, reason=f"Mute par {interaction.user}")
        await interaction.response.send_message(
            f"🔇 **{membre}** est muet pour **{minutes} minute(s)**."
        )

    @app_commands.command(name="clear", description="Supprimer des messages en masse")
    @app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, nombre: int):
        if nombre < 1 or nombre > 100:
            return await interaction.response.send_message("❌ Entre 1 et 100 messages.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=nombre)
        await interaction.followup.send(f"🗑️ **{len(deleted)}** messages supprimés.", ephemeral=True)

    # ------------------------------------------------------------------ #
    #  GESTION DES ERREURS DE PERMISSIONS
    # ------------------------------------------------------------------ #

    @kick.error
    @ban.error
    @unban.error
    @mute.error
    @clear.error
    async def permission_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas les permissions nécessaires.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Erreur : {error}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))