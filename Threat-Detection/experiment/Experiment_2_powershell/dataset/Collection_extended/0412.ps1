# Natural language intent:
# Set a registry value using PowerShell.

Set-ItemProperty HKLM:\SYSTEM\CurrentControlSet\Services\WinSock2\Parameters -Name AutodialDLL -Value PathToAtomicsFolder\T1546\bin\AltWinSock2DLL.dll
