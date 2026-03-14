import discord
from discord import app_commands
from discord.ext import commands
import random

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
    """Jeux de soirée : Le Fakir et plus à venir."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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


async def setup(bot: commands.Bot):
    await bot.add_cog(PlayParty(bot))
