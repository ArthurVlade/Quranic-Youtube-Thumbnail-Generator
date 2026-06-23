; ============================================================
;  Inno Setup script - Quran Thumbnail Generator
;  Build the app first with build.bat (produces
;  dist\QuranThumbnailGenerator\), then compile this script
;  with Inno Setup (https://jrsoftware.org/isdl.php) to create
;  a single Windows installer: Output\QuranThumbnailGenerator-Setup.exe
; ============================================================

#define MyAppName "Quran Thumbnail Generator"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ArthurVlade"
#define MyAppURL "https://github.com/ArthurVlade/Quranic-Thumbnail-Generator"
#define MyAppExeName "QuranThumbnailGenerator.exe"

[Setup]
AppId={{8F3A9C24-7B61-4E2D-9A5F-1C2D3E4F5A6B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=QuranThumbnailGenerator-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Bundle the entire PyInstaller onedir output
Source: "dist\QuranThumbnailGenerator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the per-user data created at runtime (settings, reciters, cache, custom assets)
Type: filesandordirs; Name: "{localappdata}\QuranThumbnailGenerator"
