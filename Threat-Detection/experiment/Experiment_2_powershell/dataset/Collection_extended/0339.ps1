# Natural language intent:
# Modify registry to create a Run key with a specified value.

$RunKey = "${reg_key_path}" ; Set-ItemProperty -Path $RunKey -Name "socks5_powershell" -Value "${reg_key_value}"
