#!/bin/bash

# === UTA PWYW Recovery & Restart Script ===
# Description: Recovers and restarts the Gunicorn service for UTA PWYW app.
# Author: Richard Igwegbu

APP_DIR="/var/www/uta_pwyw_starter"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="pwyw"
GUNICORN_BIN="$VENV_DIR/bin/gunicorn"
PYTHON_BIN="$VENV_DIR/bin/python3"
REQUIREMENTS="$APP_DIR/requirements.txt"

log() {
  echo -e "[INFO] $1"
}

error() {
  echo -e "[ERROR] $1" >&2
  exit 1
}

log "Navigating to app directory..."
cd "$APP_DIR" || error "App directory not found."

log "Ensuring Python virtual environment is active..."
source "$VENV_DIR/bin/activate" || error "Failed to activate venv."

log "Reinstalling required packages..."
pip install --upgrade pip >/dev/null 2>&1
pip install -r "$REQUIREMENTS" || error "Failed to install dependencies."

log "Checking Gunicorn binary permissions..."
sudo chmod +x "$GUNICORN_BIN" || error "Failed to set execute permission."

log "Reloading systemd and restarting service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl stop "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

log "Waiting for Gunicorn service to become active..."
sleep 2

STATUS=$(systemctl is-active "$SERVICE_NAME")
if [[ "$STATUS" == "active" ]]; then
  log "✅ $SERVICE_NAME is running successfully."
else
  error "❌ $SERVICE_NAME failed to start. Check logs."
fi

