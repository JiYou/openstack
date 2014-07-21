#!/bin/bash
set -e
set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
cd $TOPDIR/../

for n in `find . -name "*" | grep -v object | grep -v ".py"`; do

    cnt=`ls -l $n | head -1 | grep "\->" | wc -l`
    if [[ $cnt -eq 1 ]]; then
        rm -rf $n
    fi
done

set +o xtrace
