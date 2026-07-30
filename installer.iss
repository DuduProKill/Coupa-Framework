[Setup]
AppName=Coupa Framework - Automação de Suprimentos
AppVersion=1.0.0
AppPublisher=Coupa Framework
AppPublisherURL=https://github.com/DuduProKill/Framework
DefaultDirName={autopf}\CoupaFramework
DefaultGroupName=Coupa Framework
OutputDir=installer_output
OutputBaseFilename=CoupaFramework_Setup_v1.0.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\CoupaFramework.exe
MinVersion=10.0

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Criar atalho na Barra de Tarefas"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
; Copia toda a pasta gerada pelo PyInstaller
Source: "dist\CoupaFramework\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Coupa Framework"; Filename: "{app}\CoupaFramework.exe"
Name: "{group}\Desinstalar Coupa Framework"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Coupa Framework"; Filename: "{app}\CoupaFramework.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Coupa Framework"; Filename: "{app}\CoupaFramework.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\CoupaFramework.exe"; Description: "Iniciar Coupa Framework agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// Verifica se o Microsoft Edge está instalado antes de instalar
function InitializeSetup(): Boolean;
var
  EdgePath: String;
begin
  Result := True;
  EdgePath := 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe';
  if not FileExists(EdgePath) then
  begin
    EdgePath := 'C:\Program Files\Microsoft\Edge\Application\msedge.exe';
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
