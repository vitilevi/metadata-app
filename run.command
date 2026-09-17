#!/bin/bash
# Duplo clique neste arquivo abre o app.
cd "$(dirname "$0")" || exit 1

if ! command -v exiftool >/dev/null 2>&1; then
  echo "ExifTool não encontrado. Instalando via Homebrew…"
  brew install exiftool || {
    echo "Falha ao instalar. Rode manualmente: brew install exiftool"
    read -r -p "Enter para sair"
    exit 1
  }
fi

exec python3 app.py
