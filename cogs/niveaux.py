"""
cogs/levels.py — Système de niveaux pour KinkyBot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sources d'XP  : messages, réactions données/reçues, présence vocale
Notifications : DM obligatoire + annonce dans salon dédié (salon_levelup)
Récompenses   : crédits economy + rôles automatiques Discord
Missions      : permanentes (secrètes ou visibles), journalières (cooldown 24h),
                et missions débloquées à certains niveaux
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import sqlite3
import os
import time
from contextlib import contextmanager
from datetime import datetime, date, timedelta

from utils.database import get_config, update_db as economy_update

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION GÉNÉRALE
# ═══════════════════════════════════════════════════════════════════════════════

XP_MESSAGE        = (8, 20)   # (min, max) XP par message
XP_REACTION_GIVE  = 3         # XP quand tu réagis à un message
XP_REACTION_GET   = 5         # XP quand ton message reçoit une réaction
XP_VOCAL_TICK     = 10        # XP par tick de présence vocale
VOCAL_INTERVAL    = 60        # Secondes entre deux ticks vocaux

COOLDOWN_MESSAGE  = 20        # Secondes entre deux gains XP par message
COOLDOWN_REACTION = 5         # Secondes entre deux gains XP par réaction


# ── Formule de progression ──────────────────────────────────────────────────
def niveau_depuis_xp(xp_total: int) -> tuple[int, int, int]:
    """
    Retourne (niveau, xp_dans_niveau_actuel, xp_nécessaire_pour_prochain).
    Formule : chaque palier coûte 100 × n^1.5 XP  (courbe progressive).
    """
    niveau = 0
    xp_restant = xp_total
    while True:
        seuil = int(100 * ((niveau + 1) ** 1.5))
        if xp_restant < seuil:
            return niveau, xp_restant, seuil
        xp_restant -= seuil
        niveau += 1


# ── Paliers de rôles ────────────────────────────────────────────────────────
# Les noms doivent correspondre EXACTEMENT aux rôles créés sur ton serveur
ROLE_PALIERS: dict[int, str] = {
    5:  "🌱 Novice",
    10: "⚡ Initié",
    20: "🔥 Confirmé",
    35: "💎 Élite",
    50: "👑 Légende",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  DÉFINITION DES MISSIONS
#
#  Champs :
#    id            – identifiant unique snake_case
#    nom           – affiché une fois débloquée
#    description   – affiché une fois débloquée
#    hint          – affiché AVANT débloquage pour les missions secrètes
#    type          – condition de déclenchement (voir _check_missions)
#    valeur        – seuil ou paramètre selon le type
#    xp            – récompense XP
#    credits       – récompense crédits (economy)
#    secret        – True = masquée sous "❓" jusqu'au déclenchement
#    niveau_requis – niveau minimum pour être éligible (0 = dès le début)
#    journaliere   – True = cooldown 24h, répétable chaque jour
# ═══════════════════════════════════════════════════════════════════════════════

MISSIONS: list[dict] = [

    # ── Missions permanentes visibles ─────────────────────────────────────────
    {
        "id": "premier_pas",
        "nom": "🐣 Premier Pas",
        "description": "Envoie ton tout premier message sur le serveur.",
        "hint": "Commence à parler...",
        "type": "messages_total",
        "valeur": 1,
        "xp": 50,
        "credits": 100,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "bavard",
        "nom": "💬 Bavard",
        "description": "Envoie 100 messages au total.",
        "hint": "Continue de discuter...",
        "type": "messages_total",
        "valeur": 100,
        "xp": 200,
        "credits": 300,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "discours",
        "nom": "📢 Grand Discours",
        "description": "Envoie 500 messages au total.",
        "hint": "",
        "type": "messages_total",
        "valeur": 500,
        "xp": 500,
        "credits": 750,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "reacteur",
        "nom": "😂 Réacteur en Série",
        "description": "Réagis à 50 messages avec des emojis.",
        "hint": "Les emojis, c'est la vie...",
        "type": "reactions_donnees",
        "valeur": 50,
        "xp": 150,
        "credits": 200,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "vocal_debutant",
        "nom": "🎙️ Première Voix",
        "description": "Passe 30 minutes en vocal.",
        "hint": "Ta voix compte aussi...",
        "type": "minutes_vocal",
        "valeur": 30,
        "xp": 100,
        "credits": 150,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "vocal_veteran",
        "nom": "🎧 Vétéran Vocal",
        "description": "Passe 5 heures en vocal au total.",
        "hint": "",
        "type": "minutes_vocal",
        "valeur": 300,
        "xp": 400,
        "credits": 600,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": False,
    },

    # ── Missions permanentes secrètes ─────────────────────────────────────────
    {
        "id": "noctambule",
        "nom": "🌙 Noctambule",
        "description": "Envoie un message entre 2h et 4h du matin.",
        "hint": "???",
        "type": "message_heure",
        "valeur": (2, 4),
        "xp": 200,
        "credits": 500,
        "secret": True,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "pluie_emojis",
        "nom": "🌈 Pluie d'Émojis",
        "description": "Réagis à 10 messages différents d'affilée.",
        "hint": "???",
        "type": "reactions_consecutives",
        "valeur": 10,
        "xp": 300,
        "credits": 400,
        "secret": True,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "marathonien",
        "nom": "🏃 Marathonien",
        "description": "Reste connecté en vocal 2 heures d'affilée sans interruption.",
        "hint": "???",
        "type": "vocal_session_longue",
        "valeur": 120,
        "xp": 500,
        "credits": 800,
        "secret": True,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "populaire",
        "nom": "⭐ Populaire",
        "description": "Reçois 100 réactions sur tes messages.",
        "hint": "???",
        "type": "reactions_recues",
        "valeur": 100,
        "xp": 350,
        "credits": 500,
        "secret": True,
        "niveau_requis": 0,
        "journaliere": False,
    },
    {
        "id": "matinal",
        "nom": "☀️ Lève-tôt",
        "description": "Envoie un message entre 6h et 7h du matin.",
        "hint": "???",
        "type": "message_heure",
        "valeur": (6, 7),
        "xp": 150,
        "credits": 250,
        "secret": True,
        "niveau_requis": 0,
        "journaliere": False,
    },

    # ── Missions débloquées par niveau (secrètes jusqu'au palier) ────────────
    {
        "id": "initie_defis",
        "nom": "⚡ L'Épreuve de l'Initié",
        "description": "Envoie 20 messages en une seule journée.",
        "hint": "Débloquée au niveau 10...",
        "type": "messages_aujourdhui",
        "valeur": 20,
        "xp": 250,
        "credits": 400,
        "secret": True,
        "niveau_requis": 10,
        "journaliere": False,
    },
    {
        "id": "confirme_vocal",
        "nom": "🔥 Maître du Micro",
        "description": "Passe 2 heures en vocal en une seule journée.",
        "hint": "Débloquée au niveau 20...",
        "type": "minutes_vocal_aujourdhui",
        "valeur": 120,
        "xp": 450,
        "credits": 700,
        "secret": True,
        "niveau_requis": 20,
        "journaliere": False,
    },
    {
        "id": "elite_reactions",
        "nom": "💎 L'Aimé du Serveur",
        "description": "Reçois 20 réactions en une seule journée.",
        "hint": "Débloquée au niveau 35...",
        "type": "reactions_recues_aujourdhui",
        "valeur": 20,
        "xp": 600,
        "credits": 1000,
        "secret": True,
        "niveau_requis": 35,
        "journaliere": False,
    },
    {
        "id": "legende_ultime",
        "nom": "👑 La Légende Vivante",
        "description": "Atteins le niveau 50.",
        "hint": "???",
        "type": "niveau_atteint",
        "valeur": 50,
        "xp": 1000,
        "credits": 2000,
        "secret": True,
        "niveau_requis": 0,
        "journaliere": False,
    },

    # ── Missions journalières (répétables, cooldown 24h) ──────────────────────
    {
        "id": "daily_message",
        "nom": "📅 Présence Quotidienne",
        "description": "Envoie au moins 5 messages aujourd'hui.",
        "hint": "Reviens chaque jour !",
        "type": "messages_aujourdhui",
        "valeur": 5,
        "xp": 80,
        "credits": 120,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": True,
    },
    {
        "id": "daily_reaction",
        "nom": "😄 Bonne Humeur du Jour",
        "description": "Réagis à 10 messages aujourd'hui.",
        "hint": "Distribue de la bonne humeur !",
        "type": "reactions_donnees_aujourdhui",
        "valeur": 10,
        "xp": 60,
        "credits": 80,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": True,
    },
    {
        "id": "daily_vocal",
        "nom": "🎙️ Voix du Jour",
        "description": "Passe 15 minutes en vocal aujourd'hui.",
        "hint": "Ta présence vocale compte !",
        "type": "minutes_vocal_aujourdhui",
        "valeur": 15,
        "xp": 70,
        "credits": 100,
        "secret": False,
        "niveau_requis": 0,
        "journaliere": True,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
#  BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

DB_DIR  = "data"
DB_PATH = os.path.join(DB_DIR, "kinkybot.db")


@contextmanager
def _db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_levels_db():
    """Crée / migre toutes les tables du système de niveaux."""
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS levels (
                user_id                       INTEGER PRIMARY KEY,
                xp                            INTEGER NOT NULL DEFAULT 0,
                -- Stats cumulées
                messages_total                INTEGER NOT NULL DEFAULT 0,
                reactions_donnees             INTEGER NOT NULL DEFAULT 0,
                reactions_recues              INTEGER NOT NULL DEFAULT 0,
                minutes_vocal                 INTEGER NOT NULL DEFAULT 0,
                reactions_consec              INTEGER NOT NULL DEFAULT 0,
                -- Stats journalières (remises à zéro chaque jour)
                messages_jour                 INTEGER NOT NULL DEFAULT 0,
                reactions_donnees_jour        INTEGER NOT NULL DEFAULT 0,
                reactions_recues_jour         INTEGER NOT NULL DEFAULT 0,
                minutes_vocal_jour            INTEGER NOT NULL DEFAULT 0,
                date_stats_jour               TEXT    NOT NULL DEFAULT '',
                -- Cooldowns anti-spam
                last_xp_message               REAL    NOT NULL DEFAULT 0,
                last_xp_reaction              REAL    NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS missions_completees (
                user_id      INTEGER NOT NULL,
                mission_id   TEXT    NOT NULL,
                completed_at TEXT    NOT NULL,
                PRIMARY KEY (user_id, mission_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS missions_journalieres (
                user_id      INTEGER NOT NULL,
                mission_id   TEXT    NOT NULL,
                last_done    TEXT    NOT NULL,
                PRIMARY KEY (user_id, mission_id)
            )
        """)
    print("  ✅ Table(s) [levels] prêtes.")


