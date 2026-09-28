@echo off
setlocal

where python >nul 2>nul || (
    echo Python nao encontrado.
    exit /b 1
)

where php >nul 2>nul || (
    echo PHP nao encontrado.
    exit /b 1
)

where composer >nul 2>nul || (
    echo Composer nao encontrado.
    exit /b 1
)

composer install --no-dev --optimize-autoloader || exit /b 1
python -m pip install --upgrade pyinstaller || exit /b 1

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name DownloadNFe55 ^
  --add-data "php;php" ^
  --add-data "vendor;vendor" ^
  app.py

echo.
echo Executavel criado em dist\DownloadNFe55\DownloadNFe55.exe
