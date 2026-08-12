# Natural language intent:
# Query PnP entities to find imaging devices on the system.

Get-CimInstance -Query "SELECT * FROM Win32_PnPEntity WHERE (PNPClass = 'Img' OR PNPClass = 'Cam')"
