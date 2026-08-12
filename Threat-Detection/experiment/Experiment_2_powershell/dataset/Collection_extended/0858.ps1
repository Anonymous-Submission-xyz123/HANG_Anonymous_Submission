# Natural language intent:
# Accessing Physical Memory with Windows API, This PowerShell script uses the ReadProcessMemory function from the Windows API to read a specified amount of memory from a process. It's useful for extracting information from running processes.

Add-Type -TypeDefinition @" using System; using System.Runtime.InteropServices; public class MemoryReader { [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, [Out] byte[] lpBuffer, int dwSize, out int lpNumberOfBytesRead); } "@ $process = Get-Process -Name 'process_name' $handle = $process.Handle $buffer = New-Object byte[] 1024 $bytesRead = 0 [MemoryReader]::ReadProcessMemory($handle, [IntPtr]0x00000000, $buffer, $buffer.Length, [ref]$bytesRead)
