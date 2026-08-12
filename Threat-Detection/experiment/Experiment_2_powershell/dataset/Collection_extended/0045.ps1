# Natural language intent:
# Retrieve and group indexed items based on specific criteria.

Get-IndexedItem -Filter 'System.Kind = 'Music' AND AlbumArtist like '%' ' | Group-Object -NoElement -Property 'AlbumArtist' | sort -Descending -property count
