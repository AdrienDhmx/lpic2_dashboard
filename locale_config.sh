#!/bin/bash

sudo timedatectl set-timezone Asia/Tokyo

timedatectl

sudo apt update

sudo bash -c 'echo "de_DE.UTF-8 UTF-8" >> /etc/locale.gen'
sudo bash -c 'echo "es_ES.UTF-8 UTF-8" >> /etc/locale.gen'
sudo bash -c 'echo "it_IT.UTF-8 UTF-8" >> /etc/locale.gen'
sudo bash -c 'echo "fr_FR.UTF-8 UTF-8" >> /etc/locale.gen'
sudo bash -c 'echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen'

sudo locale-gen

locale -a
