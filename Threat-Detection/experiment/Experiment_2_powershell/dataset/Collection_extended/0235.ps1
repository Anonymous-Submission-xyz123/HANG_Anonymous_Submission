# Natural language intent:
# Run malicious code that displays a Windows Forms message box with the message 'Malicious Code'.

$code = @';[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")[System.Windows.Forms.MessageBox]::Show("Malicious Code")'; Invoke-Expression $code
