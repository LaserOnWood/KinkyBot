import discord
from discord.ext import commands
import os
import sys  # Pour redémarrer le bot

# --- 1. CHARGEMENT DU TOKEN ---
def charger_token():
    """Récupère le token via variable d'environnement ou fichier local."""
    # 1. Tentative via variable d'environnement (Méthode Railway / Docker)
    if token := os.environ.get("DISCORD_TOKEN"):
        return token

    # 2. Tentative via fichier local (Méthode PC / Développement)
    if os.path.exists("token.txt"):
        with open("token.txt", "r") as f:
            return f.read().strip()

    # 3. Si rien n'est trouvé
    print("❌ Erreur : Aucun token trouvé dans l'environnement (DISCORD_TOKEN) ou dans token.txt")
    exit()


# --- 2. CONFIGURATION DES MODULES ---
# Liste centrale de tes cogs pour la gestion automatique
MODULES_LISTE = [
    "cogs.general",
    "cogs.economy",
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
        # Configuration des permissions (Intents)
        intents = discord.Intents.default()
        intents.message_content = True  # Pour lire les commandes !
        intents.members = True          # Pour l'accueil et les pseudos
        
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Initialisation des modules au démarrage."""
        print("--- Chargement des modules ---")
        for extension in MODULES_LISTE:
            try:
                await self.load_extension(extension)
                print(f"✅ {extension} chargé")
            except Exception as e:
                print(f"❌ Erreur sur {extension} : {e}")
        print("------------------------------")

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
    """Synchronise les commandes slash et affiche le détail par module."""
    attente = await ctx.send("🔄 Analyse et synchronisation des modules en cours...")
    
    try:
        commandes_synced = await bot.tree.sync()
        stats = {"Général": 0}
        
        for cmd in commandes_synced:
            trouve = False
            for nom_cog, objet_cog in bot.cogs.items():
                commandes_slash_cog = [c.name for c in objet_cog.get_app_commands()]
                if cmd.name in commandes_slash_cog:
                    stats[nom_cog] = stats.get(nom_cog, 0) + 1
                    trouve = True
                    break
            if not trouve:
                stats["Général"] += 1

        rapport = "**✅ Synchronisation terminée !**\n"
        for categorie, nombre in stats.items():
            if nombre > 0:
                rapport += f"• `{categorie}` : {nombre} commande(s)\n"
        
        rapport += f"\n👉 Total : **{len(commandes_synced)}** commandes slash actives."
        await attente.edit(content=rapport)

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
    print("--- Redémarrage demandé ---")
    
    # Fermeture propre
    await bot.close()
    
    # Relance le script python actuel
    os.execv(sys.executable, ['python3'] + sys.argv)

# --- 5. LANCEMENT ---
if __name__ == "__main__":
    bot.run(charger_token())
