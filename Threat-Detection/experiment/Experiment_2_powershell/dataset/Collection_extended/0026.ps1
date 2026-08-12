# Natural language intent:
# Modify PowerShell profile to add content and start a process.

Add-Content ${ps_profile} -Value "" ; Add-Content ${ps_profile} -Value "Start-Process ${exe_path}" ; powershell -Command exit
