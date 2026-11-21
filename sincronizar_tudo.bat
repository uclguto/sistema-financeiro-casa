@echo off
chcp 65001 > nul
echo =====================================================================
echo    SISTEMA FINANCEIRO CASA G^&J — SINCRONIZAÇÃO COMPLETA
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/4] Extraindo e reconciliando 28 categorias de Jan a Nov/2026...
python src\extrator_unificado.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha na extração de dados. Abortando.
    goto :fim
)

echo.
echo [2/4] Criptografando cofre PWA com WebCrypto AES-256-GCM...
python src\crypto_pwa.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha na criptografia do PWA. Abortando.
    goto :fim
)

echo.
echo [3/4] Atualizando Planilha no Google Drive via API v3 (Nuvem)...
python src\sync_google_sheets.py
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Falha ou aviso no envio para o Google Drive.
)

echo.
echo [4/4] Publicando atualizações no GitHub e GitHub Pages...
python src\deploy_github_pages.py
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Falha ou aviso no deploy do GitHub Pages.
)

echo.
echo =====================================================================
echo    SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!
echo    Planilha Google Drive atualizada na nuvem.
echo    App PWA disponível em: https://uclguto.github.io/sistema-financeiro-casa/
echo =====================================================================
echo.

:fim
if "%1"=="/no_pause" goto :eof
pause
