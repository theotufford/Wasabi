#!/usr/bin/env bash
if id -nG "$USER" | grep -qw "sudo" ; then
  echo 'need root permissions! re run with "sudo bash install.sh"'
else

  pkgStrings = ["npm", "python"]

  hasNpm= dpkg -l | grep npm 
  if ! hasNpm ; then
    sudo apt install nodejs npm -y
  else
    echo "npm verified"
  fi


## serial logic to be conf"igured 
fi
