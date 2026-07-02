#!/bin/bash -e

apt-get update
apt-get install -y sshpass openssh-client netcat curl expect telnet
pip install -r requirements.txt
