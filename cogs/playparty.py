import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

from utils.database import get_data, update_db

# --- Configuration des lancers ---
INTENSITES = [10, 25, 50, 75, 100]

OBJETS = ["Cravache", "Paddle", "Martinet", "Fouet", "Badine"]

ZONES = ["Pieds", "Fesses", "Dos", "Cuisses", "Poitrine"]

GAGES = [
    "Faire 10 pompes",
    "Chanter une chanson pendant 30 secondes",
    "Imiter un animal pendant 1 minute",
    "Raconter un secret",
    "Faire une déclaration d'amour dramatique",
    "Danser seul pendant 1 minute",
    "Parler avec un accent étranger pendant 5 minutes",
    "Appeler quelqu'un et lui dire qu'il te manque",
    "Manger quelque chose sans les mains",
    "Faire le tour de la pièce en marchant comme un pingouin",
    "Dire un compliment à chaque personne présente",
    "Faire semblant d'être un robot pendant 3 minutes",
    "Réciter l'alphabet à l'envers",
    "Faire 20 sauts étoiles",
    "Parler sans utiliser la lettre 'e' pendant 2 minutes",
]

# --- Couleurs par intensité ---
def couleur_intensite(intensite: int) -> int:
    if intensite <= 10:
        return 0x2ECC71   # Vert
    elif intensite <= 25:
        return 0x3498DB   # Bleu
    elif intensite <= 50:
        return 0xF39C12   # Orange
    elif intensite <= 75:
        return 0xE67E22   # Orange foncé
    else:
        return 0xE74C3C   # Rouge


