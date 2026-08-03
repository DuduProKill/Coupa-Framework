@echo off
title Release - Coupa Framework
setlocal EnableDelayedExpansion

echo ============================================================
echo  Coupa Framework - Publicar Nova Versao
echo ============================================================
echo.

:: Verifica gh CLI
gh --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] GitHub CLI nao encontrado.
    echo Instale em: https://cli.github.com
    pause
    exit /b 1
)

:: Verifica autenticacao gh
gh auth status > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Nao autenticado no GitHub CLI. Execute: gh auth login
    pause
    exit /b 1
)

:: Pede a nova versao
set /p VERSION="Digite a nova versao (ex: 1.1.1): "
if "%VERSION%"=="" (
    echo [ERRO] Versao nao informada.
    pause
    exit /b 1
)

echo.
echo [1/5] Atualizando versao para %VERSION%...

:: Atualiza CURRENT_VERSION no updater.py
powershell -Command "(Get-Content modules\updater.py) -replace 'CURRENT_VERSION = \".*\"', 'CURRENT_VERSION = \"%VERSION%\"' | Set-Content modules\updater.py"

:: Atualiza AppVersion, OutputBaseFilename, UninstallDisplayName e VersionInfoVersion no installer.iss
powershell -Command "(Get-Content installer.iss) -replace 'AppVersion=.*', 'AppVersion=%VERSION%' -replace 'OutputBaseFilename=.*', 'OutputBaseFilename=CoupaFramework_Setup_v%VERSION%' -replace 'UninstallDisplayName=.*', 'UninstallDisplayName=Coupa Framework v%VERSION%' -replace 'VersionInfoVersion=.*', 'VersionInfoVersion=%VERSION%' | Set-Content installer.iss"

echo       OK

echo.
echo [2/5] Commit e tag no Git...
git add modules\updater.py installer.iss
git commit -m "chore: bump version to v%VERSION%"
git tag "v%VERSION%"
git push
git push origin "v%VERSION%"
if %errorlevel% neq 0 (
    echo [ERRO] Falha no push. Verifique sua conexao e permissoes.
    pause
    exit /b 1
)
echo       OK

echo.
echo [3/5] Buildando o instalador...
call build_installer.bat
if %errorlevel% neq 0 (
    echo [ERRO] Falha no build.
    pause
    exit /b 1
)

echo.
echo [4/5] Localizando instalador gerado...
set "INSTALLER="
for %%F in (installer_output\CoupaFramework_Setup_v%VERSION%.exe) do set "INSTALLER=%%F"

if not defined INSTALLER (
    echo [ERRO] Instalador nao encontrado em installer_output\
    echo Verifique se o Inno Setup esta instalado e o build foi concluido.
    pause
    exit /b 1
)
echo       Encontrado: %INSTALLER%

echo.
echo [5/5] Publicando release no GitHub...
gh release create "v%VERSION%" "%INSTALLER%" --title "Coupa Framework v%VERSION%" --notes "Versao v%VERSION%. Baixe o instalador e execute. Se ja tiver instalado, atualiza automaticamente." --latest
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao publicar release no GitHub.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  SUCESSO! Release v%VERSION% publicada no GitHub.
echo  Os usuarios serao notificados na proxima abertura do app.
echo ============================================================
pause
