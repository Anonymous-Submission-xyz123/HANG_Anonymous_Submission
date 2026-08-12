# Natural language intent:
# Query the Windows registry for values containing 'password'.

reg query HKLM /f password /t REG_SZ /s
