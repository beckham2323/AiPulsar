#define MyAppName "AiPulsar"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "VESKOR (V.E. Smirnov)"
#define MyAppURL "https://github.com"
#define MyAppExeName "AiPulsar.exe"

[Setup]
AppId={{8E9A4B21-7C3D-4F1A-9B8E-2026AIPULSAR}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=D:\AiPulsar\LICENSE.txt
OutputDir=D:\AiPulsar
OutputBaseFilename=Setup_AiPulsar
SetupIconFile=D:\AiPulsar\aipulsar.ico
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "D:\AiPulsar\dist\AiPulsar\*"; DestDir: "{app}"; Excludes: "startup_diag.txt,pulsar_crash.log"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
