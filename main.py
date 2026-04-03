import discord
from discord.ext import commands
import os
import sys
from utils.database import init_db

# --- 1. CHARGEMENT DU TOKEN ---
def charger_token():
    """Récupère le token via variable d'environnement ou fichier local."""
    if token := os.environ.get("DISCORD_TOKEN"):
        return token

    if os.path.exists("token.txt"):
        with open("token.txt", "r") as f:
            return f.read().strip()

    print("❌ Erreur : Aucun token trouvé dans l'environnement (DISCORD_TOKEN) ou dans token.txt")
    exit()


# --- 2. CONFIGURATION DES MODULES ---
MODULES_LISTE = [
    "cogs.general",
    "cogs.economy",
    "cogs.nsfw",
    "cogs.niveaux",
    "cogs.casino",
    "cogs.reactions",
    "cogs.moderation",
    "cogs.gifs",
    "cogs.accueil",
    "cogs.fils_auto",
    "cogs.playparty",
    "cogs.config",
    "cogs.exportBDD",
]

class KinkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Initialisation des modules et de la base de données."""
        # Initialisation de la BDD
        init_db()
        
        print("--- Chargement des modules ---")
        for extension in MODULES_LISTE:
            try:
                await self.load_extension(extension)
                print(f"✅ {extension} chargé")
            except Exception as e:
                print(f"❌ Erreur sur {extension} : {e}")
        print("------------------------------")
        
        # Enregistrement des Persistent Views
        from cogs.config import ConfigMainView, ReactionConfigView
        self.add_view(ConfigMainView())
        self.add_view(ReactionConfigView())

    async def on_ready(self):
        """Confirmation de la mise en ligne."""
        print(f"🚀 Bot en ligne : {self.user.name}")
        print(f"🆔 ID : {self.user.id}")
        print("------------------------------")

# --- 3. INITIALISATION ---
bot = KinkyBot()

# --- 4. COMMANDES D'ADMINISTRATION (OWNER UNIQUEMENT) ---

@bot.command(name="synchro")
@commands.is_owner()
async def synchro(ctx):
    """Synchronise les commandes slash."""
    attente = await ctx.send("🔄 Analyse et synchronisation des modules en cours...")
    try:
        commandes_synced = await bot.tree.sync()
        await attente.edit(content=f"✅ Synchronisation terminée ! **{len(commandes_synced)}** commandes slash actives.")
    except Exception as e:
        await attente.edit(content=f"❌ Erreur lors de la synchronisation : {e}")

@bot.command(name="recharger")
@commands.is_owner()
async def recharger(ctx, module: str):
    """Recharge un module précis ou 'tout'."""
    if module.lower() == "tout":
        erreurs = []
        succes = 0
        for m in MODULES_LISTE:
            try:
                await bot.reload_extension(m)
                succes += 1
            except Exception as e:
                erreurs.append(f"{m}: {e}")
        
        msg = f"✅ **{succes}** modules rechargés."
        if erreurs:
            msg += f"\n❌ **{len(erreurs)}** erreurs rencontrées."
        await ctx.send(msg)
    else:
        try:
            nom_complet = f"cogs.{module}" if not module.startswith("cogs.") else module
            await bot.reload_extension(nom_complet)
            await ctx.send(f"✅ Le module `{nom_complet}` a été mis à jour !")
        except Exception as e:
            await ctx.send(f"❌ Erreur sur `{module}` : \n```{e}```")

@bot.command(name="relancer")
@commands.is_owner()
async def relancer(ctx):
    """Redémarre complètement le processus du bot."""
    await ctx.send("♻️ Redémarrage du bot en cours... Patientez.")
    await bot.close()
    os.execv(sys.executable, ['python3'] + sys.argv)

# --- 5. LANCEMENT ---
if __name__ == "__main__":
    bot.run(charger_token())