# ── Helpers stats ─────────────────────────────────────────────────────────────

def _get_or_create(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM levels WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        conn.execute("INSERT INTO levels (user_id) VALUES (?)", (user_id,))
        row = conn.execute(
            "SELECT * FROM levels WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row


def _reset_jour_si_besoin(conn: sqlite3.Connection, user_id: int, row: sqlite3.Row):
    """Remet les compteurs journaliers à zéro si la date a changé."""
    today = str(date.today())
    if row["date_stats_jour"] != today:
        conn.execute("""
            UPDATE levels
            SET messages_jour           = 0,
                reactions_donnees_jour  = 0,
                reactions_recues_jour   = 0,
                minutes_vocal_jour      = 0,
                date_stats_jour         = ?
            WHERE user_id = ?
        """, (today, user_id))


def get_level_data(user_id: int) -> dict:
    with _db() as conn:
        row = _get_or_create(conn, user_id)
        _reset_jour_si_besoin(conn, user_id, row)
        row = conn.execute(
            "SELECT * FROM levels WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row)


def add_xp(
    user_id: int,
    xp: int,
    stat: str | None = None,
    stat_val: int = 1,
    stat_jour: str | None = None,
) -> tuple[int, int, int, int]:
    """
    Ajoute de l'XP, incrémente une stat globale et/ou journalière.
    Retourne (ancien_niveau, nouveau_niveau, xp_total, xp_ajouté).
    """
    with _db() as conn:
        row = _get_or_create(conn, user_id)
        _reset_jour_si_besoin(conn, user_id, row)

        old_xp     = row["xp"]
        new_xp     = old_xp + xp
        old_niveau, _, _ = niveau_depuis_xp(old_xp)
        new_niveau, _, _ = niveau_depuis_xp(new_xp)

        sets: list[str] = ["xp = ?"]
        vals: list      = [new_xp]

        if stat:
            sets.append(f"{stat} = {stat} + ?")
            vals.append(stat_val)
        if stat_jour:
            sets.append(f"{stat_jour} = {stat_jour} + ?")
            vals.append(stat_val)

        vals.append(user_id)
        conn.execute(
            f"UPDATE levels SET {', '.join(sets)} WHERE user_id = ?", vals
        )
        return old_niveau, new_niveau, new_xp, xp


def update_cooldown(user_id: int, champ: str):
    with _db() as conn:
        conn.execute(
            f"UPDATE levels SET {champ} = ? WHERE user_id = ?",
            (time.time(), user_id)
        )


def get_cooldown(user_id: int, champ: str) -> float:
    with _db() as conn:
        row = _get_or_create(conn, user_id)
        return float(row[champ])


# ── Helpers missions ──────────────────────────────────────────────────────────

def get_completed_missions(user_id: int) -> list[str]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT mission_id FROM missions_completees WHERE user_id = ?",
            (user_id,)
        ).fetchall()
    return [r["mission_id"] for r in rows]


def complete_mission_permanente(user_id: int, mission_id: str):
    with _db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO missions_completees
               (user_id, mission_id, completed_at) VALUES (?, ?, ?)""",
            (user_id, mission_id, str(datetime.now()))
        )


def mission_journaliere_faite(user_id: int, mission_id: str) -> bool:
    today = str(date.today())
    with _db() as conn:
        row = conn.execute(
            "SELECT last_done FROM missions_journalieres WHERE user_id = ? AND mission_id = ?",
            (user_id, mission_id)
        ).fetchone()
    return row is not None and row["last_done"] == today


def marquer_mission_journaliere(user_id: int, mission_id: str):
    today = str(date.today())
    with _db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO missions_journalieres
               (user_id, mission_id, last_done) VALUES (?, ?, ?)""",
            (user_id, mission_id, today)
        )


def get_leaderboard_xp(limit: int = 10) -> list[tuple[int, int]]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT user_id, xp FROM levels ORDER BY xp DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [(r["user_id"], r["xp"]) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
#  COG PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class Levels(commands.Cog):
    """Système de niveaux — XP, missions, rôles, crédits."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # user_id → timestamp d'entrée en vocal (pour session longue)
        self._vocal_sessions: dict[int, float] = {}
        self._vocal_task = bot.loop.create_task(self._vocal_tick_loop())
        init_levels_db()

    def cog_unload(self):
        self._vocal_task.cancel()

    # ─────────────────────────────────────────────────────────────────────────
    #  HELPERS INTERNES
    # ─────────────────────────────────────────────────────────────────────────

    def _salon_levelup(self) -> discord.TextChannel | None:
        salon_id = get_config("salon_levelup")
        if salon_id:
            return self.bot.get_channel(int(salon_id))
        return None

    async def _dm(self, membre: discord.Member, embed: discord.Embed):
        """DM silencieux si désactivés par le membre."""
        try:
            await membre.send(embed=embed)
        except discord.Forbidden:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    #  LEVEL-UP
    # ─────────────────────────────────────────────────────────────────────────

    async def _notifier_levelup(
        self,
        membre: discord.Member,
        ancien_niveau: int,
        nouveau_niveau: int,
        fallback: discord.abc.Messageable | None = None,
    ):
        """
        1. Attribue les rôles de palier.
        2. Donne les crédits de bonus (niveau × 10 💶).
        3. Annonce publiquement dans le salon dédié (ou fallback).
        4. Envoie un DM obligatoire au joueur.
        """
        if nouveau_niveau <= ancien_niveau:
            return

        # ── 1. Rôles ─────────────────────────────────────────────────────
        roles_gagnes: list[str] = []
        for palier, nom_role in ROLE_PALIERS.items():
            if ancien_niveau < palier <= nouveau_niveau:
                role = discord.utils.get(membre.guild.roles, name=nom_role)
                if role:
                    try:
                        await membre.add_roles(role, reason=f"Niveau {palier} atteint")
                        roles_gagnes.append(nom_role)
                    except discord.Forbidden:
                        pass

        # ── 2. Crédits bonus ─────────────────────────────────────────────
        bonus = nouveau_niveau * 10
        try:
            economy_update(membre.id, wallet_diff=bonus)
        except Exception:
            pass

        # ── 3. Annonce publique ──────────────────────────────────────────
        embed_pub = discord.Embed(
            title="🎉 Level Up !",
            description=f"**{membre.mention}** passe au **niveau {nouveau_niveau}** ! 🚀",
            color=0xF1C40F,
        )
        embed_pub.set_thumbnail(url=membre.display_avatar.url)
        embed_pub.add_field(
            name="💰 Bonus de niveau",
            value=f"+**{bonus} 💶** crédits",
            inline=True,
        )
        for nom_role in roles_gagnes:
            embed_pub.add_field(
                name="🎖️ Rôle débloqué !",
                value=f"**{nom_role}**",
                inline=True,
            )

        salon = self._salon_levelup() or fallback
        if salon:
            try:
                await salon.send(embed=embed_pub)
            except (discord.Forbidden, AttributeError):
                pass

        # ── 4. DM obligatoire ────────────────────────────────────────────
        embed_dm = discord.Embed(
            title=f"🎉 Niveau {nouveau_niveau} atteint !",
            description="Continue comme ça sur le serveur ! 💪",
            color=0xF1C40F,
        )
        embed_dm.add_field(
            name="💰 Bonus reçu",
            value=f"+**{bonus} 💶** crédits dans ton portefeuille",
            inline=False,
        )
        for nom_role in roles_gagnes:
            embed_dm.add_field(
                name="🎖️ Nouveau rôle",
                value=f"**{nom_role}**",
                inline=False,
            )
        await self._dm(membre, embed_dm)

    # ─────────────────────────────────────────────────────────────────────────
    #  MISSIONS
    # ─────────────────────────────────────────────────────────────────────────

    async def _declencher_mission(
        self,
        membre: discord.Member,
        mission: dict,
        channel: discord.abc.Messageable | None,
    ):
        """Récompense + notification publique + DM obligatoire."""
        # Marquage
        if mission["journaliere"]:
            marquer_mission_journaliere(membre.id, mission["id"])
        else:
            complete_mission_permanente(membre.id, mission["id"])

        # XP + crédits
        old_niv, new_niv, _, _ = add_xp(membre.id, mission["xp"])
        try:
            economy_update(membre.id, wallet_diff=mission["credits"])
        except Exception:
            pass

        # ── Embeds ───────────────────────────────────────────────────────
        if mission["journaliere"]:
            titre = "📅 Mission Journalière Accomplie !"
            couleur = 0x2ECC71
        elif mission["secret"]:
            titre = "🔎 Mission Secrète Débloquée !"
            couleur = 0xE91E63
        else:
            titre = "🏆 Mission Accomplie !"
            couleur = 0x9B59B6

        embed_pub = discord.Embed(title=titre, color=couleur)
        embed_pub.add_field(name=mission["nom"], value=mission["description"], inline=False)
        embed_pub.add_field(
            name="🎁 Récompenses",
            value=f"+**{mission['xp']} XP** · +**{mission['credits']} 💶**",
            inline=False,
        )
        embed_pub.set_footer(text=f"Félicitations {membre.display_name} !")

        embed_dm = discord.Embed(
            title=f"✅ {mission['nom']}",
            description=mission["description"],
            color=couleur,
        )
        embed_dm.add_field(
            name="🎁 Récompenses reçues",
            value=f"+**{mission['xp']} XP** · +**{mission['credits']} 💶** dans ton portefeuille",
            inline=False,
        )
        if mission["journaliere"]:
            embed_dm.set_footer(text="Mission journalière — reviens demain !")
        else:
            embed_dm.set_footer(text="Mission permanente accomplie 🏆")

        # ── Envoi ────────────────────────────────────────────────────────
        salon = self._salon_levelup() or channel
        if salon:
            try:
                await salon.send(content=membre.mention, embed=embed_pub)
            except (discord.Forbidden, AttributeError):
                pass

        # DM obligatoire
        await self._dm(membre, embed_dm)

        # Level-up déclenché par les XP de la mission
        if new_niv > old_niv:
            await self._notifier_levelup(membre, old_niv, new_niv, channel)

    async def _check_missions(
        self,
        membre: discord.Member,
        data: dict,
        channel: discord.abc.Messageable | None = None,
        contexte: str | None = None,
    ):
        """Vérifie toutes les missions et déclenche celles accomplies."""
        completees = get_completed_missions(membre.id)
        niv, _, _  = niveau_depuis_xp(data["xp"])

        for mission in MISSIONS:
            mid = mission["id"]

            # Niveau requis non atteint → skip silencieux
            if niv < mission["niveau_requis"]:
                continue

            # Permanente déjà faite → skip
            if not mission["journaliere"] and mid in completees:
                continue

            # Journalière déjà faite aujourd'hui → skip
            if mission["journaliere"] and mission_journaliere_faite(membre.id, mid):
                continue

            # ── Évaluation ───────────────────────────────────────────────
            accomplie = False
            mtype = mission["type"]
            mval  = mission["valeur"]

            if mtype == "messages_total" and data["messages_total"] >= mval:
                accomplie = True
            elif mtype == "reactions_donnees" and data["reactions_donnees"] >= mval:
                accomplie = True
            elif mtype == "reactions_recues" and data["reactions_recues"] >= mval:
                accomplie = True
            elif mtype == "minutes_vocal" and data["minutes_vocal"] >= mval:
                accomplie = True
            elif mtype == "reactions_consecutives" and data["reactions_consec"] >= mval:
                accomplie = True
            elif mtype == "niveau_atteint" and niv >= mval:
                accomplie = True
            elif mtype == "message_heure" and contexte == "message":
                h_min, h_max = mval
                if h_min <= datetime.now().hour < h_max:
                    accomplie = True
            elif mtype == "messages_aujourdhui" and data["messages_jour"] >= mval:
                accomplie = True
            elif mtype == "reactions_donnees_aujourdhui" and data["reactions_donnees_jour"] >= mval:
                accomplie = True
            elif mtype == "reactions_recues_aujourdhui" and data["reactions_recues_jour"] >= mval:
                accomplie = True
            elif mtype == "minutes_vocal_aujourdhui" and data["minutes_vocal_jour"] >= mval:
                accomplie = True

            if accomplie:
                await self._declencher_mission(membre, mission, channel)

    # ─────────────────────────────────────────────────────────────────────────
    #  BOUCLE VOCALE
    # ─────────────────────────────────────────────────────────────────────────

    async def _vocal_tick_loop(self):
        """Distribue l'XP vocale toutes les VOCAL_INTERVAL secondes."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(VOCAL_INTERVAL)
            now = time.time()

            for guild in self.bot.guilds:
                for vc in guild.voice_channels:
                    for membre in vc.members:
                        if membre.bot:
                            continue
                        # Pas d'XP si sourd (canal AFK ou sourdine serveur)
                        if membre.voice and (membre.voice.self_deaf or membre.voice.deaf):
                            continue

                        min_tick = VOCAL_INTERVAL // 60
                        old_niv, new_niv, _, _ = add_xp(
                            membre.id,
                            XP_VOCAL_TICK,
                            stat="minutes_vocal",
                            stat_val=min_tick,
                            stat_jour="minutes_vocal_jour",
                        )
                        data = get_level_data(membre.id)

                        # Mission marathonien : session ininterrompue >= 2h
                        ts = self._vocal_sessions.get(membre.id)
                        if ts and (now - ts) / 60 >= 120:
                            if "marathonien" not in get_completed_missions(membre.id):
                                m = next(x for x in MISSIONS if x["id"] == "marathonien")
                                await self._declencher_mission(membre, m, None)

                        if new_niv > old_niv:
                            await self._notifier_levelup(
                                membre, old_niv, new_niv, self._salon_levelup()
                            )

                        await self._check_missions(membre, data)

    # ─────────────────────────────────────────────────────────────────────────
    #  LISTENERS
    # ─────────────────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        now     = time.time()

        if now - get_cooldown(user_id, "last_xp_message") < COOLDOWN_MESSAGE:
            return

        xp_gagne = random.randint(*XP_MESSAGE)
        old_niv, new_niv, _, _ = add_xp(
            user_id, xp_gagne,
            stat="messages_total",
            stat_jour="messages_jour",
        )
        update_cooldown(user_id, "last_xp_message")
        data = get_level_data(user_id)

        if new_niv > old_niv:
            await self._notifier_levelup(
                message.author, old_niv, new_niv, message.channel
            )

        await self._check_missions(
            message.author, data,
            channel=message.channel,
            contexte="message",
        )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot or not reaction.message.guild:
            return

        now = time.time()

        # ── Celui qui réagit ─────────────────────────────────────────────
        if now - get_cooldown(user.id, "last_xp_reaction") >= COOLDOWN_REACTION:
            old_niv, new_niv, _, _ = add_xp(
                user.id, XP_REACTION_GIVE,
                stat="reactions_donnees",
                stat_jour="reactions_donnees_jour",
            )
            with _db() as conn:
                conn.execute(
                    "UPDATE levels SET reactions_consec = reactions_consec + 1 WHERE user_id = ?",
                    (user.id,)
                )
            update_cooldown(user.id, "last_xp_reaction")
            data   = get_level_data(user.id)
            membre = reaction.message.guild.get_member(user.id)
            if membre:
                if new_niv > old_niv:
                    await self._notifier_levelup(
                        membre, old_niv, new_niv, reaction.message.channel
                    )
                await self._check_missions(membre, data, reaction.message.channel)

        # ── L'auteur du message ──────────────────────────────────────────
        author = reaction.message.author
        if author.bot or author.id == user.id:
            return

        add_xp(
            author.id, XP_REACTION_GET,
            stat="reactions_recues",
            stat_jour="reactions_recues_jour",
        )
        data_author   = get_level_data(author.id)
        membre_author = reaction.message.guild.get_member(author.id)
        if membre_author:
            await self._check_missions(
                membre_author, data_author, reaction.message.channel
            )

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return
        if before.channel is None and after.channel is not None:
            self._vocal_sessions[member.id] = time.time()
        elif before.channel is not None and after.channel is None:
            self._vocal_sessions.pop(member.id, None)

    # ─────────────────────────────────────────────────────────────────────────
    #  COMMANDES SLASH
    # ─────────────────────────────────────────────────────────────────────────

    @app_commands.command(name="niveau", description="Voir ton niveau et ton XP")
    @app_commands.describe(membre="Un autre membre (optionnel)")
    async def niveau(self, interaction: discord.Interaction, membre: discord.Member = None):
        await interaction.response.defer()
        cible = membre or interaction.user
        data  = get_level_data(cible.id)

        niv, xp_dans_niv, xp_prochain = niveau_depuis_xp(data["xp"])
        filled = int((xp_dans_niv / xp_prochain) * 20) if xp_prochain else 20
        barre  = "█" * filled + "░" * (20 - filled)

        prochain_role = next(
            ((p, n) for p, n in sorted(ROLE_PALIERS.items()) if p > niv),
            None,
        )

        embed = discord.Embed(title=f"📊 Profil de {cible.display_name}", color=0x3498DB)
        embed.set_thumbnail(url=cible.display_avatar.url)
        embed.add_field(name="🏅 Niveau",            value=f"**{niv}**",          inline=True)
        embed.add_field(name="✨ XP Total",           value=f"**{data['xp']}**",   inline=True)
        embed.add_field(name="​",                     value="​",                   inline=True)
        embed.add_field(
            name=f"📈 Vers niveau {niv + 1}",
            value=f"`{barre}` {xp_dans_niv} / {xp_prochain} XP",
            inline=False,
        )
        embed.add_field(name="💬 Messages",           value=str(data["messages_total"]),    inline=True)
        embed.add_field(name="😀 Réactions données",  value=str(data["reactions_donnees"]), inline=True)
        embed.add_field(name="⭐ Réactions reçues",   value=str(data["reactions_recues"]),  inline=True)
        embed.add_field(name="🎙️ Minutes en vocal",   value=str(data["minutes_vocal"]),     inline=True)

        if prochain_role:
            embed.add_field(
                name="🎖️ Prochain rôle",
                value=f"**{prochain_role[1]}** au niveau **{prochain_role[0]}**",
                inline=False,
            )

        nb_ok   = len(get_completed_missions(cible.id))
        nb_perm = len([m for m in MISSIONS if not m["journaliere"]])
        embed.add_field(
            name="🏆 Missions permanentes",
            value=f"**{nb_ok}** / {nb_perm} accomplies",
            inline=False,
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="classement_xp", description="Top 10 des membres les plus expérimentés")
    async def classement_xp(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rows  = get_leaderboard_xp(10)
        embed = discord.Embed(title="🏆 Classement XP", color=0xF1C40F)

        if not rows:
            embed.description = "Personne n'a encore gagné d'XP."
            return await interaction.followup.send(embed=embed)

        medailles = ["🥇", "🥈", "🥉"]
        lignes = []
        for i, (uid, xp) in enumerate(rows, start=1):
            u = self.bot.get_user(uid)
            if u is None:
                try:
                    u = await self.bot.fetch_user(uid)
                except Exception:
                    u = None
            nom      = u.display_name if u else f"ID:{uid}"
            niv, _,_ = niveau_depuis_xp(xp)
            prefix   = medailles[i - 1] if i <= 3 else f"**{i}.**"
            lignes.append(f"{prefix} {nom} — Niv. {niv} · {xp} XP")

        embed.description = "\n".join(lignes)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="missions", description="Voir tes missions et leur progression")
    async def missions_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data       = get_level_data(interaction.user.id)
        completees = get_completed_missions(interaction.user.id)
        niv, _, _  = niveau_depuis_xp(data["xp"])
        uid        = interaction.user.id

        embed = discord.Embed(
            title="📋 Tes Missions",
            description=(
                "Accomplis des missions pour gagner XP et crédits !\n"
                "Les missions 🔒 se débloquent en montant de niveau.\n"
                "Les missions 📅 se renouvellent chaque jour à minuit."
            ),
            color=0x9B59B6,
        )

        def barre(actuel: int, total: int) -> str:
            pct    = min(actuel / total, 1) if total else 0
            filled = int(pct * 10)
            return f"`{'█' * filled}{'░' * (10 - filled)}` {min(actuel, total)}/{total}"

        stat_map = {
            "messages_total":               data["messages_total"],
            "reactions_donnees":            data["reactions_donnees"],
            "reactions_recues":             data["reactions_recues"],
            "minutes_vocal":                data["minutes_vocal"],
            "messages_aujourdhui":          data["messages_jour"],
            "reactions_donnees_aujourdhui": data["reactions_donnees_jour"],
            "reactions_recues_aujourdhui":  data["reactions_recues_jour"],
            "minutes_vocal_aujourdhui":     data["minutes_vocal_jour"],
        }

        sections = [
            ("📌 Missions Principales",
             [m for m in MISSIONS if not m["secret"] and not m["journaliere"]]),
            ("📅 Missions Journalières",
             [m for m in MISSIONS if m["journaliere"]]),
            ("🔎 Missions Secrètes & Niveaux",
             [m for m in MISSIONS if m["secret"] and not m["journaliere"]]),
        ]

        for titre_sec, liste in sections:
            if not liste:
                continue
            embed.add_field(name=titre_sec, value="​", inline=False)

            for m in liste:
                mid = m["id"]

                # ── Niveau requis non atteint ─────────────────────────
                if niv < m["niveau_requis"]:
                    embed.add_field(
                        name="🔒 Mission verrouillée",
                        value=(
                            f"*{m['hint']}*\n"
                            f"🔓 Accessible au niveau **{m['niveau_requis']}** "
                            f"_(encore {m['niveau_requis'] - niv} niveaux)_"
                        ),
                        inline=False,
                    )
                    continue

                ok_perm  = not m["journaliere"] and mid in completees
                ok_daily = m["journaliere"] and mission_journaliere_faite(uid, mid)
                ok       = ok_perm or ok_daily

                # ── Secrète non encore débloquée ─────────────────────
                if m["secret"] and not ok:
                    embed.add_field(
                        name="❓ Mission secrète",
                        value=f"*{m['hint'] or '???'}*\n🎁 Récompense inconnue...",
                        inline=False,
                    )
                    continue

                # ── Affichage normal ──────────────────────────────────
                if ok_daily:
                    status = "🔄"  # refaite demain
                elif ok_perm:
                    status = "✅"
                else:
                    status = "⬜"

                mtype = m["type"]
                mval  = m["valeur"]
                prog  = ""
                types_sans_barre = (
                    "message_heure", "niveau_atteint",
                    "reactions_consecutives", "vocal_session_longue",
                )
                if not ok and mtype not in types_sans_barre:
                    prog = "\n" + barre(stat_map.get(mtype, 0), mval)

                refresh = "\n*↻ Disponible chaque jour à minuit*" if m["journaliere"] else ""

                embed.add_field(
                    name=f"{status} {m['nom']}",
                    value=(
                        f"{m['description']}\n"
                        f"🎁 +{m['xp']} XP · +{m['credits']} 💶"
                        f"{prog}{refresh}"
                    ),
                    inline=False,
                )

        nb_ok   = len(completees)
        nb_perm = len([m for m in MISSIONS if not m["journaliere"]])
        embed.set_footer(
            text=f"{nb_ok}/{nb_perm} missions permanentes · Niveau {niv}"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))