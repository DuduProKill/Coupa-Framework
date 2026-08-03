[Setup]
AppName=Coupa Framework - Automação de Suprimentos
AppVersion=1.1.1
AppPublisher=Coupa Framework
AppPublisherURL=https://github.com/DuduProKill/Coupa-Framework
DefaultDirName={localappdata}\CoupaFramework
DefaultGroupName=Coupa Framework
OutputDir=installer_output
OutputBaseFilename=CoupaFramework_Setup_v1.1.1
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\CoupaFramework.exe
UninstallDisplayName=Coupa Framework v1.1.1
MinVersion=10.0
VersionInfoVersion=1.1.1
VersionInfoCompany=Coupa Framework
VersionInfoDescription=Coupa Framework - Automação de Suprimentos
AppId={{B3F2A1D4-7E6C-4F8B-9A2D-1C5E8F3B7A9D}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
; Copia toda a pasta gerada pelo PyInstaller
Source: "dist\CoupaFramework\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copia o icone para que os atalhos possam referencia-lo
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Coupa Framework"; Filename: "{app}\CoupaFramework.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\Desinstalar Coupa Framework"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Coupa Framework"; Filename: "{app}\CoupaFramework.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\CoupaFramework.exe"; Description: "Iniciar Coupa Framework agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[UninstallRun]
; Oferece limpeza opcional dos dados do usuário ao desinstalar
Filename: "{cmd}"; Parameters: "/C rmdir /s /q ""{userappdata}\CoupaFramework"""; \
  StatusMsg: "Removendo dados do usuário..."; Flags: runhidden; \
  Check: ConfirmarLimpezaDados

[Code]
function ConfirmarLimpezaDados(): Boolean;
begin
  Result := MsgBox(
    'Deseja remover também os logs e histórico salvos em %APPDATA%\CoupaFramework?' + #13#10 +
    '(Logs, histórico de renomeação e configurações locais serão apagados)',
    mbConfirmation, MB_YESNO
  ) = IDYES;
end;

// Verifica se o Microsoft Edge está instalado antes de instalar
function InitializeSetup(): Boolean;
var
  EdgePath: String;
begin
  Result := True;
  EdgePath := ExpandConstant('{pf}\Microsoft\Edge\Application\msedge.exe');
  if not FileExists(EdgePath) then
  begin
    EdgePath := ExpandConstant('{pf32}\Microsoft\Edge\Application\msedge.exe');
    if not FileExists(EdgePath) then
    begin
      MsgBox(
        'Atenção: O Microsoft Edge não foi encontrado no caminho padrão.' + #13#10 +
        'O framework utiliza o Edge para automação web.' + #13#10 +
        'Certifique-se de que o Edge está instalado antes de usar o programa.',
        mbInformation, MB_OK
      );
    end;
  end;
end;
