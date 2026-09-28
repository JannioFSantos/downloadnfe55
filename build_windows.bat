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

robocopy php dist\DownloadNFe55\php /E >nul
if errorlevel 8 exit /b %errorlevel%

robocopy vendor dist\DownloadNFe55\vendor /E >nul
if errorlevel 8 exit /b %errorlevel%

robocopy runtime dist\DownloadNFe55\runtime /E >nul
if errorlevel 8 exit /b %errorlevel%

mkdir package >nul 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'dist\DownloadNFe55\*' -DestinationPath 'package\DownloadNFe55-windows-portable.zip' -Force" || exit /b 1

echo.
echo Pacote portatil criado em package\DownloadNFe55-windows-portable.zip
