# performance-optimization Specification

## Purpose
TBD - created by archiving change refactor-smart-wait-adoption. Update Purpose after archive.
## Requirements
### Requirement: 智慧等待機制全面應用

系統 SHALL 使用智慧等待方法替代所有固定時間等待，以提升執行效率和使用者體驗。

#### Scenario: 頁面導航後智慧等待

- **WHEN** 系統執行頁面導航操作（如點擊連結、提交表單）
- **THEN** 系統 SHALL 使用 `smart_wait_for_url_change()` 等待 URL 變化
- **AND** 系統 SHALL NOT 使用固定的 `time.sleep()` 等待
- **AND** 當 URL 變化發生時立即繼續執行，不浪費額外時間

#### Scenario: AJAX 請求後智慧等待

- **WHEN** 系統觸發 AJAX 請求（如點擊搜尋按鈕、下載按鈕）
- **THEN** 系統 SHALL 使用 `smart_wait_for_ajax()` 等待 AJAX 完成
- **AND** 系統 SHALL 檢測 jQuery.active 或其他 AJAX 狀態指標
- **AND** 當 AJAX 完成時立即繼續執行

#### Scenario: 元素出現後智慧等待

- **WHEN** 系統需要等待特定元素出現或變為可點擊
- **THEN** 系統 SHALL 使用 `smart_wait_for_element()` 或 `smart_wait_for_clickable()`
- **AND** 系統 SHALL 以 0.5 秒頻率輪詢元素狀態
- **AND** 當元素符合條件時立即返回，不繼續等待

#### Scenario: 檔案下載完成智慧等待

- **WHEN** 系統觸發檔案下載
- **THEN** 系統 SHALL 使用 `smart_wait_for_file_download()` 檢測下載目錄
- **AND** 系統 SHALL 排除 .crdownload, .tmp, .part 等臨時檔案
- **AND** 當有效檔案出現時立即繼續處理

#### Scenario: 登入流程智慧等待

- **WHEN** 系統提交登入表單
- **THEN** 系統 SHALL 使用 `smart_wait_for_url_change()` 等待登入後跳轉
- **AND** 系統 SHALL NOT 使用固定的 5 秒等待
- **AND** 登入成功後立即進入下一步驟

### Requirement: 固定等待限制使用

系統 SHALL 僅在必要情況下使用固定時間等待 (`time.sleep()`)，並遵循以下原則。

#### Scenario: 允許的固定等待使用情況

- **WHEN** 需要避免過於頻繁的 API 請求（如帳號間隔）
- **THEN** 系統 MAY 使用固定等待
- **AND** 固定等待時間 SHALL NOT 超過 3 秒
- **AND** 必須在代碼註解中說明使用原因

#### Scenario: 禁止的固定等待使用

- **WHEN** 等待頁面載入、元素出現、AJAX 完成
- **THEN** 系統 SHALL NOT 使用 `time.sleep()`
- **AND** 系統 MUST 使用對應的智慧等待方法
- **AND** 代碼審查時 MUST 標記為需要修正

### Requirement: 執行效能提升

系統 SHALL 透過智慧等待機制達成可量測的效能提升目標。

#### Scenario: 單一帳號執行時間縮短

- **WHEN** 執行單一帳號的完整下載流程
- **THEN** 執行時間 SHALL 比優化前減少至少 40%
- **AND** 功能正確性 SHALL 維持 100%
- **AND** 下載檔案完整性 SHALL 不受影響

#### Scenario: 多帳號批次處理效能

- **WHEN** 執行 10 個帳號的批次處理
- **THEN** 總執行時間 SHALL 從 30 分鐘降至 18 分鐘以內
- **AND** 所有帳號 SHALL 成功完成處理
- **AND** 不發生因等待時間不足導致的錯誤

#### Scenario: 網路延遲適應性

- **WHEN** 網路延遲較高（如 >2 秒響應時間）
- **THEN** 智慧等待 SHALL 自動延長等待時間
- **AND** 系統 SHALL NOT 因固定等待時間不足而失敗
- **AND** 最終仍能成功完成操作

### Requirement: 等待邏輯一致性

系統 SHALL 在所有 scraper 中使用一致的等待策略和方法。

#### Scenario: 跨 Scraper 等待方法統一

- **WHEN** PaymentScraper, FreightScraper, UnpaidScraper 需要等待
- **THEN** 所有 scraper SHALL 使用 BaseScraper 提供的智慧等待方法
- **AND** SHALL NOT 各自實現重複的等待邏輯
- **AND** 等待超時時間設定 SHALL 保持一致（預設 10 秒）

#### Scenario: 等待失敗處理一致性

- **WHEN** 智慧等待超時或失敗
- **THEN** 系統 SHALL 記錄警告訊息到日誌
- **AND** 系統 SHALL 返回 None 或 False 表示失敗
- **AND** 呼叫方 SHALL 檢查返回值並適當處理失敗情況

