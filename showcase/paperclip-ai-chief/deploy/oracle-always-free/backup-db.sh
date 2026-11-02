#!/usr/bin/env bash
# ==============================================================================
# Paperclip 資料備份腳本 (保留最近 7 天，排除認證金鑰與機敏資料)
# ==============================================================================
set -euo pipefail

BACKUP_DIR="$HOME/paperclip-deploy/backups"
DATA_DIR="$HOME/paperclip-deploy/data"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TARGET_ARCHIVE="$BACKUP_DIR/paperclip_backup_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "==> 開始封裝 Paperclip 資料 (嚴格排除 secrets 與憑證檔案)..."
tar --exclude="*.key" \
    --exclude="*auth*.json" \
    --exclude=".env" \
    -czf "$TARGET_ARCHIVE" -C "$DATA_DIR" .

echo "==> 備份完成: $TARGET_ARCHIVE"

# 保留最近 7 天備份，清理過期檔案
find "$BACKUP_DIR" -name "paperclip_backup_*.tar.gz" -mtime +7 -delete
echo "==> 歷史備份輪轉清理完畢。"
