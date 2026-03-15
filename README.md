# 🤖 KinkyBot

> **Bot Discord complet en Python** — Économie · Casino · GIFs · Modération · Réactions automatiques · Accueil · Jeux de soirée · Configuration dynamique

---

## ✨ Fonctionnalités

### 💰 Économie (`cogs/economy.py`)
Système de monnaie virtuelle (💶) complet avec portefeuille et banque séparés.

| Commande | Description |
|----------|-------------|
| `/solde` | Consulter ton solde (portefeuille + banque) |
| `/quotidien` | Récupérer ton bonus quotidien de **500 💶** |
| `/travail` | Travailler pour gagner entre **70 et 200 💶** |
| `/depot <montant\|all>` | Déposer de l'argent en banque |
| `/retrait <montant\|all>` | Retirer de l'argent de la banque |
| `/classement` | Top 10 des joueurs les plus riches |

---

### 🎰 Casino (`cogs/casino.py`)
Tente ta chance et multiplie tes gains !

| Commande | Description | Multiplicateur |
|----------|-------------|---------------|
| `/roulette <couleur> <mise>` | Parie sur `rouge` ou `noir` | x2 |
| `/roulette vert <mise>` | Parie sur le `vert` (risqué !) | x35 |
| `/machine_a_sous <mise>` | 3 symboles identiques = jackpot | x5 / x10 💎 |

**Symboles de la machine à sous :** 🍒 🍋 🍊 ⭐ 💎 7️⃣
- Trois identiques → **x5** (x10 sur 💎💎💎)
- Deux identiques → **x2**

---

### 🖼️ GIFs (`cogs/gifs.py`, propulsé par Giphy)
Exprime-toi avec des GIFs animés !

**Recherche libre :**
| Commande | Description |
|----------|-------------|
| `/gif <recherche>` | Rechercher n'importe quel GIF |
| `/gif_random` | Obtenir un GIF complètement aléatoire |

**Actions sociales :**
| Commande | Description |
|----------|-------------|
| `/câlin <membre>` | Envoyer un câlin à quelqu'un 🤗 |
| `/bisou <membre>` | Envoyer un bisou à quelqu'un 😘 |
| `/gifle <membre>` | Gifler quelqu'un 👋 |
| `/pat <membre>` | Faire un pat à quelqu'un 🤚 |
| `/bravo [membre]` | Applaudir quelqu'un 👏 |
| `/pleurer` | Exprimer ta tristesse 😢 |
| `/danse` | Danser ! 💃 |
| `/facepalm` | Exprimer ton désespoir 🤦 |

---

### 🛡️ Modération (`cogs/moderation.py`)
Garde ton serveur propre avec des outils puissants.

**Commandes manuelles :**
| Commande | Permission requise |
|----------|--------------------|
| `/expulser <membre> [raison]` | Kick Members |
| `/bannir <membre> [raison]` | Ban Members |
| `/debannir <user_id>` | Ban Members |
| `/muet <membre> [minutes]` | Moderate Members |
| `/nettoyer <nombre>` | Manage Messages (max 100) |

**Auto-modération incluse :**
- 🚫 **Filtre de mots bannis** — liste configurable dans `cogs/moderation.py`
- 🔔 **Anti-mention spam** — suppression automatique au-delà de 5 mentions simultanées
- ✅ Les modérateurs (permission `Manage Messages`) sont exemptés

---

### 💬 Réactions automatiques (`cogs/reactions.py`)
Le bot réagit intelligemment aux messages des membres.

**Réponses texte automatiques :**
| Mot-clé détecté | Exemple de réponse |
|-----------------|-------------------|
| `bonjour` | "Salut ! 👋", "Hey, ça va ? 😄" |
| `bonsoir` | "Bonsoir ! 🌙" |
| `merci` | "De rien ! 😊", "Avec plaisir !" |
| `gg` | "GG ! 🎉", "Champion 🏆" |
| `bonne nuit` | "Dors bien ! 💤" |
| `help` | Rappel des commandes slash |

