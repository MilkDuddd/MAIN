' Intel Platform — Windows silent launcher (no cmd window)
' Double-click this file for a completely terminal-free experience
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
sh.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
sh.Run "Intel Platform.bat", 0, False
