#!/bin/bash
# Macでダブルクリックすると起動するスクリプト。
# 初回だけ必要なライブラリを .venv にインストールする（数分かかります）。
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 が見つかりません。README.md の「準備」を参照してインストールしてください。"
  read -r -p "Enterキーで閉じます"
  exit 1
fi

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
  echo "Python 3.10 以上が必要です（現在: $(python3 --version)）。README.md の「準備」を参照してください。"
  read -r -p "Enterキーで閉じます"
  exit 1
fi

if [ ! -f .venv/.installed ] || [ requirements.txt -nt .venv/.installed ]; then
  echo "初回セットアップ中です（数分かかります）…"
  python3 -m venv .venv || { read -r -p "仮想環境の作成に失敗しました。Enterキーで閉じます"; exit 1; }
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  .venv/bin/python -m pip install -r requirements.txt || { read -r -p "インストールに失敗しました。Enterキーで閉じます"; exit 1; }
  touch .venv/.installed
fi

exec .venv/bin/python app.py "$@"