# --- Vue avec boutons pour le suspense ---
class FakirView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, cible: discord.Member, avec_gage: bool):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.cible = cible
        self.avec_gage = avec_gage

        # Pré-tirage de tous les résultats
        self.intensite = random.choice(INTENSITES)
        self.objet = random.choice(OBJETS)
        self.zone = random.choice(ZONES)
        self.gage = random.choice(GAGES) if avec_gage else None

        # État d'avancement
        self.etape = 0  # 0 = début, 1 = intensité, 2 = objet, 3 = zone, 4 = gage (optionnel)

    def _embed_base(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎯 Le Jeu du Fakir",
            color=0x9B59B6
        )
        embed.set_footer(text=f"Initié par {self.interaction.user.display_name} pour {self.cible.display_name}")
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = self._embed_base()

        if self.etape == 0:
            embed.description = (
                f"🎮 Une partie du Fakir commence pour **{self.cible.display_name}** !\n\n"
                "Appuie sur **Lancer** pour révéler l'intensité."
            )

        elif self.etape == 1:
            embed.color = couleur_intensite(self.intensite)
            embed.description = f"🎲 **Intensité révélée !**"
            embed.add_field(name="⚡ Intensité", value=f"**{self.intensite}**", inline=False)
            embed.add_field(name="⏳ Suivant", value="Appuie sur **Lancer** pour révéler l'objet.", inline=False)

        elif self.etape == 2:
            embed.color = couleur_intensite(self.intensite)
            embed.description = f"🎲 **Objet révélé !**"
            embed.add_field(name="⚡ Intensité", value=f"**{self.intensite}**", inline=True)
            embed.add_field(name="🪄 Objet", value=f"**{self.objet}**", inline=True)
            embed.add_field(name="⏳ Suivant", value="Appuie sur **Lancer** pour révéler la zone.", inline=False)

        elif self.etape == 3:
            embed.color = couleur_intensite(self.intensite)
            embed.description = f"🎯 **Résultat final pour {self.cible.display_name} !**"
            embed.add_field(name="⚡ Intensité", value=f"**{self.intensite}**", inline=True)
            embed.add_field(name="🪄 Objet", value=f"**{self.objet}**", inline=True)
            embed.add_field(name="📍 Zone", value=f"**{self.zone}**", inline=True)

            if self.avec_gage:
                embed.add_field(name="⏳ Suivant", value="Appuie sur **Lancer** pour révéler le gage bonus !", inline=False)
            else:
                embed.add_field(
                    name="🏁 Partie terminée",
                    value=f"**{self.intensite} coups** de **{self.objet}** sur les **{self.zone}** !",
                    inline=False
                )
                self._disable_all()

        elif self.etape == 4:
            embed.color = couleur_intensite(self.intensite)
            embed.description = f"🎯 **Résultat complet pour {self.cible.display_name} !**"
            embed.add_field(name="⚡ Intensité", value=f"**{self.intensite}**", inline=True)
            embed.add_field(name="🪄 Objet", value=f"**{self.objet}**", inline=True)
            embed.add_field(name="📍 Zone", value=f"**{self.zone}**", inline=True)
            embed.add_field(name="🎭 Gage Bonus", value=f"**{self.gage}**", inline=False)
            embed.add_field(
                name="🏁 Partie terminée",
                value=f"**{self.intensite} coups** de **{self.objet}** sur les **{self.zone}** + le gage !",
                inline=False
            )
            self._disable_all()

        await interaction.response.edit_message(embed=embed, view=self)

    def _disable_all(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🎲 Lancer", style=discord.ButtonStyle.primary)
    async def lancer(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.etape += 1
        await self.update_message(interaction)

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.danger)
    async def annuler(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎯 Le Jeu du Fakir",
            description="❌ La partie a été annulée.",
            color=0x95A5A6
        )
        self._disable_all()
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        self._disable_all()
        try:
            await self.interaction.edit_original_response(view=self)
        except Exception:
            pass


class PlayParty(commands.Cog):
    """Jeux de soirée : Le Fakir, La Roue et plus à venir."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="roue", description="Faire tourner une roue et découvrir ton destin !")
    async def roue(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎡 La Roue",
            description=(
                "Choisis une roue dans le menu ci-dessous, puis lance-la !\n\n"
                "🍀 **Roue de la Chance** — Des récompenses t'attendent peut-être...\n"
                "🔥 **Roue du Courage** — Pour les téméraires seulement !"
            ),
            color=0x9B59B6,
        )
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}")
        view = RoueSelectView(interaction, self.bot)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="fakir", description="Lancer une partie du jeu du Fakir pour un membre")
    @app_commands.describe(
        cible="La personne qui joue",
        gage="Ajouter un lancer de gage bonus ? (optionnel)"
    )
    async def fakir(
        self,
        interaction: discord.Interaction,
        cible: discord.Member,
        gage: bool = False
    ):
        view = FakirView(interaction, cible, gage)
        embed = discord.Embed(
            title="🎯 Le Jeu du Fakir",
            description=(
                f"🎮 Une partie du Fakir commence pour **{cible.display_name}** !\n\n"
                "Appuie sur **Lancer** pour révéler l'intensité."
            ),
            color=0x9B59B6
        )
        embed.set_footer(text=f"Initié par {interaction.user.display_name} pour {cible.display_name}")
        await interaction.response.send_message(embed=embed, view=view)


# ------------------------------------------------------------------ #
#  CONFIGURATION DES ROUES
# ------------------------------------------------------------------ #

ROUES: dict[str, dict] = {
    "roue_chance": {
        "label": "🍀 Roue de la Chance",
        "description": "Tente ta chance et vois ce que le destin te réserve !",
        "couleur": 0x2ECC71,
        "cases": [
            {
                "label": "💰 500 crédits offerts !",
                "action": "credits",
                "valeur": 500,
            },
            {
                "label": "🪙 50 crédits offerts !",
                "action": "credits",
                "valeur": 50,
            },
            {
                "label": "🗳️ Vote x2 au prochain sondage !",
                "action": "roleplay",
                "valeur": "Tu bénéficies d'un **vote x2** au prochain sondage du serveur ! Annonce-le quand il sera lancé.",
            },
        ],
    },
    "roue_courage": {
        "label": "🔥 Roue du Courage",
        "description": "Tu es courageux ? Prouve-le en acceptant ce que la roue décide !",
        "couleur": 0xE74C3C,
        "cases": [
            {
                "label": "🎨 Défi artistique !",
                "action": "artistique",
                "valeur": None,  # membre aléatoire sera choisi au moment du tirage
            },
            {
                "label": "🔇 Muet pendant 1 heure !",
                "action": "mute",
                "valeur": 60,
            },
            {
                "label": "🔇 Muet pendant 30 minutes !",
                "action": "mute",
                "valeur": 30,
            },
            {
                "label": "💸 Perd 500 crédits !",
                "action": "credits",
                "valeur": -500,
            },
        ],
    },
}

# Messages d'animation pour le suspense
ANIMATION_FRAMES = [
    "🎡 La roue tourne...",
    "🎡 La roue tourne... ⠋",
    "🎡 Elle tourne encore...",
    "🎡 Elle tourne encore... ⠙",
    "🎡 Ça ralentit...",
    "🎡 Ça ralentit... ⠹",
    "🎡 Encore un peu...",
    "🎡 Presque... 🤞",
]


# ------------------------------------------------------------------ #
#  VUE : SÉLECTION DE LA ROUE
# ------------------------------------------------------------------ #

class RoueSelectView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, bot: commands.Bot):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.bot = bot
        self.roue_choisie = None

        # Construire le menu déroulant dynamiquement
        options = [
            discord.SelectOption(
                label=data["label"],
                value=key,
                description=data["description"],
            )
            for key, data in ROUES.items()
        ]

        select = discord.ui.Select(
            placeholder="Choisis une roue...",
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        self.roue_choisie = interaction.data["values"][0]
        roue = ROUES[self.roue_choisie]

        # Mise à jour de l'embed avec la roue choisie
        embed = discord.Embed(
            title="🎡 La Roue",
            description=(
                f"Tu as choisi **{roue['label']}**\n\n"
                f"_{roue['description']}_\n\n"
                "Prêt ? Clique sur **Lancer la roue** !"
            ),
            color=roue["couleur"],
        )
        embed.set_footer(text=f"Demandé par {self.interaction.user.display_name}")

        # Remplacer la vue par les boutons de confirmation
        confirm_view = RoueConfirmView(self.interaction, self.bot, self.roue_choisie)
        await interaction.response.edit_message(embed=embed, view=confirm_view)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except Exception:
            pass


# ------------------------------------------------------------------ #
#  VUE : CONFIRMATION ET LANCEMENT
# ------------------------------------------------------------------ #

class RoueConfirmView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, bot: commands.Bot, roue_key: str):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.bot = bot
        self.roue_key = roue_key

    @discord.ui.button(label="🎡 Lancer la roue !", style=discord.ButtonStyle.success)
    async def lancer(self, interaction: discord.Interaction, button: discord.ui.Button):
        roue = ROUES[self.roue_key]

        # Désactiver les boutons pendant l'animation
        for item in self.children:
            item.disabled = True

        # Tirage du résultat
        case = random.choice(roue["cases"])

        # --- Première réponse obligatoire ---
        embed = discord.Embed(
            title=f"{roue['label']}",
            description=ANIMATION_FRAMES[0],
            color=roue["couleur"],
        )
        embed.set_footer(text=f"Demandé par {self.interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=self)

        # --- Animation suspense via edit_original_response ---
        for frame in ANIMATION_FRAMES[1:]:
            await asyncio.sleep(0.8)
            embed.description = frame
            await interaction.edit_original_response(embed=embed, view=self)

        await asyncio.sleep(1)

        # --- Résultat final ---
        resultat_texte, erreur = await appliquer_action(
            case, self.interaction.user, self.bot, interaction.guild
        )

        embed_final = discord.Embed(
            title=f"🎉 {roue['label']} — Résultat !",
            description=f"**{case['label']}**\n\n{resultat_texte}",
            color=roue["couleur"],
        )
        embed_final.set_footer(text=f"Demandé par {self.interaction.user.display_name}")

        if erreur:
            embed_final.add_field(name="⚠️ Note", value=erreur, inline=False)

        await interaction.edit_original_response(embed=embed_final, view=None)

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.danger)
    async def annuler(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎡 La Roue",
            description="❌ La roue a été annulée.",
            color=0x95A5A6,
        )
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except Exception:
            pass


# ------------------------------------------------------------------ #
#  HELPER : appliquer l'action de la case
# ------------------------------------------------------------------ #

async def appliquer_action(
    case: dict,
    user: discord.Member,
    bot: commands.Bot,
    guild: discord.Guild,
) -> tuple[str, str | None]:
    """Applique l'effet de la case et retourne (texte_resultat, erreur_optionnelle)."""

    action = case["action"]
    valeur = case["valeur"]
    erreur = None

    if action == "credits":
        wallet, bank, _ = get_data(user.id)
        if valeur < 0 and wallet < abs(valeur):
            # Pas assez dans le wallet, on vide juste
            perte_reelle = wallet
            update_db(user.id, wallet_diff=-perte_reelle)
            texte = f"💸 Tu perds **{perte_reelle} 🪙** (tout ton portefeuille, tu n'en avais pas assez)."
        else:
            update_db(user.id, wallet_diff=valeur)
            if valeur > 0:
                texte = f"💰 **{valeur} 🪙** ont été ajoutés à ton portefeuille !"
            else:
                texte = f"💸 **{abs(valeur)} 🪙** ont été retirés de ton portefeuille."

    elif action == "roleplay":
        texte = str(valeur)

    elif action == "artistique":
        # Choisir un membre aléatoire du serveur (hors bots)
        membres = [m for m in guild.members if not m.bot and m.id != user.id]
        if membres:
            cible = random.choice(membres)
            texte = (
                f"🎨 Tu dois créer quelque chose d'artistique pour **{cible.mention}** !\n"
                "Dessin, poème, musique... à toi de choisir. Bonne chance ! 🖌️"
            )
        else:
            texte = "🎨 Tu dois créer quelque chose d'artistique... mais personne d'autre n'est sur le serveur !"

    elif action == "mute":
        from datetime import timedelta
        try:
            until = discord.utils.utcnow() + timedelta(minutes=valeur)
            await user.timeout(until, reason="Roue du Courage — résultat automatique")
            texte = f"🔇 Tu es muet pendant **{valeur} minute(s)** ! Bonne chance... 😈"
        except discord.Forbidden:
            texte = f"🔇 Tu devais être muet {valeur} minute(s)... mais le bot n'a pas les permissions nécessaires."
            erreur = "Le bot manque de permissions pour appliquer le timeout."
        except Exception as e:
            texte = f"🔇 Résultat : muet {valeur} minute(s)."
            erreur = f"Erreur lors du mute : {e}"

    else:
        texte = "Résultat inconnu."

    return texte, erreur


async def setup(bot: commands.Bot):
    await bot.add_cog(PlayParty(bot))
