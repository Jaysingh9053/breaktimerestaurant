#define MyAppName "Breaktime Restaurant"
#define MyAppPublisher "Breaktime Restaurant"
#define MyAppExeName "BreaktimeRestaurant.exe"

#ifndef MyAppSource
#define MyAppSource "."
#endif
#ifndef MyAppOutput
#define MyAppOutput "."
#endif
#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif
#ifndef MyAppOutputBaseFilename
#define MyAppOutputBaseFilename "BreaktimeRestaurant-Setup"
#endif
#ifndef MyAppIcon
#define MyAppIcon "app_icon.ico"
#endif

[Setup]
AppId={{D5FBD5A2-6C2C-4B50-9D98-5C1FD8B8B6F1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\BreaktimeRestaurant
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#MyAppOutput}
OutputBaseFilename={#MyAppOutputBaseFilename}
SetupIconFile={#MyAppIcon}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#MyAppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
