# Natural language intent:
# Get stored Wi-Fi passwords from Wireless Profiles, With this command we can extract all stored Wi-Fi passwords (WEP, WPA PSK, WPA2 PSK etc.) from the wireless profiles that are configured in the Windows system:

(netsh wlan show profiles) | Select-String "\:(.+)$" | %{$name=$_.Matches.Groups[1].Value.Trim(); $_} | %{(netsh wlan show profile name="$name" key=clear)}  | Select-String "Key Content\W+\:(.+)$" | %{$pass=$_.Matches.Groups[1].Value.Trim(); $_} | %{[PSCustomObject]@{ PROFILE_NAME=$name;PASSWORD=$pass }} | Format-Table -AutoSize
