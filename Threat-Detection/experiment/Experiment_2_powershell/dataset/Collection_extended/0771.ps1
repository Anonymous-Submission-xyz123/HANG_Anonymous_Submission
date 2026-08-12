# Natural language intent:
# Environment Variable Obfuscation, Stores a command in an environment variable and then executes it, which can help hide the command from casual observation and some security tools.

$env:PSVariable = 'Get-Process'; Invoke-Expression $env:PSVariable
