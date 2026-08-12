# Natural language intent:
# Execute SSH command to retrieve user identity information.

Invoke-SSHCommand -ip 192.168.1.100 -Username root -Password test -Command 'id'
