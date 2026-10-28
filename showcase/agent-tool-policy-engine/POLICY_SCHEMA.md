# Policy Schema

## Defaults

`policies/policy.toml` 的 `[defaults]` 可設定：

- `readonly`
- `local_write`
- `external`
- `destructive`
- `critical`
- `unknown`

值只能是 `allow`、`allow_scoped`、`require_approval`、`deny`。

## Resources

`[resources]` 支援：

- `allowed_paths`
- `allowed_repos`
- `allowed_branches`
- `allowed_domains`
- `protected_branches`

路徑使用平台原生分隔符或 `/`；比較前會正規化。Repo 與 domain 會轉小寫，branch 會移除 `refs/heads/`。

`allowed_paths` 可使用 `${PROJECT_ROOT}` 代表 policy 檔案所在專案根目錄，避免把開發者本機絕對路徑帶入 CI 或其他環境；其他絕對路徑仍會原樣保留。

## Rules

`[[rules]]` 可使用 `id`、`tool`、`operation`、`repos`、`branches`、`domains`、`side_effects` 與 `decision`。規則依檔案順序取第一個符合者；沒有符合者時使用 defaults。

注意：`allow_scoped` 只有在 path、repo+branch 或 domain 真正命中 allowlist 時成立，否則降級為 `require_approval`。`critical` 與 protected branch 的 deny 不能被 prompt override 放寬。
