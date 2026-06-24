; ============================================================
;  Quran Thumbnail Generator — Windows installer
;  Build with:  build_installer.bat
;  Output:      Output\QuranThumbnailGenerator-Setup.exe
; ============================================================

#define MyAppName "Quran Thumbnail Generator"
#define MyAppVersion "1.3.1"
#define MyAppPublisher "ArthurVlade"
#define MyAppURL "https://github.com/ArthurVlade/Quranic-Youtube-Thumbnail-Generator"
#define MyAppExeName "QuranThumbnailGenerator.exe"

[Setup]
AppId={{8F3A9C24-7B61-4E2D-9A5F-1C2D3E4F5A6B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=QuranThumbnailGenerator-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
MinVersion=10.0
LicenseFile=
InfoBeforeFile=
; Approximate installed size hint (PyInstaller onedir + assets)
ExtraDiskSpaceRequired=314572800

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Entire PyInstaller output (app + bundled Python runtime + assets)
Source: "dist\QuranThumbnailGenerator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\QuranThumbnailGenerator"

[Messages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nNo Python installation is required — everything is included.%n%nOn first launch the app may download additional scenery images over the internet (one-time, optional if already bundled).

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
