; Inno Setup 6 script for C++ Adventure (Phase 11).
; Build: build-windows.bat runs ISCC with /DAppVersion=<server.APP_VERSION> after PyInstaller.
;
; - Per-user install, no administrator rights (same place as the older PowerShell installer).
; - Setup and uninstall ask the user to close a running copy (AppMutex = desktop.SINGLE_INSTANCE_MUTEX).
; - Setup warns when the Microsoft Edge WebView2 runtime is missing.
; - Uninstall removes the program and the sandbox AppContainer profile (it only holds temporary
;   program runs). Profiles, progress and backups in %LOCALAPPDATA%\CppAdventure are kept.
; - The files are not code-signed: no signing certificate is available.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\dist\CppAdventure"
#endif

[Setup]
AppId={{6F4C2E8A-3B1D-4E57-9A0C-5D2B8E7A41C3}
AppName=C++ Adventure
AppVersion={#AppVersion}
AppVerName=C++ Adventure {#AppVersion}
AppPublisher=C++ Adventure
VersionInfoVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\CppAdventure
DefaultGroupName=C++ Adventure
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=C++Adventure-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
AppMutex=Local\CppAdventure.SingleInstance
CloseApplications=yes
UninstallDisplayIcon={app}\CppAdventure.exe
UninstallDisplayName=C++ Adventure

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
turkish.DesktopIcon=Masaüstü kısayolu oluştur
russian.DesktopIcon=Создать ярлык на рабочем столе
turkish.NoWebView2=C++ Adventure, Microsoft Edge WebView2 Runtime ile çalışır ve bu bilgisayarda bulunamadı.%n%nKurulum devam edecek; uygulamayı açmadan önce ücretsiz runtime'ı şu adresten kur:%nhttps://go.microsoft.com/fwlink/p/?LinkId=2124703
russian.NoWebView2=C++ Adventure работает на Microsoft Edge WebView2 Runtime, но он не найден на этом компьютере.%n%nУстановка продолжится; перед запуском установи бесплатный runtime:%nhttps://go.microsoft.com/fwlink/p/?LinkId=2124703
turkish.KeptData=Profillerin ve ilerlemen silinmedi: %1
russian.KeptData=Профили и прогресс сохранены: %1

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\C++ Adventure"; Filename: "{app}\CppAdventure.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\C++ Adventure"; Filename: "{app}\CppAdventure.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\CppAdventure.exe"; Description: "{cm:LaunchProgram,C++ Adventure}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\CppAdventure.exe"; Parameters: "--remove-sandbox-profile"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveSandboxProfile"

[Code]
const
  WebView2Client = 'Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function HasWebView2(): Boolean;
var
  Version: String;
begin
  Result :=
    (RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\' + WebView2Client, 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0')) or
    (RegQueryStringValue(HKLM, 'SOFTWARE\' + WebView2Client, 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0')) or
    (RegQueryStringValue(HKCU, 'Software\' + WebView2Client, 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0'));
end;

function InitializeSetup(): Boolean;
begin
  if not HasWebView2() then
    MsgBox(CustomMessage('NoWebView2'), mbInformation, MB_OK);
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and not UninstallSilent() then
    MsgBox(FmtMessage(CustomMessage('KeptData'), [ExpandConstant('{localappdata}\CppAdventure')]), mbInformation, MB_OK);
end;
