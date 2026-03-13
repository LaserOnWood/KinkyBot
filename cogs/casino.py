import discord
from discord import app_commands
from discord.ext import commands
import random

from utils.database import get_data, update_db


class Casino(commands.Cog):
    """Jeux de casino : roulette, machine à sous (extensible)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # /roulette
    @app_commands.command(name="roulette", description="Parier sur une couleur (rouge, noir, vert)")
    @app_commands.describe(couleur="rouge, noir ou vert", mise="Somme à parier")
    async def roulette(self, interaction: discord.Interaction, couleur: str, mise: int):
        user_id = interaction.user.id
        wallet, _, _ = get_data(user_id)
        couleur = couleur.lower()

        if couleur not in ("rouge", "noir", "vert"):
            return await interaction.response.send_message(
                "❌ Couleur invalide. Choisis : `rouge`, `noir` ou `vert`.", ephemeral=True
            )
        if mise <= 0 or mise > wallet:
            return await interaction.response.send_message(
                "❌ Mise invalide ou insuffisante.", ephemeral=True
            )

        tirage = random.randint(0, 36)
        result_color = "vert" if tirage == 0 else ("rouge" if tirage <= 18 else "noir")
        multiplicateur = 35 if couleur == "vert" else 2

        if couleur == result_color:
            gain = mise * multiplicateur
            update_db(user_id, wallet_diff=gain - mise)
            result_text = f"🎉 Bravo ! Tu gagnes **{gain} 🪙** !"
        else:
            update_db(user_id, wallet_diff=-mise)
            result_text = f"💀 Perdu... Tu perds **{mise} 🪙**."

        color_map = {"rouge": 0xE74C3C, "noir": 0x2C3E50, "vert": 0x2ECC71}
        embed = discord.Embed(title="🎰 Roulette", description=result_text, color=color_map[result_color])
        embed.add_field(
            name="Résultat",
            value=f"Le numéro **{tirage}** est tombé sur le **{result_color.upper()}**",
        )
        await interaction.response.send_message(embed=embed)

    # /machine_a_sous
    @app_commands.command(name="machine_a_sous", description="Tenter ta chance à la machine à sous")
    @app_commands.describe(mise="Somme à parier")
    async def slots(self, interaction: discord.Interaction, mise: int):
        user_id = interaction.user.id
        wallet, _, _ = get_data(user_id)

        if mise <= 0 or mise > wallet:
            return await interaction.response.send_message("❌ Mise invalide.", ephemeral=True)

        symboles = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]
        rouleaux = [random.choice(symboles) for _ in range(3)]
        affichage = " | ".join(rouleaux)

        if rouleaux[0] == rouleaux[1] == rouleaux[2]:
            multi = 10 if rouleaux[0] == "💎" else 5
            gain = mise * multi
            update_db(user_id, wallet_diff=gain - mise)
            result = f"🎉 JACKPOT ! Tu gagnes **{gain} 🪙** (x{multi}) !"
        elif rouleaux[0] == rouleaux[1] or rouleaux[1] == rouleaux[2]:
            gain = mise * 2
            update_db(user_id, wallet_diff=gain - mise)
            result = f"✨ Deux identiques ! Tu gagnes **{gain} 🪙** (x2) !"
        else:
            update_db(user_id, wallet_diff=-mise)
            result = f"💀 Rien... Tu perds **{mise} 🪙**."

        embed = discord.Embed(title="🎰 Machine à sous", color=0x9B59B6)
        embed.add_field(name="Rouleaux", value=f"[ {affichage} ]", inline=False)
        embed.description = result
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Casino(bot))
