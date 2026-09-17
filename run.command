#!/bin/bash
# macOS: duplo clique neste arquivo abre o app.
# Linux: rode com  bash run.command
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 não encontrado. Instale-o e rode de novo."
  read -r -p "Enter para sair"
  exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
  echo "Este Python não tem Tkinter."
  echo "macOS: instale o Python oficial de python.org."
  echo "Linux: sudo apt install python3-tk"
  read -r -p "Enter para sair"
  exit 1
fi

if ! command -v exiftool >/dev/null 2>&1; then
  echo "ExifTool não encontrado. Tentando instalar…"
  if command -v brew >/dev/null 2>&1; then
    brew install exiftool
  elif command -v apt >/dev/null 2>&1; then
    sudo apt install -y libimage-exiftool-perl
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y perl-Image-ExifTool
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm perl-image-exiftool
  fi

  if ! command -v exiftool >/dev/null 2>&1; then
    echo "Falha ao instalar. Instale manualmente e rode de novo."
    read -r -p "Enter para sair"
    exit 1
  fi
fi

exec python3 app.py
