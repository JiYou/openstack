#!/usr/bin/expect -f

set remote_ip [lindex $argv 0]
set password [lindex $argv 1]
set command [lindex $argv 2]
set timeout -1

spawn ssh root@${remote_ip} $command
expect {
"(yes/no)?" {send "yes\r";exp_continue}
"assword:*" {send "$password\r"}
}

expect eof

