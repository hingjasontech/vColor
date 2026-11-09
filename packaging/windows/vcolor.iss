; Inno Setup script for the vColor Windows installer.
;
; scripts/package.py calls this with these defines:
;   /DMyAppVersion=<version> /DMyArch=<x64compatible|arm64>
;   /DSourceDir=<dist>\vColor /DOutputDir=<dist>
;   /DOutputBaseFilename=vColor-<version>-windows-<x64|arm64>-setup
;
; To build manually, run from the repository root:
;   iscc /DMyAppVersion=1.1.0 packaging\windows\vcolor.iss

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

#ifndef MyArch
  #define MyArch "x64compatible"
#endif

#ifndef SourceDir
  #define SourceDir "..\..\dist\vColor"
#endif

#ifndef OutputDir
  #define OutputDir "..\..\dist"
#endif

#ifndef OutputBaseFilename
  #define OutputBaseFilename "vColor-setup"
#endif

[Setup]
AppId={{7C4E2F1A-9B3D-4C58-8A6E-2D1F0B7C9E43}
AppName=vColor
AppVersion={#MyAppVersion}
AppVerName=vColor {#MyAppVersion}
AppPublisher=vColor
AppPublisherURL=https://github.com/hingjasontech/vColor
AppSupportURL=https://github.com/hingjasontech/vColor/issues
AppUpdatesURL=https://github.com/hingjasontech/vColor/releases
DefaultDirName={autopf}\vColor
DefaultGroupName=vColor
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
MinVersion=10.0
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile=..\..\vcolor\resources\icon.ico
UninstallDisplayIcon={app}\vColor.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed={#MyArch}
ArchitecturesInstallIn64BitMode={#MyArch}
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\vColor"; Filename: "{app}\vColor.exe"
Name: "{autodesktop}\vColor"; Filename: "{app}\vColor.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\vColor.exe"; Description: "{cm:LaunchProgram,vColor}"; Flags: nowait postinstall skipifsilent
