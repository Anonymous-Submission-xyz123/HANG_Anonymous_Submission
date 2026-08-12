# Natural language intent:
# Defines excluded extensions and adds them to Windows Defender preferences.

$excludedExts= "${excluded_exts}" ; Add-MpPreference -ExclusionExtension $excludedExts
