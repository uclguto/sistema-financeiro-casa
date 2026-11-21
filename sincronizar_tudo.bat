@echo off
setlocal

echo =====================================================================
echo    SISTEMA FINANCEIRO CASA - SINCRONIZACAO COMPLETA (V3.0)
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/5] Extraindo e reconciliando extratos nas 8 Secoes Canonicas (A-Z)...
python src\extrator_unificado.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha na extracao de dados. Abortando.
    if "%~1"=="/no_pause" exit /b 1
    pause
    exit /b 1
)

echo.
echo [2/5] Criptografando cofre PWA com WebCrypto AES-256-GCM...
python src\crypto_pwa.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha na criptografia do PWA. Abortando.
    if "%~1"=="/no_pause" exit /b 1
    pause
    exit /b 1
)

echo.
echo [3/5] Atualizando Planilha (18 Abas) no Google Drive via API v3...
python src\sync_google_sheets.py
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Falha ou aviso no envio para o Google Drive.
)

echo.
echo [4/5] Executando suite de testes automatizados (pytest)...
python -m pytest tests\test_motor_financeiro.py -q
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Bateria de testes automatizados falhou.
    if "%~1"=="/no_pause" exit /b 1
    pause
    exit /b 1
)

echo.
echo [5/5] Publicando atualizacoes no GitHub e GitHub Pages...
python src\deploy_github_pages.py
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Falha ou aviso no deploy do GitHub Pages.
)

echo.
echo =====================================================================
echo    SINCRONIZACAO V3.0 CONCLUIDA COM SUCESSO!
echo    Planilha Google Drive atualizada na nuvem (18 abas).
echo    App PWA disponivel em: https://uclguto.github.io/sistema-financeiro-casa/
echo =====================================================================
echo.

if not "%~1"=="/no_pause" pause
