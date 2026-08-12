# Natural language intent:
# Conducting Network Sniffing, Sets up a network capture session to sniff packets, which can be analyzed for sensitive data or network troubleshooting.

$adapter = Get-NetAdapter | Select-Object -First 1; New-NetEventSession -Name 'Session1' -CaptureMode SaveToFile -LocalFilePath 'C:\temp\network_capture.etl'; Add-NetEventPacketCaptureProvider -SessionName 'Session1' -Level 4 -CaptureType Both -Enable; Start-NetEventSession -Name 'Session1'; StopNetEventSession -Name 'Session1' after 60
