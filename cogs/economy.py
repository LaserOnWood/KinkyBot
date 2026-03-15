import discord
from discord import app_commands
from discord.ext import commands
from datetime import date
import random

from utils.database import get_data, update_db, init_db, get_leaderboard


class Economy(commands.Cog):
    """Commandes d'économie : solde, quotidien, travail, dépôt, retrait, classement."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db()

    # /solde
    @app_commands.command(name="solde", description="Consulter ton solde")
    async def balance(self, interaction: discord.Interaction):
        await interaction.response.defer() # Sécurité anti-timeout
        
        wallet, bank, _ = get_data(interaction.user.id)
        embed = discord.Embed(
            title=f"🏦 Compte de {interaction.user.display_name}",
            color=0x3498DB,
        )
        embed.add_field(name="Portefeuille", value=f"**{wallet}** 💶", inline=True)
        embed.add_field(name="Banque",        value=f"**{bank}** 🏦",  inline=True)
        await interaction.followup.send(embed=embed)

    # /quotidien
    @app_commands.command(name="quotidien", description="Récupérer ton bonus quotidien")
    async def daily(self, interaction: discord.Interaction):
        # On defer en ephemeral car le message d'erreur "reviens demain" doit être privé
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        _, _, last_daily = get_data(user_id)
        today = str(date.today())

        if last_daily == today:
            embed = discord.Embed(
                title="⏳ Patience",
                description=f"**{interaction.user.display_name}**, reviens demain !",
                color=0xE67E22
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        reward = 500
        update_db(user_id, wallet_diff=reward, new_daily=today)
        embed = discord.Embed(
            title="🎁 Bonus Quotidien",
            description=f"**{interaction.user.display_name}**, tu as reçu **{reward} 💶** !",
            color=0x2ECC71
        )
        # On envoie la réussite en public (ephemeral=False par défaut)
        await interaction.followup.send(embed=embed, ephemeral=False)

    # /travail
    @app_commands.command(name="travail", description="Travailler pour gagner de l'argent")
    async def work(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        gain = random.randint(70, 200)
        update_db(interaction.user.id, wallet_diff=gain)
        jobs = ["Mineur de Bitcoin", "Livreur Uber", "Modérateur Discord", "Mercenaire", "Streamer Twitch"]
        embed = discord.Embed(
            title="💼 Travail terminé",
            description=f"**{interaction.user.display_name}**, tu as travaillé comme **{random.choice(jobs)}** et gagné **{gain} 💶** !",
            color=0x3498DB
        )
        await interaction.followup.send(embed=embed)

    # /depot
    @app_commands.command(name="depot", description="Déposer de l'argent en banque")
    @app_commands.describe(montant="Montant à déposer (ou 'all')")
    async def deposit(self, interaction: discord.Interaction, montant: str):
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        wallet, _, _ = get_data(user_id)

        try:
            amt = wallet if montant.lower() == "all" else int(montant)
        except ValueError:
            embed = discord.Embed(title="❌ Erreur", description="Montant invalide.", color=0xE74C3C)
            return await interaction.followup.send(embed=embed, ephemeral=True)

        if amt <= 0 or amt > wallet:
            embed = discord.Embed(title="❌ Erreur", description="Montant invalide ou insuffisant.", color=0xE74C3C)
            return await interaction.followup.send(embed=embed, ephemeral=True)

        update_db(user_id, wallet_diff=-amt, bank_diff=amt)
        embed = discord.Embed(
            title="✅ Dépôt réussi",
            description=f"**{interaction.user.display_name}**, tu as déposé **{amt} 💶** en banque.",
            color=0x2ECC71
        )
        await interaction.followup.send(embed=embed, ephemeral=False)

    # /retrait
    @app_commands.command(name="retrait", description="Retirer de l'argent de la banque")
    @app_commands.describe(montant="Montant à retirer (ou 'all')")
    async def withdraw(self, interaction: discord.Interaction, montant: str):
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        _, bank, _ = get_data(user_id)

        try:
            amt = bank if montant.lower() == "all" else int(montant)
        except ValueError:
            embed = discord.Embed(title="❌ Erreur", description="Montant invalide.", color=0xE74C3C)
            return await interaction.followup.send(embed=embed, ephemeral=True)

        if amt <= 0 or amt > bank:
            embed = discord.Embed(title="❌ Erreur", description="Montant invalide ou insuffisant en banque.", color=0xE74C3C)
            return await interaction.followup.send(embed=embed, ephemeral=True)

        update_db(user_id, wallet_diff=amt, bank_diff=-amt)
        embed = discord.Embed(
            title="✅ Retrait réussi",
            description=f"**{interaction.user.display_name}**, tu as retiré **{amt} 💶** de ta banque.",
            color=0x2ECC71
        )
        await interaction.followup.send(embed=embed, ephemeral=False)

    # /classement
    @app_commands.command(name="classement", description="Classement des joueurs les plus riches")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        rows = get_leaderboard(10)
        if not rows:
            embed = discord.Embed(title="🏆 Classement", description="Aucun joueur pour l'instant.", color=0xF1C40F)
            return await interaction.followup.send(embed=embed)

        embed = discord.Embed(title="🏆 Classement", color=0xF1C40F)
        lines = []
        for i, (user_id, total) in enumerate(rows, start=1):
            # On tente de récupérer le nom depuis le cache, sinon on fetch
            user = self.bot.get_user(user_id)
            if user is None:
                try:
                    user = await self.bot.fetch_user(user_id)
                except:
                    user = None
            
            user_name = user.display_name if user else f"ID:{user_id}"
            lines.append(f"**{i}.** {user_name} — {total} 💶")
            
        embed.description = "\n".join(lines)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))