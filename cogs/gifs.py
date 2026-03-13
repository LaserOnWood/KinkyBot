import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os

# --- Configuration Giphy ---
# Récupère la clé API depuis la variable d'environnement GIPHY_API_KEY
# ou depuis le fichier giphy_key.txt à la racine du projet
def charger_giphy_key() -> str:
    if key := os.environ.get("GIPHY_API_KEY"):
        return key
    if os.path.exists("giphy_key.txt"):
        with open("giphy_key.txt", "r") as f:
            return f.read().strip()
    # Clé publique de test Giphy (limitée, pour le développement uniquement)
    return "dc6zaTOxFJmzC"

GIPHY_API_KEY = charger_giphy_key()
GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"
GIPHY_RANDOM_URL = "https://api.giphy.com/v1/gifs/random"

# --- Catégories prédéfinies ---
# Chaque commande slash correspond à un tag de recherche Giphy
GIF_CATEGORIES: dict[str, str] = {
    "câlin":    "hug anime",
    "bisou":    "kiss anime",
    "gifle":    "slap anime",
    "pleurer":  "cry anime",
    "rire":     "laugh anime",
    "bonjour":  "hello wave anime",
    "bonsoir":  "good night anime",
    "danse":    "dance happy",
    "facepalm": "facepalm",
    "pat":      "pat head anime",
    "bravo":    "clap congratulations",
    "shock":    "shocked surprised anime",
}


async def fetch_gif(tag: str) -> str | None:
    """Recherche un GIF sur Giphy et retourne son URL. Retourne None en cas d'erreur."""
    params = {
        "api_key": GIPHY_API_KEY,
        "q":       tag,
        "limit":   20,
        "rating":  "pg-13",
        "lang":    "fr",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(GIPHY_SEARCH_URL, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            results = data.get("data", [])
            if not results:
                return None
            import random
            gif = random.choice(results)
            return gif["images"]["original"]["url"]


async def fetch_random_gif(tag: str = "") -> str | None:
    """Récupère un GIF aléatoire (avec tag optionnel) depuis Giphy."""
    params = {
        "api_key": GIPHY_API_KEY,
        "rating":  "pg-13",
    }
    if tag:
        params["tag"] = tag

    async with aiohttp.ClientSession() as session:
        async with session.get(GIPHY_RANDOM_URL, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            gif = data.get("data", {})
            return gif.get("images", {}).get("original", {}).get("url")


class Gifs(commands.Cog):
    """Commandes GIF propulsées par l'API Giphy."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_embed(self, titre: str, gif_url: str, couleur: int, auteur: discord.User) -> discord.Embed:
        embed = discord.Embed(title=titre, color=couleur)
        embed.set_image(url=gif_url)
        embed.set_footer(text=f"Demandé par {auteur.display_name} • Powered by Giphy")
        return embed

    # /gif — recherche libre
    @app_commands.command(name="gif", description="Rechercher un GIF sur Giphy")
    @app_commands.describe(recherche="Ce que tu veux chercher")
    async def gif(self, interaction: discord.Interaction, recherche: str):
        await interaction.response.defer()
        url = await fetch_gif(recherche)
        if not url:
            return await interaction.followup.send("❌ Aucun GIF trouvé pour cette recherche.", ephemeral=True)
        embed = self._build_embed(f"🔍 {recherche}", url, 0x00B4FF, interaction.user)
        await interaction.followup.send(embed=embed)

    # /gif_random — GIF complètement aléatoire
    @app_commands.command(name="gif_random", description="Obtenir un GIF aléatoire")
    async def gif_random(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = await fetch_random_gif()
        if not url:
            return await interaction.followup.send("❌ Impossible de récupérer un GIF.", ephemeral=True)
        embed = self._build_embed("🎲 GIF aléatoire", url, 0x9B59B6, interaction.user)
        await interaction.followup.send(embed=embed)

    # --- Commandes d'actions ---

    @app_commands.command(name="câlin", description="Envoyer un câlin à quelqu'un")
    @app_commands.describe(membre="La personne à câliner")
    async def calin(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.response.defer()
        url = await fetch_gif(GIF_CATEGORIES["câlin"])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        embed = self._build_embed(
            f"🤗 {interaction.user.display_name} fait un câlin à {membre.display_name} !",
            url, 0xFF69B4, interaction.user
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bisou", description="Envoyer un bisou à quelqu'un")
    @app_commands.describe(membre="La personne à embrasser")
    async def bisou(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.response.defer()
        url = await fetch_gif(GIF_CATEGORIES["bisou"])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        embed = self._build_embed(
            f"😘 {interaction.user.display_name} fait un bisou à {membre.display_name} !",
            url, 0xFF1493, interaction.user
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gifle", description="Gifler quelqu'un")
    @app_commands.describe(membre="La personne à gifler")
    async def gifle(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.response.defer()
        url = await fetch_gif(GIF_CATEGORIES["gifle"])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        embed = self._build_embed(
            f"👋 {interaction.user.display_name} gifle {membre.display_name} !",
            url, 0xE74C3C, interaction.user
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pat", description="Faire un pat à quelqu'un")
    @app_commands.describe(membre="La personne à patter")
    async def pat(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.response.defer()
        url = await fetch_gif(GIF_CATEGORIES["pat"])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        embed = self._build_embed(
            f"🤚 {interaction.user.display_name} fait un pat à {membre.display_name} !",
            url, 0xF39C12, interaction.user
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pleurer", description="Exprimer ta tristesse en GIF")
    async def pleurer(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = await fetch_gif(GIF_CATEGORIES["pleurer"])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        embed = self._build_embed(
            f"😢 {interaction.user.display_name} pleure...",
            url, 0x3498DB, interaction.user
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="danse", description="Danser !")
    async def danse(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = await fetch_gif(GIF_CATEGORIES["danse"])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        embed = self._build_embed(
            f"💃 {interaction.user.display_name} danse !",
            url, 0x2ECC71, interaction.user
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="facepalm", description="Exprimer ton désespoir")
    async def facepalm(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = await fetch_gif(GIF_CATEGORIES["facepalm"])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        embed = self._build_embed(
            f"🤦 {interaction.user.display_name}...",
            url, 0x95A5A6, interaction.user
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bravo", description="Applaudir quelqu'un")
    @app_commands.describe(membre="La personne à féliciter (optionnel)")
    async def bravo(self, interaction: discord.Interaction, membre: discord.Member = None):
        await interaction.response.defer()
        url = await fetch_gif(GIF_CATEGORIES["bravo"])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        cible = f" pour {membre.display_name}" if membre else ""
        embed = self._build_embed(
            f"👏 Bravo{cible} !",
            url, 0xF1C40F, interaction.user
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Gifs(bot))
