import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import random

# --- CONFIGURATION GIPHY ---
def charger_giphy_key() -> str:
    if key := os.environ.get("GIPHY_API_KEY"):
        return key
    if os.path.exists("giphy_key.txt"):
        with open("giphy_key.txt", "r") as f:
            return f.read().strip()
    return "dc6zaTOxFJmzC"

GIPHY_API_KEY = charger_giphy_key()
GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"
GIPHY_RANDOM_URL = "https://api.giphy.com/v1/gifs/random"

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

class Gifs(commands.Cog):
    """Commandes GIF propulsées par l'API Giphy avec session optimisée."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def _fetch_gif(self, tag: str) -> str | None:
        params = {
            "api_key": GIPHY_API_KEY,
            "q":       tag,
            "limit":   20,
            "rating":  "pg-13",
            "lang":    "fr",
        }
        try:
            async with self.session.get(GIPHY_SEARCH_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("data", [])
                    if results:
                        return random.choice(results)["images"]["original"]["url"]
        except Exception as e:
            print(f"⚠️ Erreur Giphy (fetch_gif): {e}")
        return None

    async def _fetch_random_gif(self, tag: str = "") -> str | None:
        params = {"api_key": GIPHY_API_KEY, "rating": "pg-13"}
        if tag: params["tag"] = tag
        try:
            async with self.session.get(GIPHY_RANDOM_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", {}).get("images", {}).get("original", {}).get("url")
        except Exception as e:
            print(f"⚠️ Erreur Giphy (fetch_random_gif): {e}")
        return None

    def _build_embed(self, titre: str, gif_url: str, couleur: int, auteur: discord.User) -> discord.Embed:
        embed = discord.Embed(title=titre, color=couleur)
        embed.set_image(url=gif_url)
        embed.set_footer(text=f"Demandé par {auteur.display_name} • Powered by Giphy")
        return embed

    @app_commands.command(name="gif", description="Rechercher un GIF sur Giphy")
    @app_commands.describe(recherche="Ce que tu veux chercher")
    async def gif(self, interaction: discord.Interaction, recherche: str):
        await interaction.response.defer()
        url = await self._fetch_gif(recherche)
        if not url:
            return await interaction.followup.send("❌ Aucun GIF trouvé pour cette recherche.", ephemeral=True)
        await interaction.followup.send(embed=self._build_embed(f"🔍 {recherche}", url, 0x00B4FF, interaction.user))

    @app_commands.command(name="gif_random", description="Obtenir un GIF aléatoire")
    async def gif_random(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = await self._fetch_random_gif()
        if not url:
            return await interaction.followup.send("❌ Impossible de récupérer un GIF.", ephemeral=True)
        await interaction.followup.send(embed=self._build_embed("🎲 GIF aléatoire", url, 0x9B59B6, interaction.user))

    async def _action_command(self, interaction: discord.Interaction, membre: discord.Member, action_key: str, phrase: str, couleur: int):
        await interaction.response.defer()
        url = await self._fetch_gif(GIF_CATEGORIES[action_key])
        if not url:
            return await interaction.followup.send("❌ GIF introuvable.")
        titre = phrase.format(user=interaction.user.display_name, target=membre.display_name)
        await interaction.followup.send(embed=self._build_embed(titre, url, couleur, interaction.user))

    @app_commands.command(name="câlin", description="Envoyer un câlin à quelqu'un")
    async def calin(self, interaction: discord.Interaction, membre: discord.Member):
        await self._action_command(interaction, membre, "câlin", "🤗 {user} fait un câlin à {target} !", 0xFF69B4)

    @app_commands.command(name="bisou", description="Envoyer un bisou à quelqu'un")
    async def bisou(self, interaction: discord.Interaction, membre: discord.Member):
        await self._action_command(interaction, membre, "bisou", "😘 {user} fait un bisou à {target} !", 0xFF1493)

    @app_commands.command(name="gifle", description="Gifler quelqu'un")
    async def gifle(self, interaction: discord.Interaction, membre: discord.Member):
        await self._action_command(interaction, membre, "gifle", "👋 {user} gifle {target} !", 0xE74C3C)

    @app_commands.command(name="pat", description="Faire un pat à quelqu'un")
    async def pat(self, interaction: discord.Interaction, membre: discord.Member):
        await self._action_command(interaction, membre, "pat", "🤚 {user} fait un pat à {target} !", 0xF39C12)

    @app_commands.command(name="pleurer", description="Exprimer ta tristesse en GIF")
    async def pleurer(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = await self._fetch_gif(GIF_CATEGORIES["pleurer"])
        if not url: return await interaction.followup.send("❌ GIF introuvable.")
        await interaction.followup.send(embed=self._build_embed(f"😢 {interaction.user.display_name} pleure...", url, 0x3498DB, interaction.user))

    @app_commands.command(name="danse", description="Danser !")
    async def danse(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = await self._fetch_gif(GIF_CATEGORIES["danse"])
        if not url: return await interaction.followup.send("❌ GIF introuvable.")
        await interaction.followup.send(embed=self._build_embed(f"💃 {interaction.user.display_name} danse !", url, 0x2ECC71, interaction.user))

    @app_commands.command(name="facepalm", description="Exprimer ton désespoir")
    async def facepalm(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = await self._fetch_gif(GIF_CATEGORIES["facepalm"])
        if not url: return await interaction.followup.send("❌ GIF introuvable.")
        await interaction.followup.send(embed=self._build_embed(f"🤦 {interaction.user.display_name}...", url, 0x95A5A6, interaction.user))

    @app_commands.command(name="bravo", description="Applaudir quelqu'un")
    async def bravo(self, interaction: discord.Interaction, membre: discord.Member = None):
        await interaction.response.defer()
        url = await self._fetch_gif(GIF_CATEGORIES["bravo"])
        if not url: return await interaction.followup.send("❌ GIF introuvable.")
        cible = f" pour {membre.display_name}" if membre else ""
        await interaction.followup.send(embed=self._build_embed(f"👏 Bravo{cible} !", url, 0xF1C40F, interaction.user))

async def setup(bot: commands.Bot):
    await bot.add_cog(Gifs(bot))
