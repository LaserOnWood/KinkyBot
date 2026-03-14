import discord
from discord.ext import commands
import os

# --- 1. CHARGEMENT DU TOKEN ---
def charger_token():
    """Lit le token depuis le fichier token.txt à la racine."""
    if not os.path.exists("token.txt"):
        print("❌ Erreur : Le fichier 'token.txt' est introuvable.")
        exit()
    with open("token.txt", "r") as f:
        return f.read().strip()

# --- 2. CLASSE PRINCIPALE DU BOT ---
class KinkyBot(commands.Bot):
    def __init__(self):
        # Configuration des permissions (Intents)
        intents = discord.Intents.default()
        intents.message_content = True  # Pour lire les commandes avec préfixe (!)
        intents.members = True          # Pour gérer les pseudos et la modération
        
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Initialisation des modules (Cogs) avant la connexion."""
        modules = [
            "cogs.general",
            "cogs.economy",
            "cogs.casino",
            "cogs.reactions",
            "cogs.moderation",
            "cogs.gifs",
            "cogs.accueil",
            "cogs.fils_auto",
        ]
        
        print("--- Chargement des modules ---")
        for extension in modules:
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

# --- 4. COMMANDES D'ADMINISTRATION (PROPRIÉTAIRE UNIQUEMENT) ---

@bot.command(name="synchro")
@commands.is_owner()
async def synchro(ctx):
    """Synchronise les commandes slash et affiche le détail par module."""
    attente = await ctx.send("🔄 Analyse et synchronisation des modules en cours...")
    
    try:
        # Synchronisation globale avec les serveurs Discord
        commandes_synced = await bot.tree.sync()
        
        # Dictionnaire pour compter les commandes par catégorie (Cog)
        stats = {"Général": 0}
        
        # Tri des commandes synchronisées pour le rapport
        for cmd in commandes_synced:
            trouve = False
            for nom_cog, objet_cog in bot.cogs.items():
                # Récupère les noms des commandes slash rattachées à ce Cog
                commandes_slash_cog = [c.name for c in objet_cog.get_app_commands()]
                if cmd.name in commandes_slash_cog:
                    stats[nom_cog] = stats.get(nom_cog, 0) + 1
                    trouve = True
                    break
            
            if not trouve:
                stats["Général"] += 1

        # Construction du rapport détaillé
        rapport = "**✅ Synchronisation terminée !**\n"
        for categorie, nombre in stats.items():
            if nombre > 0:
                rapport += f"• `{categorie}` : {nombre} commande(s)\n"
        
        rapport += f"\n👉 Total : **{len(commandes_synced)}** commandes slash actives."
        
        await attente.edit(content=rapport)
        print(f"💾 Synchro réussie pour {ctx.author} ({len(commandes_synced)} commandes).")

    except Exception as e:
        erreur_msg = f"❌ Erreur lors de la synchronisation : {e}"
        await attente.edit(content=erreur_msg)
        print(erreur_msg)

@bot.command(name="recharger")
@commands.is_owner()
async def recharger(ctx, module: str):
    """Recharge un module spécifique (ex: !recharger economy)."""
    try:
        await bot.reload_extension(f"cogs.{module}")
        await ctx.send(f"✅ Le module `{module}` a été mis à jour avec succès !")
        print(f"♻️ Module rechargé : cogs.{module}")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors du rechargement de `{module}` : \n```{e}```")

# --- 5. LANCEMENT ---
if __name__ == "__main__":
    bot.run(charger_token())
