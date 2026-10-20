#define AppVersion "1.0.0"
#define AppName "智电析电力系统运行数据分析与可视化软件 V1.0"
#ifndef DistDir
  #define DistDir "..\dist\SmartPowerAnalyzer"
#endif
#ifndef ReleaseDir
  #define ReleaseDir "..\release"
#endif
[Setup]
AppId={{CF8757AD-241E-49A0-8CCE-B1EA917D976A}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName}（1.0.0）
DefaultDirName={localappdata}\Programs\SmartPowerAnalyzer
DefaultGroupName=智电析
DisableProgramGroupPage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#ReleaseDir}
OutputBaseFilename=SmartPowerAnalyzer-Setup-{#AppVersion}
SetupIconFile=..\smartpower\assets\app.ico
UninstallDisplayIcon={app}\SmartPowerAnalyzer.exe
VersionInfoVersion=1.0.0.0
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
InfoBeforeFile=DISTRIBUTION_NOTICE.md
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
CloseApplications=no
RestartApplications=no
DisableWelcomePage=no
[Languages]
Name: "chinesesimp"; MessagesFile: "ChineseSimplified.isl"
[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: unchecked
[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\智电析 V1.0"; Filename: "{app}\SmartPowerAnalyzer.exe"; WorkingDir: "{app}"
Name: "{group}\卸载智电析"; Filename: "{uninstallexe}"
Name: "{autodesktop}\智电析 V1.0"; Filename: "{app}\SmartPowerAnalyzer.exe"; WorkingDir: "{app}"; Tasks: desktopicon
[Run]
Filename: "{app}\SmartPowerAnalyzer.exe"; Description: "启动智电析"; Flags: nowait postinstall skipifsilent
; No UninstallDelete: remove only installer-owned files/shortcuts. User SQLite,
; preferences and exported reports in per-user locations are intentionally kept.
