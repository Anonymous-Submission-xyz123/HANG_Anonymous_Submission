# Natural language intent:
# PowerShell command is to create a new PowerShell session (New-PSSession) named "PSC" on the remote computer with the specified name "the.computer.name," and then enter that session (Enter-PSSession). This allows the user to interact with the remote computer using PowerShell commands within the created session. It's important to note that you need the necessary permissions and authentication to establish a remote PowerShell session on the specified computer.

New-PSSession -Name PSC -ComputerName the.computer.name; Enter-PSSession PSC
