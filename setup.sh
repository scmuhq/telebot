#!/bin/bash
# Script d'installation automatique du bot sur un VPS Ubuntu
# Usage: bash setup.sh

set -e

echo "=== Installation du bot Telegram Πειραιεύς ==="

# Mise à jour système
echo "[1/6] Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installer Python 3.11+ et pip
echo "[2/6] Installation de Python..."
sudo apt install -y python3 python3-pip python3-venv git

# Créer le dossier et copier les fichiers
echo "[3/6] Création de l'environnement virtuel..."
cd /home/ubuntu/telebot
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
echo "[4/6] Installation des dépendances Python..."
pip install -r requirements.txt

# Configurer le service systemd
echo "[5/6] Configuration du service systemd..."
sudo cp telebot.service /etc/systemd/system/telebot.service
sudo systemctl daemon-reload
sudo systemctl enable telebot
sudo systemctl start telebot

echo "[6/6] Terminé !"
echo ""
echo "=== Le bot est lancé et démarrera automatiquement au reboot ==="
echo ""
echo "Commandes utiles :"
echo "  sudo systemctl status telebot    — voir le statut"
echo "  sudo systemctl restart telebot   — redémarrer"
echo "  sudo systemctl stop telebot      — arrêter"
echo "  sudo journalctl -u telebot -f    — voir les logs en direct"
