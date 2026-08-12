# Natural language intent:
# Invoke a malicious HTML Application (HTA) file with specific options and simulate lateral movement.

Invoke-ATHHTMLApplication -HTAFilePath ${hta_file_path} -ScriptEngine ${script_engine} -AsLocalUNCPath -SimulateLateralMovement -MSHTAFilePath ${mshta_file_path}
