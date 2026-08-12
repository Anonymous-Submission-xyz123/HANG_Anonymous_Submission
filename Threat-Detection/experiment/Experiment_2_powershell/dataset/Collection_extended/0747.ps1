# Natural language intent:
# Find credentials in Sysprep or Unattend files, This command will look for remnants from automated installation and auto-configuration, which could potentially contain plaintext passwords or base64 encoded passwords:

gci c:\ -Include *sysprep.inf,*sysprep.xml,*sysprep.txt,*unattended.xml,*unattend.xml,*unattend.txt -File -Recurse -EA SilentlyContinue
