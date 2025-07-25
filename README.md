# LPIC2 Dashboard – Projet Client/Serveur

## Objectif

Ce projet met en œuvre une architecture client-serveur sous Linux, intégrant :
- Un serveur NTP (Chrony)
- Un serveur de messagerie (Postfix)
- Une sécurité renforcée via PAM
- Une interface graphique de supervision (Tkinter)
- Le support de X11 forwarding pour accès distant

## Structure du dossier

```
lpic2_dashboard/
├── config_chrony.sh           
├── postfix_config.sh          
├── pam_config.sh              
├── locale_config.sh           
├── enable_x11_forwarding.sh   
├── event.sh                   
├── dashboard.sh               
├── main.py                    
├── utils.py                   
├── client_setup_config.sh     
├── README.md                  
```

## Prérequis

- Deux machines virtuelles Linux (une serveur, une client)
- Accès root ou sudo
- Connexion réseau entre les deux machines

## Instructions de test

### 1. Serveur Linux

#### a. Configuration NTP (Chrony)
```bash
sudo chmod +x config_chrony.sh
sudo  ./config_chrony.sh
```
- Vérifier la synchronisation :  
  `chronyc sources -v`

#### b. Configuration Postfix
```bash
sudo chmod +x postfix_config.sh 
sudo ./postfix_config.sh
```
- Renseigner l’adresse Gmail et mot de passe lors de l’exécution.
- Vérifier l’envoi de mail :  
  `echo "Test" | mail -s "Test Postfix" votre_email@gmail.com`

#### c. Configuration Fuseau Horaire et Locales
```bash
sudo chmod +x locale_config.sh
sudo ./locale_config.sh
```
- Vérifier le fuseau :  
  `date`
- Vérifier les locales :  
  `locale -a`

#### d. Sécurité PAM
```bash
sudo chmod +x pam_config.sh
sudo ./pam_config.sh
```
- Tester la limitation des connexions (tentatives, horaires).
- Changer le mot de passe pour déclencher un mail.

#### e. Activation du X11 Forwarding
```bash
sudo chmod +x enable_x11_forwarding.sh
sudo ./enable_x11_forwarding.sh
```
- Depuis le client :  
  `ssh -X utilisateur@ip_du_serveur`

#### f. Lancement du Dashboard Graphique
```bash
sudo chmod +x dashboard.sh 
sudo -E ./dashboard.sh (-E correspond à  garder l envirronement actuel)
```
- Visualiser en temps réel : heure, ressources, logs PAM/Postfix.
- Filtrer et exporter les logs (CSV/JSON).

### 2. Client Linux

```bash
sudo chmod +x client_setup_config.sh 
sudo ./client_setup_config.sh
```
- Saisir l’IP du serveur NTP.
- Saisir les identifiants Gmail pour Postfix.
- Configurer le fuseau horaire (différent du serveur).
- Vérifier la synchronisation NTP :  
  `chronyc sources -v`
- Vérifier l’envoi de mail via Postfix.

### 3. Tests PAM et Mail

- Tenter une connexion hors horaires autorisés (doit être refusée).
- Changer le mot de passe (doit déclencher un mail).
- Vérifier la réception des mails d’alerte.

### 4. Accès distant au Dashboard

- Depuis le client, lancer le dashboard graphique du serveur via SSH/X11 :
  ```bash
  ssh -X utilisateur@ip_du_serveur
  sudo -E ./dashboard.sh
  ```
- Vérifier l’affichage et l’interactivité.

