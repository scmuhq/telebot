# 🤖 Telegram Bot — Accès, CAPTCHA, Modération & Annonces

Bot Telegram complet regroupant :

- Onboarding contrôlé (groupe backup obligatoire)
- CAPTCHA mathématique à l'entrée
- Modération automatique (blacklist de mots)
- Commandes admin (/ban, /mute, /unmute, /warn)
- Système d'annonces en MP
- Liste de membres certifiés (/certif)

---

## 📁 Structure du projet

```
telebot/
├── bot.py                  # Point d'entrée principal
├── config.py               # Configuration (variables d'environnement)
├── database.py             # Base de données SQLite
├── .env.example            # Modèle de fichier .env
├── requirements.txt        # Dépendances Python
├── handlers/
│   ├── __init__.py
│   ├── start.py            # /start + vérification backup + lien d'invitation
│   ├── captcha.py          # CAPTCHA à l'entrée du groupe
│   ├── moderation.py       # Blacklist + /ban /mute /unmute /warn
│   ├── announce.py         # /announce — envoyer des annonces en MP
│   ├── certif.py           # /certif /addcertif /removecertif
│   └── restrictions.py     # Blocage stickers/photos/vidéos
```

---

## 🚀 Installation

### 1. Cloner / copier le projet

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer le fichier `.env`

Copier `.env.example` → `.env` et remplir les valeurs :

```bash
cp .env.example .env
```

| Variable            | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `BOT_TOKEN`         | Token obtenu via [@BotFather](https://t.me/BotFather)    |
| `MAIN_GROUP_ID`     | ID du groupe principal (nombre négatif)                  |
| `BACKUP_GROUP_ID`   | ID du groupe backup (nombre négatif)                     |
| `ADMIN_IDS`         | IDs des administrateurs, séparés par des virgules        |
| `CHANNEL_NAME`      | Nom affiché dans les messages du bot                     |
| `CAPTCHA_TIMEOUT`   | Temps en secondes pour résoudre le CAPTCHA (défaut : 60) |
| `TEMP_BAN_DURATION` | Durée du ban temporaire en secondes (défaut : 3600)      |

### 4. Lancer le bot

```bash
python bot.py
```

---

## ⚙️ Configuration Telegram requise

### Bot

1. Créer le bot via [@BotFather](https://t.me/BotFather)
2. Désactiver « Group Privacy » : BotFather → `/mybots` → Bot Settings → Group Privacy → **Turn off**
3. Ajouter le bot comme **administrateur** dans les deux groupes (principal + backup)

### Groupe principal

- Mettre le groupe en **privé** (pas de lien public)
- Ajouter le bot comme **admin** avec les permissions :
  - Supprimer des messages
  - Bannir des utilisateurs
  - Inviter des utilisateurs via des liens
  - Restreindre les membres
  - Épingler des messages

### Groupe backup

- Le bot doit être **membre** (ou admin) pour vérifier l'appartenance des utilisateurs

---

## 📋 Commandes disponibles

### Utilisateurs

| Commande  | Description                                     |
| --------- | ----------------------------------------------- |
| `/start`  | Démarrer le bot et lancer l'onboarding          |
| `/certif` | Afficher la liste du staff et membres certifiés |

### Administrateurs

| Commande            | Description                                         |
| ------------------- | --------------------------------------------------- |
| `/ban`              | Bannir un utilisateur (répondre à son message)      |
| `/mute`             | Muter un utilisateur                                |
| `/unmute`           | Démuter un utilisateur                              |
| `/warn`             | Avertir un utilisateur (3 warns = ban auto)         |
| `/announce <texte>` | Envoyer une annonce en MP à tous les utilisateurs   |
| `/addcertif <rôle>` | Ajouter un membre certifié (répondre à son message) |
| `/removecertif`     | Retirer un membre certifié (répondre à son message) |

---

## 🔧 Modifier la blacklist

Éditer le fichier `config.py`, tableau `BLACKLISTED_WORDS` :

```python
BLACKLISTED_WORDS: list[str] = [
    "cc",
    "scamma",
    "pack id",
    # Ajouter d'autres mots ici
]
```

---

## 📌 Notes

- **Annonces** : seuls les utilisateurs ayant fait `/start` dans le bot recevront les annonces (limitation Telegram).
- **CAPTCHA** : les utilisateurs ont 60 secondes par défaut. Modifier `CAPTCHA_TIMEOUT` dans `.env`.
- **Warnings** : après 3 avertissements, l'utilisateur est automatiquement banni.
- **Lien d'invitation** : dans `handlers/start.py`, remplacer `https://t.me/+BACKUP_INVITE_LINK` par le vrai lien d'invitation du groupe backup.

---

## 🔍 Obtenir les IDs Telegram

- **Bot** : créer via @BotFather, récupérer le token
- **Group ID** : ajouter [@userinfobot](https://t.me/userinfobot) ou [@getidsbot](https://t.me/getidsbot) dans le groupe, ou utiliser l'API
- **User ID** : envoyer `/start` à [@userinfobot](https://t.me/userinfobot)
