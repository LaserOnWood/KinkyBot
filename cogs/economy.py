import discord
from discord import app_commands
from discord.ext import commands
from datetime import date
import random

from utils.database import get_data, update_db, init_db, get_leaderboard


class Economy(commands.Cog):
    """Commandes d'économie : solde, daily, travail, dépôt, retrait, classement."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db()

    # /bal
    @app_commands.command(name="bal", description="Consulter ton solde")
    async def balance(self, interaction: discord.Interaction):
        wallet, bank, _ = get_data(interaction.user.id)
        embed = discord.Embed(
            title=f"🏦 Compte de {interaction.user.name}",
            color=0x3498DB,
        )
        embed.add_field(name="Portefeuille", value=f"**{wallet}** 🪙", inline=True)
        embed.add_field(name="Banque",        value=f"**{bank}** 🏦",  inline=True)
        await interaction.response.send_message(embed=embed)

    # /daily
    @app_commands.command(name="daily", description="Récupérer ton bonus quotidien")
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        _, _, last_daily = get_data(user_id)
        today = str(date.today())

        if last_daily == today:
            return await interaction.response.send_message("⏳ Reviens demain !", ephemeral=True)

        reward = 500
        update_db(user_id, wallet_diff=reward, new_daily=today)
        await interaction.response.send_message(f"🎁 **{reward} 🪙** ajoutés à ton portefeuille !")

    # /work
    @app_commands.command(name="work", description="Travailler pour gagner de l'argent")
    async def work(self, interaction: discord.Interaction):
        gain = random.randint(70, 200)
        update_db(interaction.user.id, wallet_diff=gain)
        jobs = ["Mineur de Bitcoin", "Livreur Uber", "Modérateur Discord", "Mercenaire", "Streamer Twitch"]
        await interaction.response.send_message(
            f"💼 Job : **{random.choice(jobs)}** | Gain : **{gain} 🪙**"
        )

    # /dep
    @app_commands.command(name="dep", description="Déposer de l'argent en banque")
    @app_commands.describe(montant="Montant à déposer (ou 'all')")
    async def deposit(self, interaction: discord.Interaction, montant: str):
        user_id = interaction.user.id
        wallet, _, _ = get_data(user_id)

        amt = wallet if montant.lower() == "all" else int(montant)
        if amt <= 0 or amt > wallet:
            return await interaction.response.send_message("❌ Montant invalide.", ephemeral=True)

        update_db(user_id, wallet_diff=-amt, bank_diff=amt)
        await interaction.response.send_message(f"✅ **{amt} 🪙** déposés en banque.")

    # /with
    @app_commands.command(name="with", description="Retirer de l'argent de la banque")
    @app_commands.describe(montant="Montant à retirer (ou 'all')")
    async def withdraw(self, interaction: discord.Interaction, montant: str):
        user_id = interaction.user.id
        _, bank, _ = get_data(user_id)

        amt = bank if montant.lower() == "all" else int(montant)
        if amt <= 0 or amt > bank:
            return await interaction.response.send_message("❌ Montant invalide.", ephemeral=True)

        update_db(user_id, wallet_diff=amt, bank_diff=-amt)
        await interaction.response.send_message(f"✅ **{amt} 🪙** retirés.")

    # /top
    @app_commands.command(name="top", description="Classement des joueurs les plus riches")
    async def leaderboard(self, interaction: discord.Interaction):
        rows = get_leaderboard(10)
        if not rows:
            return await interaction.response.send_message("Aucun joueur pour l'instant.")

        embed = discord.Embed(title="🏆 Classement", color=0xF1C40F)
        lines = []
        for i, (user_id, total) in enumerate(rows, start=1):
            user = self.bot.get_user(user_id) or f"ID:{user_id}"
            lines.append(f"**{i}.** {user} — {total} 🪙")
        embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))