#!/bin/bash


apt-get update && \
  apt-get install -y python3 python3-pip nginx curl git

curl -sL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

npm install -g vite

cat << EOF > /etc/systemd/system/wasabi_flask.service
[Unit]
Description=wasabi flask backend server and serial server
After=network.target

[Service]
Type=simple
WorkingDirectory=$PWD
ExecStart=$PWD/start_flask_server.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > /etc/systemd/system/wasabi_vite.service
[Unit]
Description=wasabi interface server startup script
After=network.target

[Service]
Type=simple
WorkingDirectory=$PWD
ExecStart=$PWD/start_vite_server.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
