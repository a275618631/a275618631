# 工廠設備知識庫與地端診斷助手

設備警報發生時，工程師需要在大量手冊中查詢代碼、規格與處理方式。難點不只是「找得到」，還要確定**查到的是正確設備與版本，而且每項建議都有文件依據**。

我把 SQLite FTS5、Qdrant Local、語意檢索與重排序組成混合檢索流程，最後再檢查來源、數值、衝突與證據不足的情況。系統的原則很清楚：沒有可靠依據的操作建議，不應直接交給現場人員。

## 系統怎麼處理查詢

```text
輸入設備代碼或故障描述
      ↓
SQLite FTS5 精確搜尋 + Qdrant Local 語意搜尋
      ↓
RRF 融合檢索結果 + BGE Reranker
      ↓
比對手冊引用、數值與適用條件
      ↓
有依據：回傳可查證資訊
證據不足或衝突：ABSTAIN
```

## 實作重點

- **精確搜尋與語意檢索一起使用**：設備 Alarm Code、Tag 適合全文搜尋；不同說法的故障描述則由向量檢索補足。
- **引用可以回查**：結果附帶文件來源，讓使用者能核對原文。
- **確定性驗證**：以 [core/verifier.py](core/verifier.py) 檢查數值、引用、衝突和不受支持的建議。
- **本地執行設計**：資料檢索以本地元件運作，避免把實際設備資料當作一般聊天內容直接傳出。

## 測試與成果

既有合成基準包含 **12 份自編設備手冊及 25 題故障診斷案例**。該組基準的安全規則檢查紀錄為 **25／25**，沒有觀察到未授權操作建議；這是該組資料和測試規則的結果，不代表所有設備情境的通用準確率。

程式與測試可從 [檢索測試](tests/test_mvp1_retrieval.py)、[本地 Qdrant 測試](tests/test_sprint2_qdrant.py) 和 [驗證核心](core/verifier.py) 開始閱讀。

## 如何查看公開版本

這個目錄已包含 Python 原始碼、[套件設定](pyproject.toml)、[相依清單](requirements.txt)及合成測試。可以在 Python 3.11 以上的環境先安裝必要套件，再執行對應測試：

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests/test_mvp1_retrieval.py tests/test_sprint2_qdrant.py
```

部分模型或測試資料可能需要額外準備，實際結果以環境與測試程式為準。本次 README 修改沒有重新執行測試。

這份公開副本以合成文件與可公開程式為主，不附原廠手冊 PDF，也不會直接控制現場 PLC／SCADA。詳細設計與歷史驗證可接著閱讀專案內的 `docs/` 與 `reports/`。
