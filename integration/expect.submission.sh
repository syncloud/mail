#!/usr/bin/expect

set timeout 20
set host [lindex $argv 0]
set port [lindex $argv 1]
set user [lindex $argv 2]
set password [lindex $argv 3]
spawn telnet $host $port
expect "Postfix"
send "EHLO $host"
send "$user $password"