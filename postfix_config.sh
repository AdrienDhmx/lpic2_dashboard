#!/bin/bash
sudo apt update
sudo apt install postfix

GMAIL=""
PASS=""

sudo postconf -e "relayhost = [smtp.gmail.com]:587"
sudo postconf -e "smtp_use_tls = yes"
sudo postconf -e "smtp_sasl_auth_enable = yes"
sudo postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"
sudo postconf -e "smtp_sasl_security_options = noanonymous"
sudo postconf -e "smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"

sudo bash -c 'cat > /etc/postfix/sasl_passwd' <<EOF
[smtp.gmail.com]:587 $GMAIL:$PASS
EOF

sudo postmap /etc/postfix/sasl_passwd
sudo chmod 600 /etc/postfix/sasl_passwd
sudo systemctl restart postfix

CRON_JOB="@reboot /home/matteo/Bureau/TPFinal/postfix/event.sh System Rebooted The system has been rebooted."


(crontab -l 2>/dev/null | grep -F "$CRON_JOB") || (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -


PAM_LINE="password optional pam_exec.so /home/matteo/Bureau/TPFinal/postfix/event.sh Password Changed Un utilisateur à modifier son mot de passe."
if ! grep -Fq "$PAM_LINE" /etc/pam.d/common-password; then
    echo "$PAM_LINE" | sudo tee -a /etc/pam.d/common-password > /dev/null
fi

sudo sed -i 's|auth\s\+\[success=1 default=ignore\]\s\+pam_unix\.so nullo|auth    [success=2 default=ignore]    pam_unix.so nullok|' /etc/pam.d/common-auth


PAM_AUTH_LINE="auth required pam_exec.so /home/matteo/Bureau/TPFinal/postfix/event.sh Failed Login A failed login attempt has occurred"
if ! grep -Fq "$PAM_AUTH_LINE" /etc/pam.d/common-auth; then
    echo "$PAM_AUTH_LINE" | sudo tee -a /etc/pam.d/common-auth > /dev/null
fi
echo "Test de configuration Postfix" | mail -s "Test" @gmail.com