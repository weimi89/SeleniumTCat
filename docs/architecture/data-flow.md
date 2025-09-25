# SeleniumTCat 資料流程設計

## 資料流程概覽

SeleniumTCat 的資料流程涵蓋從使用者配置到最終檔案輸出的完整生命週期。系統設計了多層次的資料處理機制，確保資料的完整性、一致性和可追溯性。

```mermaid
flowchart TD
    subgraph "配置階段"
        ConfigFile[accounts.json<br/>使用者配置]
        EnvFile[.env<br/>環境變數]
        Settings[設定檔載入<br/>和驗證]
    end

    subgraph "初始化階段"
        MAM[MultiAccountManager<br/>管理器初始化]
        AccountList[啟用帳號列表<br/>提取]
    end

    subgraph "執行階段"
        Loop{遍歷每個帳號}
        Scraper[建立 Scraper<br/>實例]
        Browser[瀏覽器初始化]
        Login[登入流程]
        Navigate[頁面導航]
        DataExtract[資料抓取]
        FileDownload[檔案下載]
    end

    subgraph "後處理階段"
        FileRename[檔案重新命名]
        FileMove[移動到最終目錄]
        Cleanup[清理臨時檔案]
        Report[生成執行報告]
    end

    ConfigFile --> Settings
    EnvFile --> Settings
    Settings --> MAM
    MAM --> AccountList
    AccountList --> Loop
    Loop --> Scraper
    Scraper --> Browser
    Browser --> Login
    Login --> Navigate
    Navigate --> DataExtract
    DataExtract --> FileDownload
    FileDownload --> FileRename
    FileRename --> FileMove
    FileMove --> Cleanup
    Cleanup --> Report
    Report --> Loop
```

## 詳細資料流程分析

### 1. 配置載入和驗證流程

#### 1.1 配置檔案結構
```json
{
  "accounts": [
    {
      "username": "帳號1",
      "password": "密碼1",
      "enabled": true
    }
  ],
  "settings": {
    "headless": false,
    "download_base_dir": "downloads"
  }
}
```

#### 1.2 配置載入流程
```mermaid
sequenceDiagram
    participant User as 使用者
    participant Script as 執行腳本
    participant MAM as MultiAccountManager
    participant Config as 配置檔案

    User->>Script: 執行命令
    Script->>MAM: 建立管理器實例
    MAM->>Config: 讀取 accounts.json
    Config->>MAM: 回傳配置資料

    alt 配置檔案不存在
        MAM->>User: 拋出 FileNotFoundError
    else 配置格式錯誤
        MAM->>User: 拋出 ValueError
    else 配置載入成功
        MAM->>MAM: 驗證配置完整性
        MAM->>MAM: 提取啟用帳號列表
    end
```

### 2. 多帳號批次處理流程

#### 2.1 帳號處理順序
```mermaid
flowchart LR
    Start[開始] --> GetAccounts[獲取啟用帳號]
    GetAccounts --> Loop{還有帳號?}
    Loop -->|是| ProcessAccount[處理當前帳號]
    ProcessAccount --> Success{處理成功?}
    Success -->|是| RecordSuccess[記錄成功結果]
    Success -->|否| RecordError[記錄錯誤結果]
    RecordSuccess --> Wait[等待 3 秒]
    RecordError --> Wait
    Wait --> Loop
    Loop -->|否| GenerateReport[生成總結報告]
    GenerateReport --> End[結束]
```

#### 2.2 個別帳號處理流程
```mermaid
sequenceDiagram
    participant MAM as MultiAccountManager
    participant Scraper as PaymentScraper
    participant Browser as Chrome Browser
    participant Website as 黑貓宅急便網站

    MAM->>Scraper: 建立 Scraper 實例
    Scraper->>Browser: 初始化瀏覽器
    Browser-->>Scraper: 瀏覽器就緒

    Scraper->>Website: 前往登入頁面
    Website-->>Scraper: 載入登入頁面

    loop 最多 3 次重試
        Scraper->>Website: 填寫登入表單
        Scraper->>Website: 提交表單
        Website-->>Scraper: 登入回應

        alt 登入成功
            break 跳出重試迴圈
        else 登入失敗
            Scraper->>Scraper: 準備重試
        end
    end

    alt 登入最終成功
        Scraper->>Website: 導航到查詢頁面
        Scraper->>Website: 執行資料查詢
        Website-->>Scraper: 回傳查詢結果
        Scraper->>Website: 下載檔案
        Website-->>Scraper: 下載完成
        Scraper->>Scraper: 檔案後處理
        Scraper-->>MAM: 回傳成功結果
    else 登入失敗
        Scraper-->>MAM: 回傳失敗結果
    end

    Scraper->>Browser: 關閉瀏覽器
```

