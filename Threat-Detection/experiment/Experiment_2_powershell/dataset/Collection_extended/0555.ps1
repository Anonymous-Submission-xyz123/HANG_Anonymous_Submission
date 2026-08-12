# Natural language intent:
# Query the Windows registry for values containing 'password' in the current user's hive.

reg query HKCU /f password /t REG_SZ /s
