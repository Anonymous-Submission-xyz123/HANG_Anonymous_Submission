# Natural language intent:
# find and filter information related to processes, threads, files, keys, and process IDs (PIDs) from the output of handle64.exe. The /r option in findstr indicates that the search string is a regular expression, and /i makes the search case-insensitive

handle64.exe /a | findstr /r /i "process thread file key pid:"
