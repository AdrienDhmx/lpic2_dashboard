#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
  echo "❌ Ce script doit être exécuté en tant que root." >&2
  exit 1
fi

echo "🚀 Démarrage de la configuration de sécurité PAM..."

AUTH_FILE="/etc/pam.d/common-auth"
ACCOUNT_FILE="/etc/pam.d/common-account"

cp "$AUTH_FILE" "${AUTH_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "[+] Sauvegarde créée : ${AUTH_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

cat > "$AUTH_FILE" << 'EOF'
# Configuration PAM pour l'authentification avec faillock
auth required pam_faillock.so preauth silent deny=3 unlock_time=600
auth [success=2 default=ignore] pam_unix.so nullok
auth optional pam_exec.so /home/matteo/Bureau/TPFinal/postfix/event.sh Failed Login A failed login attempt has occurred
auth [default=die] pam_faillock.so authfail deny=3 unlock_time=600
auth sufficient pam_faillock.so authsucc deny=3 unlock_time=600
EOF

echo "[+] Configuration pam_faillock et pam_exec appliquée à $AUTH_FILE."

if ! grep -q "pam_faillock.so" "$ACCOUNT_FILE"; then
    sed -i '1i account required pam_faillock.so' "$ACCOUNT_FILE"
    echo "[+] pam_faillock ajouté à $ACCOUNT_FILE."
else
    echo "[=] pam_faillock semble déjà configuré dans $ACCOUNT_FILE."
fi

LOGIN_FILE="/etc/pam.d/login"
TIME_CONF_FILE="/etc/security/time.conf"

echo "[*] Configuration des restrictions horaires de connexion..."

if ! grep -vE '^\s*#' "$LOGIN_FILE" | grep -q "pam_time.so"; then
    echo "account [success=1 default=ignore] pam_succeed_if.so user = root" >> "$LOGIN_FILE"
    echo "account requisite pam_time.so" >> "$LOGIN_FILE"
    echo "[+] Module pam_time.so (avec exception root) ajouté à $LOGIN_FILE."
else
    echo "[=] pam_time.so semble déjà configuré dans $LOGIN_FILE."
fi


TIME_RULE_ROOT="*;*;root;Al0000-2400"
TIME_RULE="*;*;*;Wk0800-1800"
if ! grep -Fxq "$TIME_RULE" "$TIME_CONF_FILE"; then
    echo "# Règle ajoutée par le script de sécurité PAM" > "$TIME_CONF_FILE"
    echo "# Autorise root à se connecter à tout moment" >> "$TIME_CONF_FILE"
    echo "$TIME_RULE_ROOT" >> "$TIME_CONF_FILE"
    echo "# Interdit les connexions en dehors des heures de travail (Lundi-Vendredi, 8h-18h)" >> "$TIME_CONF_FILE"
    echo "$TIME_RULE" >> "$TIME_CONF_FILE"
    echo "[+] Plage horaire de connexion configurée dans $TIME_CONF_FILE."
else
    echo "[=] La règle de restriction horaire semble déjà exister dans $TIME_CONF_FILE."
fi

COMMON_PASS_FILE="/etc/pam.d/common-password"

echo "[*] Installation et configuration de la politique de mot de passe..."

apt-get update > /dev/null
apt-get install -y libpam-pwquality

PWQUALITY_LINE="password requisite pam_pwquality.so retry=3 minlen=12 dcredit=-1 ucredit=-1 lcredit=-1 ocredit=-1 reject_username"

if grep -q "pam_pwquality.so" "$COMMON_PASS_FILE"; then
    sed -i "s/.*pam_pwquality.so.*/$PWQUALITY_LINE/" "$COMMON_PASS_FILE"
    echo "[+] Règle pam_pwquality mise à jour dans $COMMON_PASS_FILE."
else
    sed -i "/password.*pam_unix.so/i $PWQUALITY_LINE" "$COMMON_PASS_FILE"
    echo "[+] Règle pam_pwquality ajoutée à $COMMON_PASS_FILE."
fi

LOGIN_DEFS_FILE="/etc/login.defs"
echo "[*] Configuration de l'expiration des mots de passe dans $LOGIN_DEFS_FILE..."

sed -i -E "s/^PASS_MAX_DAYS.*/PASS_MAX_DAYS\t90/" "$LOGIN_DEFS_FILE"
sed -i -E "s/^PASS_MIN_DAYS.*/PASS_MIN_DAYS\t1/" "$LOGIN_DEFS_FILE"
sed -i -E "s/^PASS_WARN_AGE.*/PASS_WARN_AGE\t7/" "$LOGIN_DEFS_FILE"

echo "[+] Politique d'expiration appliquée pour les futurs utilisateurs."
echo "[!] Note : Pour appliquer aux utilisateurs existants, utilisez :"
echo "[!] for user in \$(getent passwd | awk -F: '\$3>=1000{print \$1}'); do chage -M 90 -m 1 -W 7 \$user; done"

echo "✅ Configuration PAM de sécurité terminée."