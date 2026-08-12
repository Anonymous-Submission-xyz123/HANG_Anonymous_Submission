# Natural language intent:
# Analyze PowerShell command line parameters for potential attack vectors.

Out-ATHPowerShellCommandLineParameter -CommandLineSwitchType ${command_line} -CommandParamVariation ${command_param_variation} -Execute -ErrorAction Stop
