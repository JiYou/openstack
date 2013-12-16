#!/bin/bash

if [[ $# -eq 1 ]]; then
    git config --global user.name "JiYou"
    git config --global user.email "jiyou09@gmail.com"
    git remote rm origin
    git remote add origin git@github.com:JiYou/openstack.git
    tsocks git add .
    tsocks git commit -asm "\"$@\""
    tsocks git push origin
else
    echo "Useage: ./update.sh commit_msg"
fi
