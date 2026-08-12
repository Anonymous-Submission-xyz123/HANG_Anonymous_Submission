# Natural language intent:
# Using PowerShell Classes for Code Hiding, Defines a custom PowerShell class to encapsulate and hide malicious code, making it harder for security tools to detect.

class HiddenCode { [string] Run() { return 'Hidden command executed' } }; $instance = [HiddenCode]::new(); $instance.Run()
