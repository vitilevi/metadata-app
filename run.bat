@echo off
rem Duplo clique neste arquivo abre o app no Windows.
setlocal
cd /d "%~dp0"

rem --- Python -------------------------------------------------------------
set "PY_CMD="
where py >nul 2>&1 && set "PY_CMD=py -3"
if not defined PY_CMD (
  where python >nul 2>&1 && set "PY_CMD=python"
)
if not defined PY_CMD (
  echo Python 3 nao encontrado.
  echo Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH".
  pause
  exit /b 1
)

rem --- Tkinter ------------------------------------------------------------
%PY_CMD% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
  echo Este Python nao tem Tkinter instalado.
  echo Reinstale o Python oficial marcando a opcao "tcl/tk and IDLE".
  pause
  exit /b 1
)

rem --- ExifTool -----------------------------------------------------------
where exiftool >nul 2>&1
if errorlevel 1 (
  if exist "%~dp0exiftool\exiftool.exe" goto :run
  echo ExifTool nao encontrado. Tentando instalar via winget...
  winget install -e --id OliverBetz.ExifTool --accept-source-agreements --accept-package-agreements
  where exiftool >nul 2>&1
  if errorlevel 1 (
    echo.
    echo Nao foi possivel instalar automaticamente.
    echo Baixe em https://exiftool.org, renomeie "exiftool^(-k^).exe" para "exiftool.exe"
    echo e coloque em: %~dp0exiftool\
    pause
    exit /b 1
  )
)

:run
rem pyw/pythonw abrem o app sem janela de console; se faltarem, usa o console.
set "PYW_CMD="
where pyw >nul 2>&1 && set "PYW_CMD=pyw -3"
if not defined PYW_CMD (
  where pythonw >nul 2>&1 && set "PYW_CMD=pythonw"
)
if defined PYW_CMD (
  start "" %PYW_CMD% app.py
) else (
  %PY_CMD% app.py
)
endlocal
