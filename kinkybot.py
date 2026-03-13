import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import random
import os
from datetime import date

# --- 1. CHARGEMENT DU TOKEN ---
def load_token():
    if not os.path.exists("token.txt"):
        print("❌ Erreur : Créez un fichier 'token.txt' avec votre token Discord dedans.")
        exit()
    with open("token.txt", "r") as f:
        return f.read().strip()

TOKEN = load_token()

# --- 2. GESTION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS economy (
        user_id INTEGER PRIMARY KEY,
        wallet INTEGER DEFAULT 100,
        bank INTEGER DEFAULT 0,
        last_daily TEXT DEFAULT 'Jamais'
    )
    """)
    conn.commit()
    conn.close()

def get_data(user_id):
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT wallet, bank, last_daily FROM economy WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res is None:
        cursor.execute("INSERT INTO economy (user_id) VALUES (?)", (user_id,))
        conn.commit()
        res = (100, 0, 'Jamais')
    conn.close()
    return res

def update_db(user_id, wallet_diff=0, bank_diff=0, new_daily=None):
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    if new_daily:
        cursor.execute("UPDATE economy SET wallet = wallet + ?, bank = bank + ?, last_daily = ? WHERE user_id = ?", 
                       (wallet_diff, bank_diff, new_daily, user_id))
    else:
        cursor.execute("UPDATE economy SET wallet = wallet + ?, bank = bank + ? WHERE user_id = ?", 
                       (wallet_diff, bank_diff, user_id))
    conn.commit()
    conn.close()

# --- 3. CONFIGURATION DU BOT ---
class EconomyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        init_db()
        print("✅ Base de données SQLite connectée.")

bot = EconomyBot()

# --- 4. COMMANDES DE MAINTENANCE ---
@bot.command()
@commands.is_owner()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ {len(synced)} commandes Slash synchronisées !")

# --- 5. COMMANDES D'ÉCONOMIE (SLASH) ---

@bot.tree.command(name="solde", description="Consulter ton solde")
async def balance(interaction: discord.Interaction):
    wallet, bank, _ = get_data(interaction.user.id)
    embed = discord.Embed(title=f"🏦 Compte en banque de {interaction.user.display_name}", color=0x3498db)
    embed.add_field(name="Portefeuille", value=f"**{wallet}** 🪙", inline=True)
    embed.add_field(name="Banque", value=f"**{bank}** 🏦", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="quotidien", description="Récupérer ton bonus gratuit")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    _, _, last_daily = get_data(user_id)
    today = str(date.today())

    if last_daily == today:
        return await interaction.response.send_message("⏳ Reviens demain !", ephemeral=True)

    reward = 500
    update_db(user_id, wallet_diff=reward, new_daily=today)
    await interaction.response.send_message(f"🎁 **{reward} 🪙** ajoutés à ton portefeuille !")

@bot.tree.command(name="travail", description="Travailler pour gagner de l'argent")
async def work(interaction: discord.Interaction):
    gain = random.randint(70, 200)
    update_db(interaction.user.id, wallet_diff=gain)
    jobs = ["Mineur de Bitcoin", "Livreur Uber", "Modérateur Discord", "Mercenaire"]
    await interaction.response.send_message(f"💼 Job : **{random.choice(jobs)}** | Gain : **{gain} 🪙**")

@bot.tree.command(name="depot", description="Mettre de l'argent en banque")
async def deposit(interaction: discord.Interaction, montant: str):
    user_id = interaction.user.id
    wallet, _, _ = get_data(user_id)
    
    amt = wallet if montant.lower() == "all" else int(montant)
    if amt <= 0 or amt > wallet:
        return await interaction.response.send_message("❌ Montant invalide.", ephemeral=True)

    update_db(user_id, wallet_diff=-amt, bank_diff=amt)
    await interaction.response.send_message(f"✅ **{amt} 🪙** déposés en banque.")

@bot.tree.command(name="retrait", description="Retirer de l'argent de la banque")
async def withdraw(interaction: discord.Interaction, montant: str):
    user_id = interaction.user.id
    _, bank, _ = get_data(user_id)
    
    amt = bank if montant.lower() == "all" else int(montant)
    if amt <= 0 or amt > bank:
        return await interaction.Value("❌ Montant invalide.", ephemeral=True)

    update_db(user_id, wallet_diff=amt, bank_diff=-amt)
    await interaction.response.send_message(f"✅ **{amt} 🪙** retirés.")

# --- 6. CASINO : ROULETTE ---

@bot.tree.command(name="roulette", description="Parier sur une couleur (Rouge, Noir, Vert)")
@app_commands.describe(couleur="rouge, noir ou vert", mise="Somme à parier")
async def roulette(interaction: discord.Interaction, couleur: str, mise: int):
    user_id = interaction.user.id
    wallet, _, _ = get_data(user_id)
    couleur = couleur.lower()

    if mise <= 0 or mise > wallet:
        return await interaction.response.send_message("❌ Mise invalide ou insuffisante.", ephemeral=True)

    # Tirage (0 = Vert, 1-18 = Rouge, 19-36 = Noir)
    tirage = random.randint(0, 36)
    result_color = "vert" if tirage == 0 else ("rouge" if tirage <= 18 else "noir")
    
    win = False
    multiplicateur = 2 if couleur in ["rouge", "noir"] else 35
    
    if couleur == result_color:
        win = True
        gain = mise * multiplicateur
        update_db(user_id, wallet_diff=gain - mise)
    else:
        update_db(user_id, wallet_diff=-mise)

    embed = discord.Embed(title="🎰 Roulette", color=0xe74c3c if result_color == "rouge" else 0x2c3e50)
    embed.add_field(name="Résultat", value=f"Le numéro est tombé sur le **{result_color.upper()}** ({tirage})")
    
    if win:
        embed.description = f"🎉 Bravo ! Tu gagnes **{gain} 🪙** !"
    else:
        embed.description = f"💀 Perdu... Tu perds **{mise} 🪙**."
    
    await interaction.response.send_message(embed=embed)

# --- LANCEMENT ---
@bot.event
async def on_ready():
    print(f"🚀 Bot en ligne : {bot.user.name}")

bot.run(TOKEN)
