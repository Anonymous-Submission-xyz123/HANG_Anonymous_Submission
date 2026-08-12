# Natural language intent:
# Change directory to the temp folder and execute Kerbrute to perform user enumeration on the specified domain controller.

cd $env:temp ; .\kerbrute.exe userenum -d ${Domain} --dc ${DomainController} $env:TEMP\username.txt
