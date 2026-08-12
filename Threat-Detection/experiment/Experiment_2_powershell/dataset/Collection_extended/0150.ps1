# Natural language intent:
# Perform egress network checks to specified IP and port ranges with a delay and verbose output.

Invoke-EgressCheck -ip 1.2.3.4 -portrange '22-25,53,80,443,445,3306,3389' -protocol ALL -delay 100 -verbose
