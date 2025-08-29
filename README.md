# Async Modbus Monitor

一個基於 Python asyncio 的異步 Modbus 數據監控工具，支持持續監控 Modbus 設備並收集各種寄存器類型的數據。

## 專案結構分析

### 核心文件概覽
- **`async_modbus_monitor.py`** (302行) - 主要模組，包含核心功能實現
- **`example_config.py`** (94行) - 配置示例和使用演示
- **`README.md`** (361行) - 專案文檔
- **`GEMINI.md`** (69行) - 專案概述文檔

### 架構設計

#### 核心類別結構

1. **`ModbusConfig`** - 數據類，用於配置 Modbus 連接參數
   ```python
   @dataclass
   class ModbusConfig:
       host: str                    # Modbus 設備 IP 地址
       port: int = 502             # 端口號 (默認 502)
       device_id: int = 1          # 設備 ID (從站 ID)
       poll_interval: float = 1.0  # 輪詢間隔 (秒)
       timeout: float = 3.0        # 超時時間 (秒)
       retries: int = 3            # 重試次數
   ```

2. **`RegisterConfig`** - 數據類，用於配置寄存器監控參數
   ```python
   @dataclass
   class RegisterConfig:
       address: int                           # 寄存器地址
       count: int = 1                        # 讀取數量
       register_type: str = 'holding'        # 寄存器類型
       name: str = None                      # 寄存器名稱
   ```

3. **`AsyncModbusMonitor`** - 主要監控類
   - **連接管理**: `connect()`, `disconnect()`
   - **寄存器操作**: `add_register()`, `read_register()`, `read_all_registers()`
   - **監控功能**: `monitor_continuously()`
   - **錯誤處理**: 自動重連和錯誤計數機制

#### 技術特點分析

- **異步架構**: 基於 `asyncio` 實現非阻塞 I/O 操作
- **並發讀取**: 使用 `asyncio.gather()` 並發讀取多個寄存器
- **錯誤恢復**: 
  - 最大連續錯誤數限制 (5次)
  - 自動重連機制
  - 異常捕獲和日誌記錄
- **靈活回調**: 支持自定義數據處理回調函數
- **類型安全**: 使用 Python 類型提示增強代碼可讀性

## 功能特點

- **異步操作**: 使用 Python asyncio 實現高性能異步客戶端
- **持續監控**: 可配置的輪詢間隔，持續監控 Modbus 數據
- **多種寄存器類型**: 支持 Holding Registers、Input Registers、Coils、Discrete Inputs
- **自動重連**: 連接斷開時自動嘗試重新連接
- **錯誤處理**: 完善的錯誤處理和重試機制 (最大連續錯誤數: 5)
- **靈活的數據處理**: 支持自定義回調函數處理數據
- **日誌記錄**: 詳細的日誌記錄，便於調試和監控
- **並發讀取**: 同時讀取多個寄存器配置，提高效率

## 依賴項分析

### 主要依賴
- **`pymodbus>=3.0.0`** - Modbus 協議實現庫
- **`asyncio`** - Python 標準庫，異步 I/O 支持
- **`logging`** - Python 標準庫，日誌記錄
- **`datetime`** - Python 標準庫，時間戳處理
- **`typing`** - Python 標準庫，類型提示
- **`dataclasses`** - Python 標準庫，數據類支持

### 安裝要求

```bash
pip install pymodbus>=3.0.0
```

建議使用虛擬環境來管理依賴項。

## 快速開始

### 1. 基本使用

```python
from async_modbus_monitor import AsyncModbusMonitor, ModbusConfig
import asyncio

async def main():
    # 配置連接
    config = ModbusConfig(
        host='192.168.1.100',  # 您的 Modbus 設備 IP
        port=502,
        device_id=1,
        poll_interval=2.0
    )

    # 創建監控器
    monitor = AsyncModbusMonitor(config)

    # 添加要監控的寄存器
    monitor.add_register(0, 10, 'holding', 'Holding_0-9')
    monitor.add_register(100, 5, 'input', 'Input_100-104')

    # 開始監控
    if await monitor.connect():
        await monitor.monitor_continuously()

asyncio.run(main())
```

### 2. 運行示例配置

```bash
python example_config.py
```

## 使用模式

### 模式一：直接讀取

```python
# 創建寄存器配置
reg_config = RegisterConfig(
    address=0,
    count=10,
    register_type='holding',
    name='Temperature_Sensors'
)

# 直接讀取
data = await monitor.read_register(reg_config)
if data:
    print(f"讀取到數據: {data['values']}")
```

### 模式二：持續監控

```python
# 添加寄存器到監控列表
monitor.add_register(0, 5, 'holding', 'Temperature_Setpoints')
monitor.add_register(100, 8, 'input', 'Temperature_Sensors')
monitor.add_register(0, 16, 'coils', 'Output_Controls')
monitor.add_register(100, 8, 'discrete_inputs', 'Alarm_Status')

# 開始持續監控
await monitor.monitor_continuously()
```

