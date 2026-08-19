#define MyAppName "Zelvik"
#define MyAppVersion "1.5.0"
#define MyAppPublisher "Zelvik"
#define MyAppExeName "Zelvik1.5.exe"
#define MyAppDebugExeName "Zelvik1.5Debug.exe"
#define MyUpdaterExeName "ZelvikUpdater.exe"


[Setup]
AppId={{e2b69417-d5e7-4842-9e48-498ef072fade}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={localappdata}\Programs\Zelvik
DefaultGroupName=Zelvik
DisableProgramGroupPage=yes

OutputDir=..\dist\installer
OutputBaseFilename=Zelvik-{#MyAppVersion}-Setup

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

UninstallDisplayName=Zelvik
UninstallDisplayIcon={app}\Zelvik.exe

PrivilegesRequired=lowest

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

SetupIconFile=..\assets\zelvik.ico

CloseApplications=yes
RestartApplications=no


[Types]
Name: "full"; Description: "Zelvik and Zelvik Debug"
Name: "normal"; Description: "Zelvik only"
Name: "debug"; Description: "Zelvik Debug only"


[Components]
Name: "zelvik"; Description: "Zelvik"; Types: full normal
Name: "debug"; Description: "Zelvik Debug"; Types: full debug


[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; DestName: "Zelvik.exe"; Components: zelvik; Flags: ignoreversion
Source: "..\dist\{#MyAppDebugExeName}"; DestDir: "{app}"; DestName: "ZelvikDebug.exe"; Components: debug; Flags: ignoreversion
Source: "..\dist\{#MyUpdaterExeName}"; DestDir: "{app}"; DestName: "{#MyUpdaterExeName}"; Flags: ignoreversion


[Icons]
Name: "{group}\Zelvik"; Filename: "{app}\Zelvik.exe"; Components: zelvik
Name: "{group}\Zelvik Debug"; Filename: "{app}\ZelvikDebug.exe"; Components: debug
Name: "{group}\Uninstall Zelvik"; Filename: "{uninstallexe}"

Name: "{autodesktop}\Zelvik"; Filename: "{app}\Zelvik.exe"; Tasks: desktopicon; Components: zelvik
Name: "{autodesktop}\Zelvik Debug"; Filename: "{app}\ZelvikDebug.exe"; Tasks: desktopdebugicon; Components: debug


[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut for Zelvik"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "desktopdebugicon"; Description: "Create a desktop shortcut for Zelvik &Debug"; GroupDescription: "Additional shortcuts:"; Flags: unchecked


[Run]
Filename: "{app}\Zelvik.exe"; Description: "Launch Zelvik"; Components: zelvik; Flags: nowait postinstall skipifsilent
Filename: "{app}\ZelvikDebug.exe"; Description: "Launch Zelvik Debug"; Components: debug; Flags: nowait postinstall skipifsilent unchecked