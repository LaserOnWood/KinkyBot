import discord
from discord.ext import commands
import os

def load_token():
    if not os.path.exists("token.txt"):
        print("❌ Erreur : Créez un fichier 'token.txt' avec votre token Discord dedans.")
        exit()
    with open("token.txt", "r") as f:
        return f.read().strip()

class KinkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        cogs = [
            "cogs.economy",
            "cogs.casino",
            "cogs.reactions",
            "cogs.gifs",
            "cogs.moderation",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ {cog} chargé")
            except Exception as e:
                print(f"❌ Erreur chargement {cog} : {e}")

    async def on_ready(self):
        print(f"🚀 Bot en ligne : {self.user.name}")

# --- Commandes owner ---
bot = KinkyBot()

@bot.command()
@commands.is_owner()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ {len(synced)} commandes Slash synchronisées !")

@bot.command()
@commands.is_owner()
async def reload(ctx, cog: str):
    """Recharger un cog sans redémarrer le bot. Ex: !reload economy"""
    try:
        await bot.reload_extension(f"cogs.{cog}")
        await ctx.send(f"✅ `cogs.{cog}` rechargé !")
    except Exception as e:
        await ctx.send(f"❌ Erreur : {e}")

bot.run(load_token())