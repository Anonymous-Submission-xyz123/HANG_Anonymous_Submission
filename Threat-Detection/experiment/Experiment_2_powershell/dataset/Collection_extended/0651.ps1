# Natural language intent:
# Search for sensitive files in user directories and display the first 5 results.

Get-ChildItem C:\Users -Recurse -Include *.${file.sensitive.extension} -ErrorAction 'SilentlyContinue' | foreach {$_.FullName} | Select-Object -first 5; ; exit 0;
