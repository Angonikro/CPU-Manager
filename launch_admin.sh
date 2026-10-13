#!/bin/sh
# Preserve the active graphical session for the elevated Qt process.
# Errors are logged because this launcher intentionally has no terminal.
LOG="${XDG_CACHE_HOME:-$HOME/.cache}/cpu-manager-admin.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || LOG="/tmp/cpu-manager-admin.log"
ENV_ARGS=""
[ -n "${DISPLAY:-}" ] && ENV_ARGS="$ENV_ARGS DISPLAY=$DISPLAY"
[ -n "${XAUTHORITY:-}" ] && ENV_ARGS="$ENV_ARGS XAUTHORITY=$XAUTHORITY"
[ -n "${WAYLAND_DISPLAY:-}" ] && ENV_ARGS="$ENV_ARGS WAYLAND_DISPLAY=$WAYLAND_DISPLAY"
[ -n "${XDG_RUNTIME_DIR:-}" ] && ENV_ARGS="$ENV_ARGS XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ] && ENV_ARGS="$ENV_ARGS DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS"
[ -n "${QT_QPA_PLATFORM:-}" ] && ENV_ARGS="$ENV_ARGS QT_QPA_PLATFORM=$QT_QPA_PLATFORM"
# Intentional word splitting turns the session variables into env assignments.
# Values containing spaces are unusual for these variables; DISPLAY/socket paths do not contain spaces.
# shellcheck disable=SC2086
exec pkexec /usr/bin/env $ENV_ARGS /usr/bin/python3 /usr/share/cpu-manager/main.py "$@" >>"$LOG" 2>&1
