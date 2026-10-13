#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

sudo apt-get update
sudo apt-get install -y python3 python3-pyside6.qtwidgets python3-psutil

echo
echo "Installation abgeschlossen."
echo "Starten: ./start_cpu_manager.sh"
echo "Mit Administratorrechten (nur wenn nötig): ./start_cpu_manager.sh --admin"
