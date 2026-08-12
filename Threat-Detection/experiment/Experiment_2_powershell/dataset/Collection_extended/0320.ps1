# Natural language intent:
# Copy Firefox profiles to a temporary location.

Copy-Item "$env:APPDATA\Mozilla\Firefox\Profiles\" -Destination $env:temp -Force -Recurse
