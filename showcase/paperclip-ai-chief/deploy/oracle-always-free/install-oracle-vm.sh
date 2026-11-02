#!/usr/bin/env bash
# ==============================================================================
# Oracle Cloud Always Free (Ubuntu ARM64) 初始化與防護腳本
# 規範守則：零額外計費、無公網暴露、Tailscale 私網存取、手動登入認證
# ==============================================================================
set -euo pipefail

echo "==> [1/5] 檢查硬體架構與資源邊界..."
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "arm64" ]; then
    echo "提示: 目前主機架構為 $ARCH，建議使用 ARM64 (Ampere A1) 架構。"
fi

TOTAL_MEM_MB=$(free -m | awk '/^Mem:/{print $2}')
echo "檢測到總記憶體: ${TOTAL_MEM_MB} MB"

echo "==> [2/5] 更新套件庫並安裝基礎工具 (Docker, Tailscale, Curl, Git)..."
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg lsb-release git openssl cron

# 安裝 Docker CE
if ! command -v docker &> /dev/null; then
    echo "安裝 Docker CE..."
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker "$USER"
fi

# 安裝 Tailscale 私網工具
if ! command -v tailscale &> /dev/null; then
    echo "安裝 Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
fi

echo "==> [3/5] 建立安全工作目錄..."
DEPLOY_DIR="$HOME/paperclip-deploy"
mkdir -p "$DEPLOY_DIR/data"
mkdir -p "$DEPLOY_DIR/backups"
cd "$DEPLOY_DIR"

if [ ! -f .env ]; then
    RAND_SECRET=$(openssl rand -hex 32)
    cat <<EOF > .env
PAPERCLIP_PORT=3100
PAPERCLIP_DEPLOYMENT_MODE=authenticated
PAPERCLIP_DEPLOYMENT_EXPOSURE=private
PAPERCLIP_PUBLIC_URL=http://localhost:3100
BETTER_AUTH_SECRET=${RAND_SECRET}
EOF
    echo "已自動生成隨機安全金鑰 BETTER_AUTH_SECRET。"
fi

echo "==> [4/5] 設定 UFW 防火牆 (僅允許 SSH 與 Tailscale，嚴格阻絕公網 3100)..."
if command -v ufw &> /dev/null; then
    sudo ufw allow OpenSSH
    sudo ufw allow in on tailscale0
    sudo ufw deny 3100/tcp || true
    sudo ufw --force enable || true
fi

echo "=========================================================================="
echo "==> 初始化環境配置完成！"
echo "請依序執行以下手動驗證步驟："
echo "1. 執行 'sudo tailscale up' 登入專屬私有網路並取得私網 IP。"
echo "2. 更新 .env 中的 PAPERCLIP_PUBLIC_URL 為 'http://<您的-Tailscale-IP>:3100'。"
echo "3. 執行 'docker compose -f docker-compose.oracle-arm64.yml up -d' 啟動核心服務。"
echo "4. 在雲端環境執行官方 Codex 登入流程（由您手動進行 ChatGPT 登入）。"
echo "=========================================================================="
