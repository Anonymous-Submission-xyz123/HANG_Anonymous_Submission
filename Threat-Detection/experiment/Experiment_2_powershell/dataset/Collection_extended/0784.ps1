# Natural language intent:
# Get specific info of current domain controller

Get-DomainController | select Forest , Domain , IPAddress , Name , OSVersion | fl
