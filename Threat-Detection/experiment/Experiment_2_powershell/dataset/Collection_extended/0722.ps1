# Natural language intent:
# Starting the Mozilla Maintenance Service Next, we can replace this file with a malicious `maintenanceservice.exe`, start the maintenance service, and get command execution as SYSTEM.

sc.exe start MozillaMaintenance
