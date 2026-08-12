# Natural language intent:
# Disable various Windows Defender features

Set-MpPreference -DisableRealtimeMonitoring 1 ; Set-MpPreference -DisableBehaviorMonitoring 1 ; Set-MpPreference -DisableScriptScanning 1 ; Set-MpPreference -DisableBlockAtFirstSeen 1
