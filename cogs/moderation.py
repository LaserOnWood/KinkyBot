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
                embed = discord.Embed(
                    title="⚠️ Avertissement",
                    description=f"**{message.author.display_name}**, ce message enfreint les règles.",
                    color=0xE74C3C
                )
                await message.channel.send(embed=embed, delete_after=5)
                return

        # Anti-mention spam
        if len(message.mentions) >= MAX_MENTIONS:
            await message.delete()
            embed = discord.Embed(
                title="⚠️ Avertissement",
                description=f"**{message.author.display_name}**, trop de mentions d'un coup !",
                color=0xE74C3C
            )
            await message.channel.send(embed=embed, delete_after=5)
            return

    # ------------------------------------------------------------------ #
    #  COMMANDES MANUELLES
    # ------------------------------------------------------------------ #

    @app_commands.command(name="expulser", description="Expulser un membre")
    @app_commands.describe(membre="Membre à expulser", raison="Raison (optionnel)")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        await membre.kick(reason=raison)
        embed = discord.Embed(
            title="👢 Expulsion",
            description=f"**{membre.display_name}** a été expulsé.\n📝 Raison : {raison}",
            color=0xE67E22,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bannir", description="Bannir un membre")
    @app_commands.describe(membre="Membre à bannir", raison="Raison (optionnel)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        await membre.ban(reason=raison)
        embed = discord.Embed(
            title="🔨 Bannissement",
            description=f"**{membre.display_name}** a été banni.\n📝 Raison : {raison}",
            color=0xE74C3C,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="debannir", description="Débannir un utilisateur")
    @app_commands.describe(user_id="L'ID Discord de l'utilisateur")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            embed = discord.Embed(
                title="✅ Débannissement",
                description=f"**{user.display_name}** a été débanni.",
                color=0x2ECC71
            )
            await interaction.response.send_message(embed=embed)
        except discord.NotFound:
            embed = discord.Embed(title="❌ Erreur", description="Utilisateur introuvable ou pas banni.", color=0xE74C3C)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(title="❌ Erreur", description="ID invalide.", color=0xE74C3C)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="muet", description="Rendre muet un membre (timeout)")
    @app_commands.describe(membre="Membre à mute", minutes="Durée en minutes")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membre: discord.Member, minutes: int = 10):
        from datetime import timedelta
        until = discord.utils.utcnow() + timedelta(minutes=minutes)
        await membre.timeout(until, reason=f"Mute par {interaction.user.display_name}")
        embed = discord.Embed(
            title="🔇 Mute",
            description=f"**{membre.display_name}** est muet pour **{minutes} minute(s)**.",
            color=0x95A5A6
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nettoyer", description="Supprimer des messages en masse")
    @app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, nombre: int):
        if nombre < 1 or nombre > 100:
            embed = discord.Embed(title="❌ Erreur", description="Entre 1 et 100 messages.", color=0xE74C3C)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=nombre)
        embed = discord.Embed(
            title="🗑️ Nettoyage",
            description=f"**{len(deleted)}** messages supprimés.",
            color=0x3498DB
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="deplacer", description="Déplacer des messages vers un autre salon")
    @app_commands.describe(salon="Le salon de destination", nombre="Nombre de messages à déplacer (max 100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def move_messages(self, interaction: discord.Interaction, salon: discord.TextChannel, nombre: int):
        if nombre < 1 or nombre > 100:
            embed = discord.Embed(title="❌ Erreur", description="Entre 1 et 100 messages.", color=0xE74C3C)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        
        messages = [msg async for msg in interaction.channel.history(limit=nombre)]
        if not messages:
            embed = discord.Embed(title="❌ Erreur", description="Aucun message trouvé à déplacer.", color=0xE74C3C)
            return await interaction.followup.send(embed=embed, ephemeral=True)
            
        messages.reverse()
        
        webhooks = await salon.webhooks()
        webhook = discord.utils.get(webhooks, name="KinkyBot Move")
        if not webhook:
            try:
                webhook = await salon.create_webhook(name="KinkyBot Move")
            except discord.Forbidden:
                embed = discord.Embed(title="❌ Erreur", description="Permissions insuffisantes pour créer un webhook dans le salon cible.", color=0xE74C3C)
                return await interaction.followup.send(embed=embed, ephemeral=True)
                
        for msg in messages:
            files = []
            for att in msg.attachments:
                try:
                    files.append(await att.to_file())
                except Exception:
                    pass
            
            content = msg.content
            if not content and not files and not msg.embeds:
                content = "*[Contenu non supporté]*"
                
            try:
                await webhook.send(
                    content=content,
                    username=msg.author.display_name,
                    avatar_url=msg.author.display_avatar.url if msg.author.display_avatar else None,
                    files=files,
                    embeds=msg.embeds
                )
            except discord.HTTPException:
                pass
                
        try:
            await interaction.channel.delete_messages(messages)
        except discord.HTTPException:
            for msg in messages:
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass
                    
        embed_success = discord.Embed(
            title="➡️ Déplacement",
            description=f"**{len(messages)}** messages déplacés vers {salon.mention}.",
            color=0x2ECC71
        )
        await interaction.followup.send(embed_success, ephemeral=True)

    # ------------------------------------------------------------------ #
    #  GESTION DES ERREURS DE PERMISSIONS
    # ------------------------------------------------------------------ #

    @kick.error
    @ban.error
    @unban.error
    @mute.error
    @clear.error
    @move_messages.error
    async def permission_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(title="❌ Erreur", description="Tu n'as pas les permissions nécessaires.", color=0xE74C3C)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="❌ Erreur", description=f"Erreur : {error}", color=0xE74C3C)
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
