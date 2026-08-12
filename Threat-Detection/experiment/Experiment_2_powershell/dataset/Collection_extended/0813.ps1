# Natural language intent:
# Utilizing PowerShell Runspaces for Evasion, Executes PowerShell commands within a separate runspace, isolating them from the main PowerShell environment and evading some forms of detection.

$runspace = [runspacefactory]::CreateRunspace(); $runspace.Open(); $pipeline = $runspace.CreatePipeline(); $pipeline.Commands.AddScript('Get-Process'); $results = $pipeline.Invoke(); $runspace.Close(); $results
