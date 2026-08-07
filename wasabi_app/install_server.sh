#!/bin/bash

apt-get update && \
  apt-get install -y python3 python3-pip nginx curl git

curl -sL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

npm install -g vite
