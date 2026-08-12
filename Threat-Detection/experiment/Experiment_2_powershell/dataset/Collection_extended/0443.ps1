# Natural language intent:
# Set environment variables and run PowerShell with a delay using the Start-Sleep cmdlet.

$env:COR_ENABLE_PROFILING = 1 ; $env:COR_PROFILER = '${clsid_guid}' ; $env:COR_PROFILER_PATH = '${file_name}' ; POWERSHELL -c 'Start-Sleep 1'
