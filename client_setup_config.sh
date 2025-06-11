#!/bin/bash

read -p "Veuillez entrer l'adresse IP du serveur NTP : " ntp_server_ip

echo "Installation et configuration de Chrony..."
sudo apt install -y chrony

sudo sed -i "/^server.*iburst$/d" /etc/chrony/chrony.conf
echo "pool $ntp_server_ip iburst prefer" | sudo tee -a /etc/chrony/chrony.conf
sudo systemctl restart chrony

echo "Vérification de la synchronisation NTP..."
chronyc sources -v

echo "Installation et configuration de Postfix..."
sudo apt install -y postfix

sudo debconf-set-selections <<< "postfix postfix/mailname string `hostname`"


if ! grep -q "smtp_use_tls = yes" /etc/postfix/main.cf; then
    read -p "Veuillez entrer votre adresse email Gmail : " gmail_address
    read -s -p "Veuillez entrer votre mot de passe Gmail : " gmail_password
    echo
    sudo sed -i "/^relayhost.*/d" /etc/postfix/main.cf
    echo "relayhost = [smtp.gmail.com]:587" | sudo tee -a /etc/postfix/main.cf
    echo "smtp_use_tls = yes
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt" | sudo tee -a /etc/postfix/main.cf
    echo "[smtp.gmail.com]:587 $gmail_address:$gmail_password" | sudo tee /etc/postfix/sasl_passwd
    sudo chmod 600 /etc/postfix/sasl_passwd
    sudo postmap /etc/postfix/sasl_passwd
    sudo systemctl restart postfix
fi

echo "Configuration du fuseau horaire..."
sudo dpkg-reconfigure tzdata

echo "Vérification de l'heure système..."
date
timedatectl

echo "Configuration terminée."
