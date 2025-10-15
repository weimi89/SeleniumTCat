# Proposal: 全面採用智慧等待機制

## Why

目前程式碼中存在 **34+ 處固定等待** (`time.sleep()`)，導致不必要的時間浪費：
- 每個帳號平均浪費 2-3 分鐘等待時間
- 10 個帳號累計浪費 20-30 分鐘
- 使用者體驗差，無法即時反應頁面載入完成

雖然 `BaseScraper` 已實現完整的智慧等待機制 (`smart_wait` 系列方法)，但實際使用率不到 30%，大量固定等待仍在使用中。

## What Changes

- 替換所有 `time.sleep()` 調用為對應的智慧等待方法
- 優化等待策略，條件滿足時立即繼續執行
- 保持功能完全不變，僅提升執行效率
- 統一等待邏輯，提升代碼一致性

**修改範圍**：
- `src/scrapers/payment_scraper.py` - 15 處替換
- `src/scrapers/freight_scraper.py` - 8 處替換
- `src/scrapers/unpaid_scraper.py` - 6 處替換
- `src/core/base_scraper.py` - 5 處替換
- `src/core/multi_account_manager.py` - 1 處保留（帳號間隔）

**不改變**：
- ❌ 不修改任何業務邏輯
- ❌ 不改變現有 API 介面
- ❌ 不影響功能正確性

## Impact

### 預期效益
- ⚡ **執行時間減少 40-60%**：10 個帳號從 30 分鐘降至 12-18 分鐘
- ✅ **使用者體驗提升**：即時響應頁面載入，不再盲目等待
- 🔧 **代碼品質提升**：統一等待策略，符合最佳實踐
- 📊 **可維護性提升**：所有等待邏輯集中在 BaseScraper

### Affected Specs
- `specs/performance-optimization/spec.md` - 新增效能優化規範

### Affected Code
**核心修改**：
- `src/scrapers/payment_scraper.py:58,350,454,709,1051` - 關鍵等待點
- `src/scrapers/freight_scraper.py:74,178,188` - AJAX 等待
- `src/scrapers/unpaid_scraper.py:54,158,195` - 導航等待
- `src/core/base_scraper.py:290,446` - 登入流程等待

**測試需求**：
- 需要完整的端到端測試驗證
- 確保多帳號批次處理正常
- 驗證各種網路狀況下的穩定性

### Risk Assessment
- **風險等級**: 🟡 低-中 (不改變功能，但涉及等待邏輯)
- **回滾策略**: Git revert 即可完全恢復
- **測試要求**: 完整的端到端測試覆蓋所有 scraper

### Breaking Changes
- **無** - 這是純粹的效能優化，對外 API 保持不變