### 3. 登入和驗證碼處理流程

#### 3.1 登入流程詳解
```mermaid
flowchart TD
    Start[開始登入] --> LoadPage[載入登入頁面]
    LoadPage --> FillForm[填寫表單]

    subgraph "表單填寫"
        FillUsername[填入帳號]
        FillPassword[填入密碼]
        HandleCaptcha[處理驗證碼]
        SelectContract[選擇契約客戶專區]
    end

    FillForm --> FillUsername
    FillUsername --> FillPassword
    FillPassword --> HandleCaptcha
    HandleCaptcha --> SelectContract

    subgraph "驗證碼處理"
        CaptureImg[截取驗證碼圖片]
        OCRProcess[ddddocr 識別]
        OCRSuccess{識別成功?}
        FillCaptcha[填入驗證碼]
        ManualInput[等待手動輸入]
    end

    HandleCaptcha --> CaptureImg
    CaptureImg --> OCRProcess
    OCRProcess --> OCRSuccess
    OCRSuccess -->|是| FillCaptcha
    OCRSuccess -->|否| ManualInput
    FillCaptcha --> SelectContract
    ManualInput --> SelectContract

    SelectContract --> Submit[提交表單]
    Submit --> CheckAlerts{檢查彈窗}

    CheckAlerts -->|密碼安全警告| SecurityWarning[記錄安全警告]
    CheckAlerts -->|其他提示| AcceptAlert[接受提示]
    CheckAlerts -->|無彈窗| CheckSuccess[檢查登入狀態]

    SecurityWarning --> LoginFailed[登入失敗]
    AcceptAlert --> CheckSuccess

    CheckSuccess --> Success{登入成功?}
    Success -->|是| LoginSuccess[登入成功]
    Success -->|否| RetryCheck{還有重試次數?}

    RetryCheck -->|是| LoadPage
    RetryCheck -->|否| LoginFailed
```

#### 3.2 ddddocr 驗證碼識別流程
```python
def solve_captcha(self, captcha_img_element):
    """驗證碼識別流程"""
    # 1. 截取驗證碼圖片
    screenshot = captcha_img_element.screenshot_as_png

    # 2. ddddocr 識別
    result = self.ocr.classification(screenshot)

    # 3. 結果驗證
    if result and len(result) >= 4:  # 通常為 4 位數字
        return result
    else:
        return None  # 識別失敗
```

### 4. 資料抓取和下載流程

#### 4.1 通用資料抓取流程
```mermaid
flowchart TD
    StartQuery[開始查詢] --> Navigate[導航到查詢頁面]
    Navigate --> SetParams[設定查詢參數]

    subgraph "查詢參數設定"
        SetDateRange[設定日期範圍]
        SelectPeriod[選擇結算期間]
        FillSearchForm[填寫搜尋表單]
    end

    SetParams --> SetDateRange
    SetDateRange --> SelectPeriod
    SelectPeriod --> FillSearchForm

    FillSearchForm --> ExecuteSearch[執行搜尋]
    ExecuteSearch --> WaitResults[等待結果載入]
    WaitResults --> CheckResults{有結果?}

    CheckResults -->|是| FindDownloadBtn[尋找下載按鈕]
    CheckResults -->|否| NoDataResult[無資料結果]

    FindDownloadBtn --> ClickDownload[點擊下載]
    ClickDownload --> WaitDownload[等待下載完成]
    WaitDownload --> VerifyFiles[驗證下載檔案]

    VerifyFiles --> Success{下載成功?}
    Success -->|是| PostProcess[後處理檔案]
    Success -->|否| DownloadFailed[下載失敗]

    PostProcess --> RenameFiles[重新命名檔案]
    RenameFiles --> MoveFiles[移動到最終目錄]
    MoveFiles --> CleanupTemp[清理臨時檔案]
    CleanupTemp --> DownloadSuccess[下載成功]
```

