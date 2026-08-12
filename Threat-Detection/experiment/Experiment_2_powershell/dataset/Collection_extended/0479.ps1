# Natural language intent:
# Add a registry entry to disable Hypervisor Enforced Code Integrity using the Windows Registry.

reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v "Enabled" /t REG_DWORD /d 0 /f
