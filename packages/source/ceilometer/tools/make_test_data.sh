#!/bin/bash

bindir=$(dirname $0)

project_name="$1"
if [ -z "$project_name" ]
then
    project_name=demo
fi

if [ -z "$OS_USERNAME" ]
then
    user=demo
else
    user=$OS_USERNAME
fi

# Convert a possible project name to an id, if we have
# keystone installed.
if which keystone >/dev/null
then
    project=$(keystone tenant-list | grep " $project_name " | cut -f2 -d'|' | cut -f2 -d' ')
else
    # Assume they gave us the project id as argument.
    project="$project_name"
fi

if [ -z "$project" ]
then
    echo "Could not determine project id for \"$project_name\"" 1>&2
    exit 1
fi

early1="2012-08-27T07:00:00"
early2="2012-08-27T17:00:00"

start="2012-08-28T00:00:00"

middle1="2012-08-28T08:00:00"
middle2="2012-08-28T18:00:00"
middle3="2012-08-29T09:00:00"
middle4="2012-08-29T19:00:00"

end="2012-08-31T23:59:00"

late1="2012-08-31T10:00:00"
late2="2012-08-31T20:00:00"

mkdata() {
  ${bindir}/make_test_data.py --project "$project" \
    --user "$user" --start "$2" --end "$3" \
    "$1" instance:m1.tiny 1
}

dates=(early1 early2 start middle1 middle2 middle3 middle4 end late1 late2)

echo $project

for i in $(seq 0 $((${#dates[@]} - 2)) )
do

  iname=${dates[$i]}
  eval "ivalue=\$$iname"

  for j in $(seq $((i + 1)) $((${#dates[@]} - 1)) )
  do
    jname=${dates[$j]}
    eval "jvalue=\$$jname"

    resource_id="${project_name}-$iname-$jname"
    echo "$resource_id"

    mkdata "$resource_id" "$ivalue" "$jvalue"
    [ $? -eq 0 ] || exit $?
  done
  echo
done
