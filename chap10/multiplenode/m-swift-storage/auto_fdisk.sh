#!/usr/bin/expect -f
spawn fdisk /dev/vdb
expect "Command (m for help):"
send "n\r"

expect "Select*:"
send "p\r"

expect "Partition number*:"
send "\r"

expect "First sector*:"
send "\r"

expect "Last sector, +sectors or +size*:"
send "\r"

expect "Command (m for help):"
send "w\r"

expect eof
