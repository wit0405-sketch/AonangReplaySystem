; Inno Setup script for AONANG LANDMARK REPLAY SYSTEM
#define MyAppName "AONANG LANDMARK REPLAY SYSTEM"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "Aonang Landmark Boxing Stadium"
#define MyAppExeName "AonangReplaySystem.exe"

[Setup]
AppId={{A3A2D07C-1BA7-46A4-9E12-8D0D3A11BEEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\AonangReplaySystem
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=Setup_AonangReplaySystem
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\AonangReplaySystem.exe

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\AonangReplaySystem\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\AONANG Replay System"; Filename: "{app}\AonangReplaySystem.exe"
Name: "{autodesktop}\AONANG Replay System"; Filename: "{app}\AonangReplaySystem.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AonangReplaySystem.exe"; Description: "Launch AONANG Replay System"; Flags: postinstall nowait skipifsilent
