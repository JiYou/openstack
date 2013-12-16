#!/bin/sh
# this is rather stupid script is needed as testr init
# complains if there is already a repo.
if [ -d nova_tests/.testrepository ]
then
    exit 0
fi
testr init -d nova_tests
