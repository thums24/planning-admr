; Inno Setup installer for Planning ADMR (Windows)
; Compile with: iscc installer.iss

#define MyAppName "Planning ADMR"
#define MyAppVersion "1.0.0"
#define MyAppExe "Planning ADMR.exe"

[Setup]
AppId={{3F2A1B4C-8D6E-4F2A-9C1B-7E5A3D8F0B42}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Planning ADMR
DefaultGroupName={#MyAppName}
OutputDir={#SourcePath}
OutputBaseFilename=Setup-Planning-ADMR-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExe}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\Planning ADMR\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
