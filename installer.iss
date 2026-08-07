[Setup]
AppName=Coupa Framework - Automação de Suprimentos
AppVersion=1.1.4
AppPublisher=Coupa Framework
AppPublisherURL=https://github.com/DuduProKill/Coupa-Framework
DefaultDirName={localappdata}\CoupaFramework
DefaultGroupName=Coupa Framework
OutputDir=installer_output
OutputBaseFilename=CoupaFramework_Setup_v1.1.4
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\CoupaFramework.exe
UninstallDisplayName=Coupa Framework v1.1.4
MinVersion=10.0
VersionInfoVersion=1.1.4
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
; Sem "skipifsilent": também relança o app automaticamente após uma instalação
; silenciosa (/VERYSILENT), usada pelo fluxo "Baixar este módulo" dentro do app.
Filename: "{app}\CoupaFramework.exe"; Description: "Iniciar Coupa Framework agora"; Flags: nowait postinstall

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

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

// Importante: o parâmetro "Check:" de [UninstallRun] é avaliado durante a
// INSTALAÇÃO (na etapa "Salvando informações de desinstalação..."), não na
// hora de desinstalar — por isso a pergunta aparecia mesmo na primeira
// instalação. O jeito certo de perguntar algo só na hora real de desinstalar
// é aqui, em CurUninstallStepChanged, que roda dentro do desinstalador.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if ConfirmarLimpezaDados() then
    begin
      DelTree(ExpandConstant('{userappdata}\CoupaFramework'), True, True, True);
    end;
  end;
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

// Lê o valor previamente salvo de um módulo em {app}\module_selection.json,
// para não desmarcar (e apagar os arquivos de) módulos já instalados quando
// o instalador é reaberto só para adicionar UM módulo específico.
function ReadModuleValueFromJson(ModuleKey: String; DefaultValue: Boolean): Boolean;
var
  FileName: String;
  Lines: TArrayOfString;
  Index: Integer;
  SearchKey: String;
begin
  Result := DefaultValue;
  FileName := ExpandConstant('{app}\module_selection.json');
  if not FileExists(FileName) then
    Exit;
  if not LoadStringsFromFile(FileName, Lines) then
    Exit;

  SearchKey := '"' + ModuleKey + '":';
  for Index := 0 to GetArrayLength(Lines) - 1 do
  begin
    if Pos(SearchKey, Lines[Index]) > 0 then
    begin
      Result := Pos('true', Lines[Index]) > 0;
      Exit;
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

  // Pré-popula com a seleção já instalada (se houver), preservando módulos
  // que o usuário já tinha habilitado em instalações anteriores.
  ModuleSelectionPage.Values[0] := ReadModuleValueFromJson('extrator', True);
  ModuleSelectionPage.Values[1] := ReadModuleValueFromJson('downloader', True);
  ModuleSelectionPage.Values[2] := ReadModuleValueFromJson('pdf', True);
  ModuleSelectionPage.Values[3] := ReadModuleValueFromJson('renomeador', True);
  ModuleSelectionPage.Values[4] := ReadModuleValueFromJson('organizador', True);
  ModuleSelectionPage.Values[5] := ReadModuleValueFromJson('email', True);
  ModuleSelectionPage.Values[6] := ReadModuleValueFromJson('perfis', True);

  // Se um módulo específico foi solicitado (via /MODULE=xxx), garante que ele
  // fique marcado — sem desmarcar os módulos que já estavam habilitados.
  if RequestedModuleName = 'extrator' then ModuleSelectionPage.Values[0] := True;
  if RequestedModuleName = 'downloader' then ModuleSelectionPage.Values[1] := True;
  if RequestedModuleName = 'pdf' then ModuleSelectionPage.Values[2] := True;
  if RequestedModuleName = 'renomeador' then ModuleSelectionPage.Values[3] := True;
  if RequestedModuleName = 'organizador' then ModuleSelectionPage.Values[4] := True;
  if RequestedModuleName = 'email' then ModuleSelectionPage.Values[5] := True;
  if RequestedModuleName = 'perfis' then ModuleSelectionPage.Values[6] := True;
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
    // Salva a seleção aqui (em vez de em NextButtonClick) para funcionar tanto
    // em instalação interativa quanto em instalação silenciosa (/VERYSILENT),
    // já que o assistente não é navegado nesse último caso.
    SaveModuleSelection();
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