## 寄存器類型支持

| 寄存器類型 | 描述 | 讀取方法 | 用途 |
|-----------|------|----------|------|
| `holding` | 保持寄存器 | `read_holding_registers()` | 設定值、配置參數 |
| `input` | 輸入寄存器 | `read_input_registers()` | 傳感器讀數、測量值 |
| `coils` | 線圈 | `read_coils()` | 數字輸出控制 |
| `discrete_inputs` | 離散輸入 | `read_discrete_inputs()` | 狀態信號、報警 |

## 配置參數詳解

### ModbusConfig 參數

- **`host`**: Modbus 設備的 IP 地址
- **`port`**: TCP 端口號，標準 Modbus TCP 端口為 502
- **`device_id`**: Modbus 設備 ID (從站 ID)，通常為 1
- **`poll_interval`**: 輪詢間隔（秒），控制數據讀取頻率
- **`timeout`**: 連接超時時間（秒）
- **`retries`**: 連接失敗時的重試次數

### RegisterConfig 參數

- **`address`**: 寄存器起始地址
- **`count`**: 要讀取的寄存器數量
- **`register_type`**: 寄存器類型 ('holding', 'input', 'coils', 'discrete_inputs')
- **`name`**: 寄存器組的自定義名稱

## 錯誤處理機制

### 連接錯誤處理
- 自動檢測連接狀態
- 連接斷開時自動重連
- 最大連續連接錯誤數限制 (5次)

### 讀取錯誤處理
- 捕獲 ModbusException 和一般異常
- 記錄詳細錯誤日誌
- 連續讀取錯誤計數和限制

### 監控循環保護
- `asyncio.CancelledError` 處理
- 優雅的停止機制
- 資源清理和連接關閉

## 自定義數據處理

### 使用自定義回調函數

```python
async def custom_data_processor(data):
    """自定義數據處理函數"""
    print(f"處理 {len(data)} 個讀數...")
    
    for item in data:
        name = item['name']
        values = item['values']
        timestamp = item['timestamp']
        
        # 根據寄存器類型進行不同處理
        if 'Holding' in name:
            # 處理保持寄存器（設定值、配置）
            avg_value = sum(values) / len(values) if values else 0
            print(f"   {name}: 平均值 = {avg_value:.2f}")
            
        elif 'Input' in name:
            # 處理輸入寄存器（傳感器讀數）
            print(f"   {name}: 傳感器值 = {values}")
            
        elif 'Coils' in name:
            # 處理線圈（數字輸出）
            active_coils = [i for i, v in enumerate(values) if v]
            print(f"   {name}: 激活的線圈 = {active_coils}")

# 使用自定義處理器
await monitor.monitor_continuously(data_callback=custom_data_processor)
```

## 日誌配置

```python
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 設置特定模組的日誌級別
logging.getLogger('async_modbus_monitor').setLevel(logging.DEBUG)
```

## 性能優化

### 並發讀取
- 使用 `asyncio.gather()` 同時讀取多個寄存器
- 減少總體讀取時間
- 提高數據收集效率

### 連接管理
- 保持長連接，避免頻繁連接/斷開
- 智能重連機制
- 連接狀態監控

### 錯誤恢復
- 快速故障檢測
- 自動恢復機制
- 最小化停機時間

## 實際應用場景

### 工業自動化
- 溫度控制系統監控
- 壓力傳感器數據收集
- 設備狀態監控

### 數據採集
- SCADA 系統集成
- 歷史數據記錄
- 實時數據分析

### 設備維護
- 設備健康監控
- 預防性維護
- 故障診斷

## 故障排除

### 常見問題

1. **連接失敗**
   - 檢查 IP 地址和端口
   - 確認設備 ID 正確
   - 檢查網絡連接

2. **讀取錯誤**
   - 驗證寄存器地址範圍
   - 檢查寄存器類型
   - 確認設備支持的功能

3. **性能問題**
   - 調整輪詢間隔
   - 減少同時監控的寄存器數量
   - 優化網絡配置

## 開發和擴展

### 添加新功能
- 繼承 `AsyncModbusMonitor` 類
- 實現自定義數據處理邏輯
- 添加新的寄存器類型支持

### 集成其他系統
- 數據庫存儲
- Web API 接口
- 消息隊列集成

## 相關資源

- [pymodbus 文檔](https://pymodbus.readthedocs.io/)
- [Modbus 協議規範](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)
- [Python asyncio 文檔](https://docs.python.org/3/library/asyncio.html)

## 許可證

本專案遵循開源許可證，具體詳情請查看 LICENSE 文件。

## 貢獻

歡迎提交 Issue 和 Pull Request 來改進這個專案。

---

**注意**: 在生產環境中使用前，請確保正確配置網絡安全設置和訪問控制。