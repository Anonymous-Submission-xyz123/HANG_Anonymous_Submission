# Natural language intent:
# Retrieve information about installed antivirus products using Windows Management Instrumentation (WMI).

wmic /NAMESPACE:\root\SecurityCenter2 PATH AntiVirusProduct GET /value
