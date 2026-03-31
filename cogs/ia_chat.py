import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os


# ------------------------------------------------------------------ #
#  CHARGEMENT DES CLÉS API
# ------------------------------------------------------------------ #

def charger_cle(env_var: str, fichier: str) -> str | None:
    """Charge une clé API depuis une variable d'environnement ou un fichier .txt."""
    if key := os.environ.get(env_var):
        return key
    if os.path.exists(fichier):
        with open(fichier, "r") as f:
            return f.read().strip()
    return None


GEMINI_API_KEY  = charger_cle("GEMINI_API_KEY",  "gemini_key.txt")
OPENAI_API_KEY  = charger_cle("OPENAI_API_KEY",  "openai_key.txt")
MISTRAL_API_KEY = charger_cle("MISTRAL_API_KEY", "mistral_key.txt")

# URLs des APIs
GEMINI_URL  = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
OPENAI_URL  = "https://api.openai.com/v1/chat/completions"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"


# ------------------------------------------------------------------ #
#  FONCTIONS D'APPEL AUX APIs
# ------------------------------------------------------------------ #

async def appeler_gemini(question: str) -> str:
    """Envoie une question à l'API Gemini et retourne la réponse."""
    if not GEMINI_API_KEY:
        return "❌ Clé API Gemini manquante (`GEMINI_API_KEY` ou `gemini_key.txt`)."

    payload = {
        "contents": [
            {"parts": [{"text": question}]}
        ]
    }
    params = {"key": GEMINI_API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_URL, params=params, json=payload) as resp:
            if resp.status != 200:
                erreur = await resp.text()
                return f"❌ Erreur Gemini ({resp.status}) : {erreur[:300]}"
            data = await resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                return "❌ Réponse Gemini inattendue."


async def appeler_chatgpt(question: str) -> str:
    """Envoie une question à l'API OpenAI (ChatGPT) et retourne la réponse."""
    if not OPENAI_API_KEY:
        return "❌ Clé API OpenAI manquante (`OPENAI_API_KEY` ou `openai_key.txt`)."

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": question}],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(OPENAI_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                erreur = await resp.text()
                return f"❌ Erreur ChatGPT ({resp.status}) : {erreur[:300]}"
            data = await resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return "❌ Réponse ChatGPT inattendue."


async def appeler_mistral(question: str) -> str:
    """Envoie une question à l'API Mistral et retourne la réponse."""
    if not MISTRAL_API_KEY:
        return "❌ Clé API Mistral manquante (`MISTRAL_API_KEY` ou `mistral_key.txt`)."

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": question}],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(MISTRAL_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                erreur = await resp.text()
                return f"❌ Erreur Mistral ({resp.status}) : {erreur[:300]}"
            data = await resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return "❌ Réponse Mistral inattendue."


# ------------------------------------------------------------------ #
#  HELPER : Tronque la réponse si elle dépasse la limite Discord
# ------------------------------------------------------------------ #

def tronquer(texte: str, limite: int = 4000) -> str:
    """Tronque proprement un texte trop long pour un embed Discord."""
    if len(texte) <= limite:
        return texte
    return texte[:limite] + "\n\n*[Réponse tronquée — trop longue pour Discord]*"


# ------------------------------------------------------------------ #
#  COG
# ------------------------------------------------------------------ #

class IaChat(commands.Cog):
    """Commandes IA : pose des questions à Gemini, ChatGPT ou Mistral."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_embed(
        self,
        question: str,
        reponse: str,
        ia_nom: str,
        couleur: int,
        emoji: str,
        auteur: discord.User,
    ) -> discord.Embed:
        embed = discord.Embed(
            title=f"{emoji} {ia_nom}",
            color=couleur,
        )
        embed.add_field(name="❓ Question", value=tronquer(question, 1000), inline=False)
        embed.add_field(name="💬 Réponse",  value=tronquer(reponse,   3000), inline=False)
        embed.set_footer(text=f"Demandé par {auteur.display_name}")
        return embed

    # /gemini
    @app_commands.command(name="gemini", description="Pose une question à Gemini (Google)")
    @app_commands.describe(question="Ta question pour Gemini")
    async def gemini(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        reponse = await appeler_gemini(question)
        embed = self._build_embed(
            question, reponse,
            ia_nom="Gemini — Google",
            couleur=0x4285F4,
            emoji="🔵",
            auteur=interaction.user,
        )
        await interaction.followup.send(embed=embed)

    # /chatgpt
    @app_commands.command(name="chatgpt", description="Pose une question à ChatGPT (OpenAI)")
    @app_commands.describe(question="Ta question pour ChatGPT")
    async def chatgpt(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        reponse = await appeler_chatgpt(question)
        embed = self._build_embed(
            question, reponse,
            ia_nom="ChatGPT — OpenAI",
            couleur=0x10A37F,
            emoji="🟢",
            auteur=interaction.user,
        )
        await interaction.followup.send(embed=embed)

    # /mistral
    @app_commands.command(name="mistral", description="Pose une question à Mistral AI")
    @app_commands.describe(question="Ta question pour Mistral")
    async def mistral(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        reponse = await appeler_mistral(question)
        embed = self._build_embed(
            question, reponse,
            ia_nom="Mistral AI",
            couleur=0xFF7000,
            emoji="🌪️",
            auteur=interaction.user,
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(IaChat(bot))
