# Natural language intent:
# Copy an Excel VBA add-in to the Excel startup folder and start Excel.

Copy "PathToAtomicsFolder\T1137.006\bin\Addins\ExcelVBAaddin.xlam" "$env:APPDATA\Microsoft\Excel\XLSTART ; otepad.xlam" ; Start-Process "Excel"
