import discord
from discord import app_commands
from discord.ext import commands
from utils.database import set_config, get_config, set_reaction, delete_reaction, get_all_reactions

class ConfigPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panneau_config", description="Ouvrir le panneau de configuration du bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def panneau_config(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚙️ Panneau de Configuration",
            description="Choisissez une catégorie à configurer via le menu déroulant ci-dessous.",
            color=discord.Color.blue()
        )
        
        salon_photo_actuel = get_config("salons_photo", "Aucun")
        salon_accueil_actuel = get_config("salon_accueil", "Aucun")
        salon_pres_actuel = get_config("salon_presentation", "Aucun")
        salon_regle_actuel = get_config("salon_reglement", "Aucun")
        
        embed.add_field(name="📸 Salons Photo", value=f"ID(s) : {salon_photo_actuel}", inline=True)
        embed.add_field(name="👋 Salon Accueil", value=f"ID : {salon_accueil_actuel}", inline=True)
        embed.add_field(name="📝 Salon Présentation", value=f"ID : {salon_pres_actuel}", inline=True)
        embed.add_field(name="📜 Salon Règlement", value=f"ID : {salon_regle_actuel}", inline=True)

        view = ConfigMainView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class AddReactionModal(discord.ui.Modal, title="Ajouter une Réaction"):
    mot = discord.ui.TextInput(
        label="Mot-clé (déclencheur)",
        placeholder="Ex: bisous",
        min_length=1,
        max_length=50
    )
    reponse = discord.ui.TextInput(
        label="Réponse du bot",
        style=discord.TextStyle.paragraph,
        placeholder="Ex: Moi aussi je t'aime !",
        min_length=1,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        mot_str = self.mot.value.lower().strip()
        set_reaction(mot_str, self.reponse.value)
        await interaction.response.send_message(f"✅ Réaction ajoutée avec succès pour le mot **{mot_str}** !", ephemeral=True)

class DeleteReactionModal(discord.ui.Modal, title="Supprimer une Réaction"):
    mot = discord.ui.TextInput(
        label="Mot-clé à supprimer",
        placeholder="Ex: bisous",
        min_length=1,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        mot_str = self.mot.value.lower().strip()
        delete_reaction(mot_str)
        await interaction.response.send_message(f"🗑️ Réaction supprimée pour le mot **{mot_str}** (si elle existait).", ephemeral=True)

class ReactionConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ajouter / Modifier", style=discord.ButtonStyle.success, emoji="➕")
    async def add_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddReactionModal())

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def del_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DeleteReactionModal())

    @discord.ui.button(label="Voir la liste", style=discord.ButtonStyle.secondary, emoji="📋")
    async def list_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        reactions = get_all_reactions()
        if not reactions:
            return await interaction.response.send_message("Aucune réaction configurée pour le moment.", ephemeral=True)
            
        desc = ""
        for mot, reponse in reactions.items():
            rep_courte = reponse[:40] + ("..." if len(reponse) > 40 else "")
            desc += f"• **{mot}** ➡️ {rep_courte}\n"
            
        embed = discord.Embed(title="📋 Liste des réactions personnalisées", description=desc, color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ConfigMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Que souhaitez-vous configurer ?",
        options=[
            discord.SelectOption(label="Salons Photo", value="photos", emoji="📸", description="Gérer les fils automatiques"),
            discord.SelectOption(label="Accueil", value="accueil", emoji="👋", description="Changer le salon de bienvenue"),
            discord.SelectOption(label="Présentation", value="presentation", emoji="📝", description="Changer le salon de présentation"),
            discord.SelectOption(label="Règlement", value="reglement", emoji="📜", description="Changer le salon du règlement"),
            discord.SelectOption(label="Réactions", value="reactions", emoji="💬", description="Ajouter/Supprimer des réactions")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0]
        
        if val == "photos":
            channel_select = discord.ui.ChannelSelect(
                placeholder="Sélectionnez les salons photo...",
                channel_types=[discord.ChannelType.text],
                min_values=1,
                max_values=3
            )

            async def channel_callback(inter: discord.Interaction):
                ids = ",".join([str(c.id) for c in channel_select.values])
                set_config("salons_photo", ids)
                mentions = ", ".join([c.mention for c in channel_select.values])
                await inter.response.send_message(f"✅ Salons photo mis à jour : {mentions}", ephemeral=True)

            channel_select.callback = channel_callback
            new_view = discord.ui.View()
            new_view.add_item(channel_select)
            embed = discord.Embed(title="📸 Configuration - Salons Photo", description="Sélectionnez les salons dans le menu ci-dessous.", color=discord.Color.green())
            await interaction.response.edit_message(embed=embed, view=new_view)

        elif val in ["accueil", "presentation", "reglement"]:
            cle_config = f"salon_{val}"
            label = val.capitalize()
            
            channel_select = discord.ui.ChannelSelect(
                placeholder=f"Sélectionnez le salon de {val}...",
                channel_types=[discord.ChannelType.text],
                min_values=1,
                max_values=1
            )

            async def channel_callback(inter: discord.Interaction):
                c_id = str(channel_select.values[0].id)
                set_config(cle_config, c_id)
                await inter.response.send_message(f"✅ Salon de **{label}** mis à jour : {channel_select.values[0].mention}", ephemeral=True)

            channel_select.callback = channel_callback
            new_view = discord.ui.View()
            new_view.add_item(channel_select)
            embed = discord.Embed(title=f"⚙️ Configuration - Salon {label}", description=f"Sélectionnez le salon de {val} dans le menu ci-dessous.", color=discord.Color.green())
            await interaction.response.edit_message(embed=embed, view=new_view)

        elif val == "reactions":
            view = ReactionConfigView()
            embed = discord.Embed(title="💬 Configuration - Réactions Personnalisées", description="Utilisez les boutons ci-dessous pour gérer les réponses automatiques du bot.", color=discord.Color.green())
            await interaction.response.edit_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(ConfigPanel(bot))
