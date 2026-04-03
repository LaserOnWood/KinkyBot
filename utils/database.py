import sqlite3
import os
from contextlib import contextmanager

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURATION GLOBALE
# ═══════════════════════════════════════════════════════════════════

DB_DIR  = "data"
DB_PATH = os.path.join(DB_DIR, "kinkybot.db")


def _ensure_dir():
    """Crée le dossier data/ s'il n'existe pas."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)


@contextmanager
def _connect():
    """Context manager : ouvre une connexion SQLite et la ferme proprement."""
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # accès par nom de colonne
    conn.execute("PRAGMA journal_mode=WAL") # meilleures performances en écriture
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════
#  INITIALISATION GLOBALE
# ═══════════════════════════════════════════════════════════════════

def init_db():
    """Crée / migre toutes les tables de tous les modules enregistrés."""
    _ensure_dir()
    with _connect() as conn:
        for name, fn in _MODULES.items():
            fn(conn)
            print(f"  ✅ Table(s) [{name}] prêtes.")
    print("✅ Base de données initialisée.")


# ═══════════════════════════════════════════════════════════════════
#  MODULE : ÉCONOMIE
# ═══════════════════════════════════════════════════════════════════

def _init_economy(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS economy (
            user_id    INTEGER PRIMARY KEY,
            wallet     INTEGER NOT NULL DEFAULT 100,
            bank       INTEGER NOT NULL DEFAULT 0,
            last_daily TEXT    NOT NULL DEFAULT 'Jamais'
        )
    """)


# --- Lecture ---

def get_data(user_id: int) -> tuple[int, int, str]:
    """Retourne (wallet, bank, last_daily). Crée le joueur s'il n'existe pas."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT wallet, bank, last_daily FROM economy WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if row is None:
            conn.execute("INSERT INTO economy (user_id) VALUES (?)", (user_id,))
            return (100, 0, "Jamais")
        return (row["wallet"], row["bank"], row["last_daily"])


def get_leaderboard(limit: int = 10) -> list[tuple[int, int]]:
    """Retourne les `limit` joueurs les plus riches (wallet + bank)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT user_id, wallet + bank AS total FROM economy ORDER BY total DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [(r["user_id"], r["total"]) for r in rows]


# --- Écriture ---

def update_db(
    user_id: int,
    wallet_diff: int = 0,
    bank_diff: int   = 0,
    new_daily: str   = None,
):
    """Met à jour le portefeuille / la banque / la date du daily."""
    with _connect() as conn:
        if new_daily:
            conn.execute(
                """UPDATE economy
                   SET wallet = wallet + ?, bank = bank + ?, last_daily = ?
                   WHERE user_id = ?""",
                (wallet_diff, bank_diff, new_daily, user_id),
            )
        else:
            conn.execute(
                """UPDATE economy
                   SET wallet = wallet + ?, bank = bank + ?
                   WHERE user_id = ?""",
                (wallet_diff, bank_diff, user_id),
            )


def set_wallet(user_id: int, amount: int):
    """Définit directement le montant du portefeuille."""
    with _connect() as conn:
        conn.execute(
            "UPDATE economy SET wallet = ? WHERE user_id = ?",
            (amount, user_id)
        )


def set_bank(user_id: int, amount: int):
    """Définit directement le montant de la banque."""
    with _connect() as conn:
        conn.execute(
            "UPDATE economy SET bank = ? WHERE user_id = ?",
            (amount, user_id)
        )


# ═══════════════════════════════════════════════════════════════════
#  MODULE : CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

def _init_config(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS config (
            cle    TEXT PRIMARY KEY,
            valeur TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_reactions (
            mot     TEXT PRIMARY KEY,
            reponse TEXT NOT NULL DEFAULT ''
        )
    """)


# --- Config générale (clé / valeur) ---

def get_config(cle: str, default: str = None) -> str | None:
    """Retourne la valeur associée à une clé de config, ou `default`."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT valeur FROM config WHERE cle = ?", (cle,)
        ).fetchone()
    return row["valeur"] if row else default


def set_config(cle: str, valeur) -> None:
    """Insère ou remplace une paire clé/valeur dans la config."""
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (cle, valeur) VALUES (?, ?)",
            (cle, str(valeur))
        )


def delete_config(cle: str) -> None:
    """Supprime une clé de config."""
    with _connect() as conn:
        conn.execute("DELETE FROM config WHERE cle = ?", (cle,))


def get_all_config() -> dict[str, str]:
    """Retourne toute la table config sous forme de dict."""
    with _connect() as conn:
        rows = conn.execute("SELECT cle, valeur FROM config").fetchall()
    return {r["cle"]: r["valeur"] for r in rows}


# --- Réactions personnalisées ---

def get_reaction(mot: str) -> str | None:
    """Retourne la réponse associée à un mot-clé, ou None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT reponse FROM custom_reactions WHERE mot = ?", (mot,)
        ).fetchone()
    return row["reponse"] if row else None


def set_reaction(mot: str, reponse: str) -> None:
    """Insère ou remplace une réaction personnalisée."""
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO custom_reactions (mot, reponse) VALUES (?, ?)",
            (mot, reponse)
        )


def delete_reaction(mot: str) -> None:
    """Supprime une réaction personnalisée."""
    with _connect() as conn:
        conn.execute(
            "DELETE FROM custom_reactions WHERE mot = ?", (mot,)
        )


def get_all_reactions() -> dict[str, str]:
    """Retourne toutes les réactions personnalisées sous forme de dict."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT mot, reponse FROM custom_reactions"
        ).fetchall()
    return {r["mot"]: r["reponse"] for r in rows}


# ═══════════════════════════════════════════════════════════════════
#  MODULE : NIVEAUX (XP)
# ═══════════════════════════════════════════════════════════════════

def _init_levels(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS levels (
            user_id    INTEGER PRIMARY KEY,
            xp         INTEGER NOT NULL DEFAULT 0,
            level      INTEGER NOT NULL DEFAULT 0,
            last_msg   REAL    NOT NULL DEFAULT 0
        )
    """)


# ═══════════════════════════════════════════════════════════════════
#  REGISTRE DES MODULES
# ═══════════════════════════════════════════════════════════════════

_MODULES: dict[str, callable] = {
    "economy":  _init_economy,
    "config":   _init_config,
    "levels":   _init_levels,
}
