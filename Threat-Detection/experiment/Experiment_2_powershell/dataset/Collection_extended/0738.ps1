# Natural language intent:
# List namespaces inside "root\cimv2" with WMI

Get-WmiObject -Class "__Namespace" -Namespace "root\cimv2" -List -Recurse 2> $null | select __Namespace | sort __Namespace
