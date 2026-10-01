@echo off
title Compilar ProgramasV3 - Comercial Depor
color 0B
echo.
echo =====================================================
echo   Compilando ProgramasV3.pyw
echo =====================================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    pause & exit /b 1
)

:: Verificar PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller --quiet
)

:: ==========================================================
:: Rutas RELATIVAS a este .bat, para que nada se rompa si se
:: mueve la carpeta del proyecto.
::   %~dp0  = ...\_Desarrollo\programa-depor\app\
::   FUENTE = la carpeta raiz del proyecto
:: ==========================================================
pushd "%~dp0..\..\.." >nul
set "RAIZ=%CD%"
popd >nul
set "ICONO=%~dp0depor.ico"
set "SCRIPT=%~dp0ProgramasV3.pyw"

echo Carpeta raiz detectada: %RAIZ%
echo.

:: Limpiar compilaciones anteriores
echo Limpiando archivos temporales anteriores...
if exist "build"           rmdir /s /q "build"
if exist "dist"            rmdir /s /q "dist"
if exist "ProgramasV3.spec" del /q "ProgramasV3.spec"

echo.
echo Compilando - esto puede tardar 1-2 minutos...
echo.

:: OJO: PyInstaller 6.x exige --add-data con el signo = pegado.
:: La forma antigua (--add-data "ruta;.") falla con:
::   "Wrong syntax, should be --add-data=SOURCE:DEST"
:: Desde la version 4.0 la interfaz es pywebview: la carpeta ui\ (HTML/CSS/JS)
:: va DENTRO del exe y depor_ui\ se incluye sola porque el .pyw la importa.
:: Requisitos: pip install pywebview rarfile pyinstaller
:: Catalogo y permiso de los instaladores (no estan en el repositorio publico; ver herramientas\).
:: Sin ellos el programa compila igual, pero sin pendrive solo baja los gratuitos.
set EXTRA=
if exist "%~dp0catalogo_instaladores.json" set EXTRA=%EXTRA% --add-data="%~dp0catalogo_instaladores.json;."
if exist "%~dp0acceso_instaladores.json" set EXTRA=%EXTRA% --add-data="%~dp0acceso_instaladores.json;."
pyinstaller --noconfirm --onefile --windowed --icon="%ICONO%" --uac-admin --add-data="%ICONO%;." --add-data="%~dp0ui;ui" %EXTRA% --exclude-module tkinter --exclude-module PyQt6 --exclude-module PyQt5 --exclude-module PySide6 --exclude-module qtpy --exclude-module setuptools --exclude-module numpy "%SCRIPT%"

echo.

:: Verificar si se generó el exe
if exist "dist\ProgramasV3.exe" (
    echo Copiando ProgramasV3.exe a la carpeta raiz...

    :: Una sola copia: la de la raiz. Antes tambien se copiaba a "output",
    :: que era exactamente el mismo archivo duplicado.
    copy /Y "dist\ProgramasV3.exe" "%RAIZ%\ProgramasV3.exe" >nul

    if errorlevel 1 (
        echo [ERROR] No se pudo copiar el archivo. Verifica que no este abierto.
    ) else (
        echo.
        echo =====================================================
        echo   [OK] ProgramasV3.exe actualizado correctamente
        echo   En: %RAIZ%\
        echo =====================================================
    )

    :: Limpiar temporales
    rmdir /s /q "build" 2>nul
    rmdir /s /q "dist"  2>nul
    del /q "ProgramasV3.spec" 2>nul

) else (
    echo =====================================================
    echo   [ERROR] No se genero el EXE.
    echo   Revisa los mensajes de error arriba.
    echo =====================================================
)

echo.
pause
