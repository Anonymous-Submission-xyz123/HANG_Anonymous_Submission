# Natural language intent:
# Define a syntax list, iterate through it, and execute SharpView with each syntax using PowerShell.

$syntaxList = ${syntax} ; foreach ($syntax in $syntaxList) { ; ${SharpView} $syntax -}
