#!/usr/bin/expect -f

set password [lindex $argv 0]
set source_path [lindex $argv 1]
set target_path [lindex $argv 2]
set timeout -1

spawn scp -r  $source_path ${target_path}
expect {
"(yes/no)?" {send "yes\r";exp_continue}
"assword:*" {send "$password\r"}
}

expect eof

