#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
RESET='\033[0m'

set -e

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED} Ce script doit être exécuté en tant que root (essayez avec sudo).${RESET}"
  exit 1
fi

echo -e "${RESET} Configuration du transfert X11 via SSH..."

echo -e "${RESET} Installation des dépendances..."
apt-get update -qq
apt-get install -y xauth x11-utils &> /dev/null
echo -e "${GREEN} Dépendances installées.${RESET}"

SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP="/etc/ssh/sshd_config.bak"

if [ ! -f "$BACKUP" ]; then
  cp "$SSHD_CONFIG" "$BACKUP"
  echo -e "${GREEN} Sauvegarde créée : $BACKUP${RESET}"
fi

x11_forwarding=$(grep -Ei '^\s*X11Forwarding' "$SSHD_CONFIG" | tail -n1 | awk '{print $2}')
x11_display_offset=$(grep -Ei '^\s*X11DisplayOffset' "$SSHD_CONFIG" | tail -n1 | awk '{print $2}')
x11_use_localhost=$(grep -Ei '^\s*X11UseLocalhost' "$SSHD_CONFIG" | tail -n1 | awk '{print $2}')

IP=$(hostname -I | awk '{print $1}')
[ -z "$IP" ] && IP="IP_NON_DETECTÉE"

if [[ "$x11_forwarding" == "yes" && "$x11_display_offset" == "10" && "$x11_use_localhost" == "yes" ]]; then
  echo -e "${GREEN} La configuration X11 est déjà correcte. Aucune modification nécessaire.${RESET}"
  echo -e "\n${GREEN} X11 Forwarding est activé !${RESET}"
  echo -e "${RESET} Depuis votre machine cliente, connectez-vous avec :"
  echo -e "   ${GREEN}ssh -X votre_utilisateur@$IP${RESET}\n"
  exit 0
fi

echo -e "${RESET} Modification de $SSHD_CONFIG..."

sed -i 's/^#*X11Forwarding.*/X11Forwarding yes/' "$SSHD_CONFIG" || true
sed -i 's/^#*X11DisplayOffset.*/X11DisplayOffset 10/' "$SSHD_CONFIG" || true
sed -i 's/^#*X11UseLocalhost.*/X11UseLocalhost yes/' "$SSHD_CONFIG" || true

grep -q "^X11Forwarding" "$SSHD_CONFIG" || echo "X11Forwarding yes" >> "$SSHD_CONFIG"
grep -q "^X11DisplayOffset" "$SSHD_CONFIG" || echo "X11DisplayOffset 10" >> "$SSHD_CONFIG"
grep -q "^X11UseLocalhost" "$SSHD_CONFIG" || echo "X11UseLocalhost yes" >> "$SSHD_CONFIG"

echo -e "${GREEN} Paramètres X11 configurés.${RESET}"

echo -e "${RESET} Redémarrage de SSH..."
systemctl restart ssh
echo -e "${GREEN} Service SSH redémarré.${RESET}"

echo -e "\n${GREEN} X11 Forwarding est activé !${RESET}"
echo -e "${RESET} Depuis votre machine cliente, connectez-vous avec :"
echo -e "   ${GREEN}ssh -X votre_utilisateur@$IP${RESET}\n"