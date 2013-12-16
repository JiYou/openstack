#!/usr/bin/expect -f

set run_user [lindex $argv 0]

spawn su $run_user -c "ssh-keygen -t rsa"
expect {
"id_rsa*" {send "\r";exp_continue}
"passphrase*" {send "\r";exp_continue}
"again:" {send "\r";}
}