#### 4.2 PaymentScraper 特化流程
```mermaid
sequenceDiagram
    participant PS as PaymentScraper
    participant Web as 網站
    participant FileSystem as 檔案系統

    PS->>Web: 導航到貨到付款查詢頁面
    Web-->>PS: 頁面載入完成

    PS->>Web: 尋找 ddlDate 選單
    Web-->>PS: 回傳期間選項

    PS->>PS: 解析可用期間
    PS->>PS: 選擇前 N 期

    loop 對每個期間
        PS->>Web: 選擇當前期間
        PS->>Web: 執行搜尋
        Web-->>PS: 回傳搜尋結果

        PS->>Web: 點擊對帳單下載按鈕
        Web-->>PS: 開始檔案下載

        PS->>FileSystem: 等待檔案出現在臨時目錄
        FileSystem-->>PS: 檔案下載完成

        PS->>FileSystem: 重新命名檔案
        PS->>FileSystem: 移動到最終目錄
    end

    PS->>FileSystem: 清理臨時檔案
```

### 5. 檔案管理流程

#### 5.1 檔案生命週期
```mermaid
stateDiagram-v2
    [*] --> TempCreated: 建立 UUID 臨時目錄
    TempCreated --> Downloading: 瀏覽器下載檔案
    Downloading --> Downloaded: 檔案下載完成
    Downloaded --> Renamed: 重新命名檔案
    Renamed --> Moved: 移動到最終目錄
    Moved --> TempCleaned: 清理臨時目錄
    TempCleaned --> [*]: 流程完成

    state "臨時檔案狀態" as TempState {
        [*] --> temp/uuid/原始檔名.xlsx
        temp/uuid/原始檔名.xlsx --> temp/uuid/重命名檔名.xlsx
    }

    state "最終檔案狀態" as FinalState {
        [*] --> downloads/重命名檔名.xlsx
        downloads/重命名檔名.xlsx --> [*]
    }
```

#### 5.2 檔案命名規則
```python
# PaymentScraper 檔案命名
filename_pattern = "客樂得對帳單_{username}_{period}.xlsx"

# FreightScraper 檔案命名
filename_pattern = "發票明細_{username}_{invoice_date}_{invoice_number}.xlsx"

# UnpaidScraper 檔案命名
filename_pattern = "交易明細表_{username}_{start_date}-{end_date}.xlsx"
```

### 6. 錯誤處理和恢復機制

#### 6.1 錯誤處理流程
```mermaid
flowchart TD
    Error[發生錯誤] --> ErrorType{錯誤類型}

    ErrorType -->|會話超時| SessionTimeout[會話超時處理]
    ErrorType -->|驗證碼錯誤| CaptchaRetry[驗證碼重試]
    ErrorType -->|密碼安全警告| SecurityWarning[安全警告處理]
    ErrorType -->|網路錯誤| NetworkError[網路錯誤處理]
    ErrorType -->|其他錯誤| GeneralError[一般錯誤處理]

    SessionTimeout --> Relogin[重新登入]
    Relogin --> Success1{恢復成功?}
    Success1 -->|是| Continue[繼續執行]
    Success1 -->|否| RecordError1[記錄錯誤]

    CaptchaRetry --> RetryLogin[重試登入]
    RetryLogin --> RetryCount{重試次數?}
    RetryCount -->|< 3 次| Continue
    RetryCount -->|>= 3 次| RecordError2[記錄錯誤]

    SecurityWarning --> TerminateAccount[終止帳號處理]
    TerminateAccount --> RecordSecurityError[記錄安全錯誤]

    NetworkError --> RetryRequest[重試請求]
    RetryRequest --> NetworkRetryCount{重試次數?}
    NetworkRetryCount -->|< 3 次| Continue
    NetworkRetryCount -->|>= 3 次| RecordError3[記錄網路錯誤]

    GeneralError --> RecordError4[記錄一般錯誤]

    RecordError1 --> NextAccount[處理下一個帳號]
    RecordError2 --> NextAccount
    RecordSecurityError --> NextAccount
    RecordError3 --> NextAccount
    RecordError4 --> NextAccount

    Continue --> NormalFlow[返回正常流程]
    NextAccount --> AccountLoop[帳號處理迴圈]
```

