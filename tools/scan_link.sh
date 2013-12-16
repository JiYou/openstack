#!/bin/bash
set -e
set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
cd $TOPDIR/../

echo "#!/bin/bash" > $TOPDIR/create_link.sh
echo "set -e" >> $TOPDIR/create_link.sh
echo "set -o xtrace" >> $TOPDIR/create_link.sh


for n in `find . -name "*"`; do

    cnt=`ls -l $n | head -1 | grep "\->" | wc -l`
    if [[ $cnt -eq 1 ]]; then
        source_file=`ls -l $n | awk '{print $11}'`
        link_file=`ls -l $n | awk '{print $9}'`
        d_path=`dirname $link_file`
        echo $n >> /tmp/log
        echo $d_path >> /tmp/log
        file=$TOPDIR/create_link.sh

        echo "if [[ ! -e $link_file ]]; then"   >> $file
        echo "  old_dir=\`pwd\`"                  >> $file
        echo "  cd $d_path"                     >> $file
        echo "  ln -s $source_file ${link_file##*/}"  >> $file
        echo "  cd \$old_dir"                    >> $file
        echo "fi"                               >> $file
        echo >> $file

    fi
done

echo "set +o xtrace" >> $TOPDIR/create_link.sh

set +o xtrace