**Emojis ajoutés automatiquement :**
`incroyable` → 🤯 · `lol` / `haha` → 😂 · `triste` → 😢 · `gg` → 🎉 · `love` → ❤️

---

### 👋 Accueil (`cogs/accueil.py`)
Message de bienvenue automatique envoyé lors de l'arrivée d'un nouveau membre, avec les étapes à suivre (présentation, règlement, validation staff).

> ⚙️ Configure l'ID du salon de bienvenue directement dans `cogs/accueil.py` :
> ```python
> self.ID_SALON_BIENVENUE = 123456789012345678
> ```

---

### 🎭 Jeux de soirée (`cogs/playparty.py`)

#### 🎯 Le Jeu du Fakir
Lance une session interactive pour un membre avec révélation progressive par boutons.

| Commande | Description |
|----------|-------------|
| `/fakir <cible> [gage]` | Lancer une partie du Fakir pour un membre |

- Révèle successivement : **intensité**, **objet**, **zone**, puis optionnellement un **gage bonus**
- Objets possibles : Cravache, Paddle, Martinet, Fouet, Badine
- Zones : Pieds, Fesses, Dos, Cuisses, Poitrine
- Intensités : 10, 25, 50, 75, 100
- Couleur de l'embed adaptée dynamiquement selon l'intensité

#### 🎡 La Roue
Lance une roue animée avec suspense et conséquences réelles.

| Commande | Description |
|----------|-------------|
| `/roue` | Faire tourner une roue et découvrir ton destin |

- **🍀 Roue de la Chance** — Récompenses en crédits ou bonus roleplay
- **🔥 Roue du Courage** — Mute automatique, perte de crédits, défi artistique

> Les mutes sont appliqués automatiquement via l'API Discord (timeout). Le bot doit avoir la permission **Moderate Members**.

---

### 🖼️ Fils automatiques (`cogs/fils_auto.py`)
Dans les salons configurés comme "salons photo" :
- Crée automatiquement un **fil de discussion** sous chaque image postée
- Supprime les messages texte seuls (avec avertissement)
- Les membres avec la permission `Manage Messages` sont exemptés

> Les salons photo se configurent via le **Panneau de Configuration** (`/panneau_config`).

---

### ⚙️ Configuration dynamique (`cogs/config.py`)
Interface graphique de configuration sans modifier le code.

| Commande | Permission requise |
|----------|--------------------|
| `/panneau_config` | Administrator |

