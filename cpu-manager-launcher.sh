#!/bin/sh
# When launched through the desktop entry with sudo, keep the logged-in
# desktop user's settings so tray-enabled startup behaves as configured.
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != root ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    if [ -n "$USER_HOME" ]; then
        export XDG_CONFIG_HOME="$USER_HOME/.config"
    fi
fi
exec /usr/bin/python3 /usr/share/cpu-manager/main.py "$@"