#### 6.2 會話超時恢復機制
```mermaid
sequenceDiagram
    participant Scraper as BaseScraper
    participant Browser as Chrome
    participant Website as 黑貓宅急便

    Scraper->>Website: 執行操作
    Website-->>Scraper: 會話超時回應

    Scraper->>Scraper: 檢測會話超時
    Note over Scraper: _check_session_timeout()

    loop 嘗試多個登入 URL
        Scraper->>Browser: 清除 Cookies
        Scraper->>Website: 前往登入頁面

        alt 成功到達登入頁面
            Scraper->>Scraper: 重新執行登入流程
            Scraper->>Website: 登入

            alt 登入成功
                Website-->>Scraper: 登入成功
                break 恢復成功
            else 登入失敗
                continue 嘗試下一個 URL
            end
        else 無法到達登入頁面
            continue 嘗試下一個 URL
        end
    end

    alt 恢復成功
        Scraper->>Scraper: 返回正常流程
    else 恢復失敗
        Scraper->>Scraper: 記錄錯誤並跳過帳號
    end
```

### 7. 報告生成流程

#### 7.1 執行報告結構
```mermaid
classDiagram
    class ExecutionReport {
        +string execution_time
        +string total_start_time
        +string total_end_time
        +float total_execution_minutes
        +int total_accounts
        +int successful_accounts
        +int failed_accounts
        +int security_warning_accounts
        +int total_downloads
        +list~AccountResult~ details
    }

    class AccountResult {
        +bool success
        +string username
        +list~string~ downloads
        +int records
        +float duration_minutes
        +string start_time
        +string end_time
        +string error
        +string error_type
        +string message
    }

    ExecutionReport ||--o{ AccountResult
```

#### 7.2 報告生成流程
```mermaid
flowchart TD
    AllAccountsDone[所有帳號處理完成] --> CollectResults[收集執行結果]
    CollectResults --> CalculateStats[計算統計資訊]

    subgraph "統計計算"
        CountSuccess[計算成功帳號數]
        CountFailures[計算失敗帳號數]
        CountSecurity[計算安全警告數]
        CountDownloads[計算總下載檔案數]
        CalculateTime[計算總執行時間]
    end

    CalculateStats --> CountSuccess
    CountSuccess --> CountFailures
    CountFailures --> CountSecurity
    CountSecurity --> CountDownloads
    CountDownloads --> CalculateTime

    CalculateTime --> GenerateConsole[生成控制台報告]
    GenerateConsole --> SaveJSON[保存 JSON 報告]

    subgraph "報告輸出"
        ConsoleOutput[控制台詳細輸出]
        JSONFile[reports/timestamp.json]
    end

    GenerateConsole --> ConsoleOutput
    SaveJSON --> JSONFile
```

### 8. 資料流程最佳化

#### 8.1 效能最佳化策略
- **檔案流**：使用 UUID 臨時目錄避免檔案衝突
- **記憶體管理**：及時清理不需要的物件和資源
- **網路最佳化**：智慧重試機制和超時設定
- **並行處理**：雖然帳號間是序列處理，但內部操作有並行最佳化

#### 8.2 資料完整性保證
- **原子操作**：檔案移動使用原子操作
- **錯誤隔離**：單一帳號錯誤不影響其他帳號
- **狀態追蹤**：完整的執行狀態記錄
- **回滾機制**：下載失敗時的清理機制

---

本資料流程設計確保了系統的可靠性、可追溯性和可維護性，為 SeleniumTCat 的穩定運行提供了完整的資料處理保障。