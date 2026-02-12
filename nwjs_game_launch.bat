@echo off

:: ────────────────────────────────────────────────
:: Configuración (ajusta estas líneas si cambias paths)
set "NW_EXE=%userprofile%\.NW.js\nw.exe"
set "PROFILE_DIR=%localappdata%\RPGM\User Data"
:: ────────────────────────────────────────────────

echo.
echo Preparando entorno RPG Maker (NW.js portable compartido)...

:: 1. Limpiar perfil/cache (borrar completamente la carpeta User Data)
if exist "%PROFILE_DIR%" (
    echo Limpiando cache/perfil anterior...
    rd /s /q "%PROFILE_DIR%" 2>nul
    if exist "%PROFILE_DIR%" (
        echo ADVERTENCIA: No se pudo borrar completamente la carpeta de perfil.
        echo Puede haber archivos en uso o permisos insuficientes.
    ) else (
        echo Cache limpiada correctamente.
    )
) else (
    echo No existia perfil anterior, continuando...
)

:: 2. Lanzar el juego usando el mismo perfil limpio
if not exist "%NW_EXE%" (
    echo ERROR: No se encuentra nw.exe en
    echo    %NW_EXE%
    echo Instala/actualiza NW.js portable en esa ubicación.
    pause
    exit /b 1
)

echo Iniciando juego...
start "" "%NW_EXE%" --user-data-dir="%PROFILE_DIR%" --nwapp "%CD%"

endlocal
exit /b 0