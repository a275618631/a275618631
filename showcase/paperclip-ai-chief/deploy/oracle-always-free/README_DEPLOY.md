# 雲端部署與網路防護指引 (Oracle Cloud Always Free)

本指引說明如何在 Oracle Cloud Infrastructure (OCI) 的 Always Free Ampere A1 執行個體上安全部署 Paperclip AI Chief 團隊。

---

## 1. 架構特色
- **零公網暴露面**：透過 Linux 原生 UFW 防火牆全面阻絕外部連線至 3100 埠；所有管理與 Web 操作均透過 Tailscale 私有加密網路連線。
- **零額外雲端費用**：鎖定 OCI Always Free 規格（Ampere A1 ARM64，最高 4 OCPU / 24GB RAM，建議設定 2 OCPU / 6GB RAM），絕不超出免費額度。
- **安全憑證黑盒 (SECRET_BLACK_BOX)**：
  - 認證金鑰由系統自動生成隨機 Hex，絕不納入版本庫。
  - Codex 推論透過使用者的 ChatGPT Plus 訂閱於本機或雲端互動登入，不需儲存或暴露任何第三方 API 密鑰。

---

## 2. 部署操作流程

### 步驟 1：雲端執行個體建立
1. 登入 Oracle Cloud 主控台。
2. 建立專屬虛擬雲端網路 (VCN) 與公開子網路。
3. 建立運算執行個體 (Compute Instance)：
   - **作業系統**：Ubuntu 24.04 LTS / 22.04 LTS
   - **配置**：VM.Standard.A1.Flex (2 OCPU / 6GB RAM)
   - **網路**：指定指派公用 IP 位址（僅用於 SSH 連線）。

### 步驟 2：執行初始化安裝
透過 SSH 連線至主機後，執行自動化安裝腳本：
```bash
curl -fsSL https://raw.githubusercontent.com/a275618631/a275618631/main/showcase/paperclip-ai-chief/deploy/oracle-always-free/install-oracle-vm.sh | bash
```

### 步驟 3：設定私網連線 (Tailscale)
```bash
sudo tailscale up
```
依提示完成瀏覽器登入授權，取得該主機在 Tailscale 網路中的專屬 IP（如 `100.x.y.z`）。

### 步驟 4：啟動 Paperclip 容器
```bash
cd ~/paperclip-deploy
# 修改 .env 中的 PAPERCLIP_PUBLIC_URL 為 http://100.x.y.z:3100
docker compose -f docker-compose.oracle-arm64.yml up -d
```

### 步驟 5：排程備份與巡查
將備份腳本寫入 crontab：
```bash
(crontab -l 2>/dev/null; echo "0 3 * * * $HOME/paperclip-deploy/backup-db.sh") | crontab -
```
