# Natural language intent:
# Get AdminSDHolders

Get-DomainObjectAcl -SearchBase 'CN=AdminSDHolder,CN=System,DC=EGOTISTICAL-BANK,DC=local' | % { $_.SecurityIdentifier } | Convert-SidToName
