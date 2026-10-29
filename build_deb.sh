#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
VERSION="1.1.5"
ROOT="$(mktemp -d)"
trap 'rm -rf "$ROOT"' EXIT
mkdir -p "$ROOT/DEBIAN" "$ROOT/usr/bin" "$ROOT/usr/share/applications" "$ROOT/usr/share/cpu-manager/cpu_manager" "$ROOT/etc/sudoers.d"
cat > "$ROOT/DEBIAN/control" <<CONTROL
Package: cpu-manager
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Maintainer: CPU Manager Project
Depends: sudo, python3, python3-pyside6.qtwidgets, python3-psutil, python3-gi, gir1.2-gtk-3.0
Description: CPU and process monitor for Raspberry Pi and Linux with GTK tray icon
 PySide6 desktop application with configurable sampling, RAM/swap/load, CPU hardware information and GTK system tray.
CONTROL
cat > "$ROOT/usr/bin/cpu-manager" <<'LAUNCH'
#!/bin/sh
# Preserve the logged-in desktop user's settings when started with sudo.
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != root ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    if [ -n "$USER_HOME" ]; then
        export XDG_CONFIG_HOME="$USER_HOME/.config"
    fi
fi
exec /usr/bin/python3 /usr/share/cpu-manager/main.py "$@"
LAUNCH
cp main.py "$ROOT/usr/share/cpu-manager/main.py"
cp cpu_manager/*.py "$ROOT/usr/share/cpu-manager/cpu_manager/"
cat > "$ROOT/usr/share/applications/cpu-manager.desktop" <<'DESKTOP'
[Desktop Entry]
Name=CPU Manager
Comment=CPU and process monitor
Exec=sudo /usr/bin/cpu-manager
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=System;Monitor;
DESKTOP
chmod 755 "$ROOT/usr/bin/cpu-manager"
cat > "$ROOT/etc/sudoers.d/cpu-manager" <<'SUDOERS'
# Permit launching CPU Manager without a password; limited to this executable.
%sudo ALL=(root) NOPASSWD: /usr/bin/cpu-manager
SUDOERS
chmod 0440 "$ROOT/etc/sudoers.d/cpu-manager"
cat > "$ROOT/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if command -v visudo >/dev/null 2>&1; then
    visudo -cf /etc/sudoers.d/cpu-manager >/dev/null
fi
exit 0
POSTINST
chmod 755 "$ROOT/DEBIAN/postinst"
cat > "$ROOT/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
if [ "$1" = purge ]; then
    rm -f /etc/sudoers.d/cpu-manager
fi
exit 0
POSTRM
chmod 755 "$ROOT/DEBIAN/postrm"
mkdir -p dist
dpkg-deb --root-owner-group --build "$ROOT" "dist/cpu-manager_${VERSION}_all.deb"
echo "Created dist/cpu-manager_${VERSION}_all.deb"
