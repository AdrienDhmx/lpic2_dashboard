#!/bin/bash
sudo apt update
sudo apt install chrony

sudo bash -c 'cat > /etc/chrony/chrony.conf' <<EOF
pool 0.debian.pool.ntp.org iburst
pool 1.debian.pool.ntp.org iburst
pool 2.debian.pool.ntp.org iburst
pool 3.debian.pool.ntp.org iburst
allow 10.141.112.0/24
EOF

sudo systemctl restart chrony
sudo systemctl enable chrony
