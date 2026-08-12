# Natural language intent:
# use icacls.exe to grant read and execute (RX) permissions to the "Everyone" group for the specified directory path "C:\Users\redsuit\Documents\ssh\OpenSSH-Win64" and its subdirectories (/T).

icacls.exe "C:\Users\redsuit\Documents\ssh\OpenSSH-Win64" /grant Everyone:RX /T
