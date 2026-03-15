import sqlite3
import os

# Utilisation d'un chemin relatif pour plus de flexibilité (Docker/Local)
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "economy.db")

def ensure_db_dir():
    """S'assure que le dossier de la base de données existe."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"📁 Dossier '{DB_DIR}' créé.")

def init_db():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS economy (
        user_id INTEGER PRIMARY KEY,
        wallet  INTEGER DEFAULT 100,
        bank    INTEGER DEFAULT 0,
        last_daily TEXT DEFAULT 'Jamais'
    )
    """)
    conn.commit()
    conn.close()
    print("✅ Base de données SQLite connectée.")

def get_data(user_id: int) -> tuple:
    """Retourne (wallet, bank, last_daily). Crée le joueur s'il n'existe pas."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT wallet, bank, last_daily FROM economy WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res is None:
        cursor.execute("INSERT INTO economy (user_id) VALUES (?)", (user_id,))
        conn.commit()
        res = (100, 0, "Jamais")
    conn.close()
    return res

def update_db(user_id: int, wallet_diff: int = 0, bank_diff: int = 0, new_daily: str = None):
    """Met à jour le portefeuille / la banque / la date daily."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if new_daily:
        cursor.execute(
            "UPDATE economy SET wallet = wallet + ?, bank = bank + ?, last_daily = ? WHERE user_id = ?",
            (wallet_diff, bank_diff, new_daily, user_id),
        )
    else:
        cursor.execute(
            "UPDATE economy SET wallet = wallet + ?, bank = bank + ? WHERE user_id = ?",
            (wallet_diff, bank_diff, user_id),
        )
    conn.commit()
    conn.close()

def set_wallet(user_id: int, amount: int):
    """Définit directement le montant du portefeuille."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE economy SET wallet = ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_leaderboard(limit: int = 10) -> list:
    """Retourne les `limit` joueurs les plus riches (wallet + bank)."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, wallet + bank AS total FROM economy ORDER BY total DESC LIMIT ?",
        (limit,),
    )
    res = cursor.fetchall()
    conn.close()
    return res

def init_config_db():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table pour les réglages simples (ex: id_salon_photo)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        cle TEXT PRIMARY KEY,
        valeur TEXT
    )
    """)
    # Table pour les réactions (mot -> réponse)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS custom_reactions (
        mot TEXT PRIMARY KEY,
        reponse TEXT
    )
    """)
    conn.commit()
    conn.close()

def set_config(cle, valeur):
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (cle, valeur) VALUES (?, ?)", (cle, str(valeur)))
    conn.commit()
    conn.close()

def get_config(cle, default=None):
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT valeur FROM config WHERE cle = ?", (cle,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else default
