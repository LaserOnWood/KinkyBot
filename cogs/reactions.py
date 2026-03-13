import discord
from discord.ext import commands
import random


# --- Configuration des réponses automatiques ---
# Clé : mot-clé (en minuscules) | Valeur : liste de réponses possibles
TRIGGERS: dict[str, list[str]] = {
    "bonjour":   ["Salut ! 👋", "Bonjour toi ! ☀️", "Hey, ça va ? 😄"],
    "bonsoir":   ["Bonsoir ! 🌙", "Bonne soirée ! ✨"],
    "merci":     ["De rien ! 😊", "Avec plaisir !", "No problem 🤙"],
    "gg":        ["GG ! 🎉", "Bien joué ! 💪", "Champion 🏆"],
    "bonne nuit":["Bonne nuit ! 🌙😴", "Dors bien ! 💤"],
    "help":      ["Tu peux utiliser `/` pour voir toutes les commandes ! 📖"],
}

# Emojis ajoutés automatiquement selon certains mots
EMOJI_TRIGGERS: dict[str, str] = {
    "incroyable": "🤯",
    "lol":        "😂",
    "triste":     "😢",
    "gg":         "🎉",
    "love":       "❤️",
    "haha":       "😂",
    "bite":       "🍆",
}


class Reactions(commands.Cog):
    """Réactions automatiques aux messages (texte + emoji)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ne pas réagir aux bots
        if message.author.bot:
            return

        content_lower = message.content.lower()

        # --- Réponse texte via Embed ---
        for trigger, responses in TRIGGERS.items():
            if trigger in content_lower:
                embed = discord.Embed(
                    description=random.choice(responses),
                    color=0x3498DB
                )
                # Optionnel: On peut ajouter le nom de l'utilisateur dans l'embed
                embed.set_footer(text=f"Réponse pour {message.author.display_name}")
                await message.channel.send(embed=embed)
                break  # une seule réponse par message

        # --- Ajout d'emoji ---
        for word, emoji in EMOJI_TRIGGERS.items():
            if word in content_lower:
                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    pass

        # Laisser les autres commandes se traiter normalement
        await self.bot.process_commands(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reactions(bot))
