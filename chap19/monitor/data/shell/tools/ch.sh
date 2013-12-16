#!/bin/bash
rm -rf *type
for n in `ls | grep -E "(*z$|*zip$)"`
do
    mv $n ${n##*2F}
done
