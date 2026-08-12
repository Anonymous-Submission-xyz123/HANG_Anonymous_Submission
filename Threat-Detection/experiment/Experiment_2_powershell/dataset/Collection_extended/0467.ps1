# Natural language intent:
# Copy pictures related to 'Stingray' and 'portfolio' to a specified destination using PowerShell.

Get-IndexedItem Stingray, kind=picture, keyword=portfolio | copy -destination e:\
