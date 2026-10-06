Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Project\Ambuigity"
WshShell.Run "python web_server.py", 0
Set WshShell = Nothing
