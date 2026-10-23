@echo off
REM ====================================================================
REM  servir_presentacion.bat
REM  Sirve la carpeta 02_dashboards por HTTP y abre la presentacion.
REM
REM  Hace falta porque los navegadores (Chrome y Edge) NO permiten
REM  incrustar paginas locales dentro de un iframe cuando el archivo se
REM  abre con doble clic (protocolo file://). Sirviendolo por HTTP,
REM  los tres paneles se cargan dentro de presentacion.html.
REM
REM  Uso: doble clic. Se abre una ventana con el servidor y el navegador
REM       en http://localhost:8000/presentacion.html
REM  Para detenerlo: cierra la ventana "Servidor de la presentacion".
REM ====================================================================
setlocal
title Observatorio MinCiencias - presentacion
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [x] No se encontro "python" en el PATH.
  echo     Instala Python 3 o ejecuta este archivo desde una consola con Python.
  echo.
  pause
  exit /b 1
)

if not exist "presentacion.html" (
  echo [x] No se encuentra presentacion.html en esta carpeta:
  echo     %~dp0
  echo.
  pause
  exit /b 1
)

echo Sirviendo la carpeta 02_dashboards en http://localhost:8000
echo Se abrira el navegador en http://localhost:8000/presentacion.html
echo Para detener el servidor, cierra la ventana "Servidor de la presentacion".
echo.

start "Servidor de la presentacion" cmd /k python -m http.server 8000 --bind 127.0.0.1
timeout /t 3 /nobreak >nul
start "" "http://localhost:8000/presentacion.html"

exit /b 0
