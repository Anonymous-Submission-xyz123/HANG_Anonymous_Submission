# Natural language intent:
# Variable Name Obfuscation, Obfuscates a command by splitting it into parts and reassembling it, making the command less recognizable to security tools.

$o = 'Get'; $b = 'Process'; $cmd = $o + '-' + $b; Invoke-Expression $cmd
