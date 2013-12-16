#!/usr/bin/expect -f

set run_user [lindex $argv 0]
set password [lindex $argv 1]

spawn adduser $run_user
expect {
"assword:*" {send "$password\r";exp_continue}
"assword:*" {send "$password\r";exp_continue}
"Full Name*" {send "\r";exp_continue}
"Room Number*" {send "\r";exp_continue}
"Work Phone*" {send "\r";exp_continue}
"Home Phone*" {send "\r";exp_continue}
"Other*" {send "\r";exp_continue}
"correct?*" {send "Y\r"}
}

expect eof

