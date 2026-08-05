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
var
  ModuleSelectionPage: TInputOptionWizardPage;
  RequestedModuleName: String;

function ConfirmarLimpezaDados(): Boolean;
begin
  Result := MsgBox(
    'Deseja remover também os logs e histórico salvos em %APPDATA%\CoupaFramework?' + #13#10 +
    '(Logs, histórico de renomeação e configurações locais serão apagados)',
    mbConfirmation, MB_YESNO
  ) = IDYES;
end;

function GetRequestedModuleName(): String;
var
  Index: Integer;
  Param: String;
begin
  Result := '';
  for Index := 1 to ParamCount do
  begin
    Param := LowerCase(ParamStr(Index));
    if Pos('/module=', Param) = 1 then
    begin
      Result := Copy(Param, Length('/module=') + 1, Length(Param));
      Break;
    end;
  end;
end;

procedure InitializeWizard();
begin
  RequestedModuleName := GetRequestedModuleName();
  ModuleSelectionPage := CreateInputOptionPage(
    wpSelectTasks,
    'Módulos do programa',
    'Escolha quais módulos deseja instalar.',
    'Marque os módulos que você quer usar. Todas as opções vêm marcadas por padrão.',
    False, False
  );

  ModuleSelectionPage.Add('Extrator Inteligente');
  ModuleSelectionPage.Add('Baixador de Orçamentos');
  ModuleSelectionPage.Add('Gerador de PDF de Pedidos');
  ModuleSelectionPage.Add('Renomeador');
  ModuleSelectionPage.Add('Organizador');
  ModuleSelectionPage.Add('Disparo de E-mails');
  ModuleSelectionPage.Add('Gerenciar Perfis');

  if RequestedModuleName <> '' then
  begin
    ModuleSelectionPage.Values[0] := False;
    ModuleSelectionPage.Values[1] := False;
    ModuleSelectionPage.Values[2] := False;
    ModuleSelectionPage.Values[3] := False;
    ModuleSelectionPage.Values[4] := False;
    ModuleSelectionPage.Values[5] := False;
    ModuleSelectionPage.Values[6] := False;

    if RequestedModuleName = 'extrator' then ModuleSelectionPage.Values[0] := True;
    if RequestedModuleName = 'downloader' then ModuleSelectionPage.Values[1] := True;
    if RequestedModuleName = 'pdf' then ModuleSelectionPage.Values[2] := True;
    if RequestedModuleName = 'renomeador' then ModuleSelectionPage.Values[3] := True;
    if RequestedModuleName = 'organizador' then ModuleSelectionPage.Values[4] := True;
    if RequestedModuleName = 'email' then ModuleSelectionPage.Values[5] := True;
    if RequestedModuleName = 'perfis' then ModuleSelectionPage.Values[6] := True;
  end
  else
  begin
    ModuleSelectionPage.Values[0] := True;
    ModuleSelectionPage.Values[1] := True;
    ModuleSelectionPage.Values[2] := True;
    ModuleSelectionPage.Values[3] := True;
    ModuleSelectionPage.Values[4] := True;
    ModuleSelectionPage.Values[5] := True;
    ModuleSelectionPage.Values[6] := True;
  end;
end;

function BoolToJsonString(Value: Boolean): String;
begin
  if Value then
    Result := 'true'
  else
    Result := 'false';
end;

function SaveModuleSelection(): Boolean;
var
  ModuleFileName: String;
  ModuleDir: String;
  ModuleJson: String;
begin
  ModuleFileName := ExpandConstant('{app}\module_selection.json');
  ModuleDir := ExtractFileDir(ModuleFileName);

  // Garante que o diretório de destino exista antes de tentar salvar o arquivo
  if not DirExists(ModuleDir) then
  begin
    ForceDirectories(ModuleDir);
  end;

  ModuleJson := '{' + #13#10 +
    '  "extrator": ' + BoolToJsonString(ModuleSelectionPage.Values[0]) + ',' + #13#10 +
    '  "downloader": ' + BoolToJsonString(ModuleSelectionPage.Values[1]) + ',' + #13#10 +
    '  "pdf": ' + BoolToJsonString(ModuleSelectionPage.Values[2]) + ',' + #13#10 +
    '  "renomeador": ' + BoolToJsonString(ModuleSelectionPage.Values[3]) + ',' + #13#10 +
    '  "organizador": ' + BoolToJsonString(ModuleSelectionPage.Values[4]) + ',' + #13#10 +
    '  "email": ' + BoolToJsonString(ModuleSelectionPage.Values[5]) + ',' + #13#10 +
    '  "perfis": ' + BoolToJsonString(ModuleSelectionPage.Values[6]) + #13#10 +
    '}' + #13#10;

  Result := SaveStringToFile(ModuleFileName, ModuleJson, False);
  if not Result then
  begin
    MsgBox('Não foi possível salvar a seleção de módulos do instalador.', mbError, MB_OK);
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  if CurPageID = ModuleSelectionPage.ID then
  begin
    Result := SaveModuleSelection();
    Exit;
  end;

  Result := True;
end;

function RemoveUnselectedModuleFiles(): Boolean;
var
  ModuleDir: String;
begin
  ModuleDir := ExpandConstant('{app}\modules');

  if not ModuleSelectionPage.Values[0] then
  begin
    if FileExists(ModuleDir + '\ui_coupa.py') then DeleteFile(ModuleDir + '\ui_coupa.py');
    if FileExists(ModuleDir + '\coupa_scraper.py') then DeleteFile(ModuleDir + '\coupa_scraper.py');
  end;

  if not ModuleSelectionPage.Values[1] then
  begin
    if FileExists(ModuleDir + '\ui_downloader.py') then DeleteFile(ModuleDir + '\ui_downloader.py');
    if FileExists(ModuleDir + '\download_scraper.py') then DeleteFile(ModuleDir + '\download_scraper.py');
  end;

  if not ModuleSelectionPage.Values[2] then
  begin
    if FileExists(ModuleDir + '\ui_pdf_generator.py') then DeleteFile(ModuleDir + '\ui_pdf_generator.py');
    if FileExists(ModuleDir + '\pdf_generator.py') then DeleteFile(ModuleDir + '\pdf_generator.py');
  end;

  if not ModuleSelectionPage.Values[3] then
  begin
    if FileExists(ModuleDir + '\ui_renomeador.py') then DeleteFile(ModuleDir + '\ui_renomeador.py');
    if FileExists(ModuleDir + '\services\renomeador_service.py') then DeleteFile(ModuleDir + '\services\renomeador_service.py');
  end;

  if not ModuleSelectionPage.Values[4] then
  begin
    if FileExists(ModuleDir + '\ui_organizador.py') then DeleteFile(ModuleDir + '\ui_organizador.py');
    if FileExists(ModuleDir + '\organizador.py') then DeleteFile(ModuleDir + '\organizador.py');
  end;

  if not ModuleSelectionPage.Values[5] then
  begin
    if FileExists(ModuleDir + '\ui_email_sender.py') then DeleteFile(ModuleDir + '\ui_email_sender.py');
    if FileExists(ModuleDir + '\email_sender.py') then DeleteFile(ModuleDir + '\email_sender.py');
  end;

  if not ModuleSelectionPage.Values[6] then
  begin
    if FileExists(ModuleDir + '\ui_profile_manager.py') then DeleteFile(ModuleDir + '\ui_profile_manager.py');
  end;

  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RemoveUnselectedModuleFiles();
  end;
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