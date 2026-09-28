@echo off
setlocal EnableExtensions

cd /d "%~dp0"

where python >nul 2>nul || (
    echo Python nao encontrado.
    exit /b 1
)

where php >nul 2>nul || (
    echo PHP nao encontrado. Para gerar o pacote portatil localmente, instale PHP 8.1+ ou use o GitHub Actions.
    exit /b 1
)

where composer >nul 2>nul || (
    echo Composer nao encontrado. Para gerar o pacote portatil localmente, instale Composer ou use o GitHub Actions.
    exit /b 1
)

composer install --no-dev --optimize-autoloader || exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File tools\prepare_portable_php.ps1 -TargetDir runtime\php || exit /b 1
python -m pip install --upgrade pyinstaller || exit /b 1

if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist package rmdir /s /q package

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name DownloadNFe55 ^
  app.py || exit /b 1

if not exist package\DownloadNFe55 mkdir package\DownloadNFe55

if exist dist\DownloadNFe55\DownloadNFe55.exe (
    robocopy dist\DownloadNFe55 package\DownloadNFe55 /E >nul
    if errorlevel 8 exit /b %errorlevel%
) else if exist dist\DownloadNFe55.exe (
    copy /Y dist\DownloadNFe55.exe package\DownloadNFe55\DownloadNFe55.exe >nul || exit /b 1
) else (
    echo Executavel DownloadNFe55 nao encontrado em dist.
    dir dist /s
    exit /b 1
)

robocopy php package\DownloadNFe55\php /E >nul
if errorlevel 8 exit /b %errorlevel%

robocopy vendor package\DownloadNFe55\vendor /E >nul
if errorlevel 8 exit /b %errorlevel%

robocopy runtime package\DownloadNFe55\runtime /E >nul
if errorlevel 8 exit /b %errorlevel%

where 7z >nul 2>nul
if %errorlevel%==0 (
    7z a -tzip package\DownloadNFe55-windows-portable.zip .\package\DownloadNFe55\* -r || exit /b 1
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'package\DownloadNFe55\*' -DestinationPath 'package\DownloadNFe55-windows-portable.zip' -Force" || exit /b 1
)

if not exist package\DownloadNFe55\DownloadNFe55.exe exit /b 1
if not exist package\DownloadNFe55-windows-portable.zip exit /b 1

echo.
echo Pasta portatil criada em package\DownloadNFe55
echo ZIP portatil criado em package\DownloadNFe55-windows-portable.zip