Permet de configurer via menus déroulants :
- 📸 **Salons Photo** — Choix des salons où les fils automatiques sont actifs (jusqu'à 3)
- 💬 **Réactions** — Gestion des mots-clés de réaction *(à venir)*
- 👋 **Accueil** — Changement du salon de bienvenue *(à venir)*

---

### 🗄️ Export de la base de données (`cogs/exportBDD.py`)

| Commande | Permission requise |
|----------|--------------------|
| `/export_bdd` | Propriétaire du serveur uniquement |

- Envoie le fichier `.sqlite` directement en DM ou dans le salon
- Si la base dépasse **24 Mo**, elle est automatiquement compressée en `.zip` avant envoi

---

### 📖 Général (`cogs/general.py`)

| Commande | Description |
|----------|-------------|
| `/aide` | Affiche toutes les commandes disponibles, classées par module (généré dynamiquement) |

---

## 🚀 Installation

### Prérequis
- Python **3.10+**
- Un bot Discord avec les intents **Message Content** et **Members** activés dans le portail développeur

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/LaserOnWood/KinkyBot.git
cd KinkyBot

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Ajouter ton token Discord
echo "TON_TOKEN_ICI" > token.txt

# 4. (Optionnel) Ajouter ta clé API Giphy pour les GIFs
echo "TA_CLE_GIPHY" > giphy_key.txt

# 5. Lancer le bot
python main.py
```

### Synchroniser les commandes slash
Une fois le bot en ligne, envoie dans un salon Discord :
```
!synchro
```

---

## 📁 Structure du projet

```
KinkyBot/
├── main.py              # Point d'entrée — chargement des cogs
├── token.txt            # Token Discord (ne pas commit !)
├── giphy_key.txt        # Clé API Giphy (optionnel)
├── Dockerfile           # Image Docker pour le déploiement
├── requirements.txt     # Dépendances Python
├── cogs/
│   ├── general.py       # Commande /aide dynamique
│   ├── economy.py       # Économie : solde, daily, travail, dépôt, retrait, classement
│   ├── casino.py        # Roulette & Machine à sous
│   ├── gifs.py          # GIFs via API Giphy
│   ├── reactions.py     # Réactions automatiques aux messages
│   ├── moderation.py    # Modération manuelle & auto-modération
│   ├── accueil.py       # Message de bienvenue automatique
│   ├── fils_auto.py     # Fils de discussion automatiques sous les images
│   ├── playparty.py     # Jeux de soirée : Le Fakir & La Roue
│   ├── config.py        # Panneau de configuration dynamique
│   └── exportBDD.py     # Export de la base de données SQLite
└── utils/
    └── database.py      # Fonctions SQLite partagées (get, update, leaderboard, config)
```

---

## 🗄️ Base de données

Le bot utilise **SQLite** via `utils/database.py`. La base est créée automatiquement dans `/app/data/economy.db` (chemin Docker) au premier lancement.

**Table `economy` :**
| Colonne | Type | Description |
|---------|------|-------------|
| `user_id` | INTEGER | Identifiant Discord de l'utilisateur |
| `wallet` | INTEGER | Argent en portefeuille (défaut : 100 💶) |
| `bank` | INTEGER | Argent en banque (défaut : 0) |
| `last_daily` | TEXT | Date du dernier bonus quotidien |

**Table `config` :**
| Colonne | Type | Description |
|---------|------|-------------|
| `cle` | TEXT | Clé de configuration (ex: `salons_photo`) |
| `valeur` | TEXT | Valeur associée |

**Table `custom_reactions` :**
| Colonne | Type | Description |
|---------|------|-------------|
| `mot` | TEXT | Mot-clé déclencheur |
| `reponse` | TEXT | Réponse associée |

---

## ⚙️ Configuration

### Clé API Giphy (`cogs/gifs.py`)
La clé peut être fournie de trois façons (par ordre de priorité) :
1. Variable d'environnement `GIPHY_API_KEY`
2. Fichier `giphy_key.txt` à la racine
3. Clé publique de test (limitée, développement uniquement)

### Ajouter des mots bannis (`cogs/moderation.py`)
```python
BANNED_WORDS: list[str] = [
    "motinterdit1",
    "motinterdit2",
]
```

### Modifier les réactions automatiques (`cogs/reactions.py`)
```python
TRIGGERS: dict[str, list[str]] = {
    "bonjour": ["Salut ! 👋", "Hey ! 😄"],
    # Ajoute tes propres mots-clés ici
}
```

### Déploiement Docker
Le projet inclut un `Dockerfile` prêt à l'emploi :
```bash
docker build -t kinkybot .
docker run -e DISCORD_TOKEN=ton_token kinkybot
```

> Le token peut aussi être injecté via la variable d'environnement `DISCORD_TOKEN` (prioritaire sur `token.txt`).

---

## 🔧 Commandes d'administration (propriétaire uniquement)

| Commande | Description |
|----------|-------------|
| `!synchro` | Synchronise toutes les commandes slash avec Discord et affiche un rapport par module |
| `!recharger <module\|tout>` | Recharge un ou tous les modules sans redémarrer le bot |
| `!relancer` | Redémarre complètement le processus du bot |

```bash
# Exemples
!recharger economy
!recharger casino
!recharger tout
```

---

## 📜 Licence

Projet open-source — libre d'utilisation et de modification.

---

<p align="center">Fait avec ❤️ et <a href="https://discordpy.readthedocs.io/">discord.py</a> • <a href="https://github.com/LaserOnWood/KinkyBot">LaserOnWood/KinkyBot</a></p>
