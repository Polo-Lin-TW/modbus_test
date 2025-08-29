# Async Modbus Monitor

基於 pymodbus 的異步 Modbus 數據監控器，可持續監聽 Modbus 設備傳送的數據。

## 功能特點

- **高性能異步客戶端**: 使用 `AsyncModbusTcpClient`，支援高達 3,030 次/秒的讀取速度
- **雙模式讀取**: 支援單次直接讀取和持續監控模式
- **多種寄存器支援**: 支援 holding registers、input registers、coils、discrete inputs
- **錯誤處理**: 完整的錯誤處理和自動重連邏輯
- **靈活的數據處理**: 支援自定義回調函數進行數據處理
- **配置化設計**: 使用 dataclass 進行配置管理

## 檔案結構

```
modbus_test/
├── async_modbus_monitor.py  # 主要監控類別和功能
├── example_config.py        # 範例配置和使用方式
└── README.md               # 使用說明文檔
```

## 安裝依賴

```bash
pip install pymodbus>=3.0.0
# 或使用 uv
uv add pymodbus>=3.0.0
```

## 快速開始

### 1. 運行內建範例

直接運行主程式，包含兩種讀取模式的示範：

```bash
uv run python async_modbus_monitor.py
```

### 2. 運行配置範例

使用提供的範例配置：

```bash
uv run python example_config.py
```

## 兩種使用模式

### 模式 1: 直接讀取 `read_register()`

適用於單次或少量讀取操作：

```python
from async_modbus_monitor import AsyncModbusMonitor, ModbusConfig, RegisterConfig
import asyncio

async def direct_read_example():
    config = ModbusConfig(
        host='192.168.1.100',
        port=502,
        device_id=1,
        timeout=5.0
    )
    
    monitor = AsyncModbusMonitor(config)
    
    if await monitor.connect():
        # 配置寄存器
        holding_reg = RegisterConfig(
            address=0,
            count=10,
            register_type='holding',
            name='Holding_0-9'
        )
        
        # 直接讀取
        data = await monitor.read_register(holding_reg)
        if data:
            print(f"Values: {data['values']}")
        
        await monitor.disconnect()

asyncio.run(direct_read_example())
```

### 模式 2: 持續監控 `monitor_continuously()`

適用於需要持續監控的場景：

```python
from async_modbus_monitor import AsyncModbusMonitor, ModbusConfig
import asyncio

async def continuous_monitor_example():
    config = ModbusConfig(
        host='192.168.1.100',
        port=502,
        device_id=1,
        poll_interval=1.0,
        timeout=5.0
    )
    
    monitor = AsyncModbusMonitor(config)
    
    # 添加要監控的寄存器
    monitor.add_register(0, 10, 'holding', 'Holding_0-9')
    monitor.add_register(100, 5, 'input', 'Input_100-104')
    
    try:
        if await monitor.connect():
            await monitor.monitor_continuously()
    except KeyboardInterrupt:
        monitor.stop()

asyncio.run(continuous_monitor_example())
```

## 配置說明

### ModbusConfig 參數

```python
@dataclass
class ModbusConfig:
    host: str           # Modbus 設備的 IP 地址
    port: int = 502     # 端口號 (默認 502)
    device_id: int = 1  # 設備 ID / Slave ID (默認 1)
    poll_interval: float = 1.0  # 輪詢間隔，單位秒 (默認 1.0)
    timeout: float = 3.0        # 超時時間，單位秒 (默認 3.0)
    retries: int = 3            # 重試次數 (默認 3)
```

### RegisterConfig 參數

```python
@dataclass
class RegisterConfig:
    address: int                        # 寄存器起始地址
    count: int = 1                      # 讀取數量 (默認 1)
    register_type: str = 'holding'      # 寄存器類型 (默認 'holding')
    name: str = None                    # 自定義名稱 (可選)
```

### 寄存器類型

1. **holding**: Holding Registers (可讀寫)
   - 通常用於設定值、配置參數
   - 函數調用: `read_holding_registers()`
   
2. **input**: Input Registers (只讀)
   - 通常用於傳感器讀數、測量值
   - 函數調用: `read_input_registers()`
   
3. **coils**: Coils (數字輸出)
   - 通常用於控制信號
   - 函數調用: `read_coils()`
   
4. **discrete_inputs**: Discrete Inputs (數字輸入)
   - 通常用於狀態信號、警報
   - 函數調用: `read_discrete_inputs()`

## 核心類別和方法

### AsyncModbusMonitor 類別

#### 主要方法:
- `connect()`: 連接到 Modbus 設備
- `disconnect()`: 斷開連接
- `read_register(reg_config)`: 讀取單個寄存器配置
- `read_all_registers()`: 讀取所有配置的寄存器
- `monitor_continuously(data_callback=None)`: 持續監控
- `add_register(address, count, register_type, name)`: 添加監控寄存器
- `stop()`: 停止監控

## 自定義數據處理

### 使用自定義回調函數

```python
async def custom_data_handler(data):
    """自定義數據處理函數"""
    print(f"📊 接收到 {len(data)} 個寄存器讀數")
    
    for item in data:
        name = item['name']
        values = item['values']
        timestamp = item['timestamp']
        address = item['address']
        
        # 根據寄存器名稱進行不同處理
        if 'Temperature' in name:
            avg_temp = sum(values) / len(values)
            print(f"   {name}: 平均溫度 {avg_temp:.2f}°C")
        elif 'Pressure' in name:
            print(f"   {name}: 壓力值 {values}")
        else:
            print(f"   {name}: {values}")

# 使用自定義處理器
await monitor.monitor_continuously(data_callback=custom_data_handler)
```

### 數據格式

每個讀取結果包含以下欄位:
```python
{
    'name': 'Holding_0-9',           # 寄存器名稱
    'address': 0,                    # 起始地址
    'type': 'holding',               # 寄存器類型
    'values': [100, 200, 300, ...],  # 數值列表
    'timestamp': '2025-08-25T13:45:30.123456'  # 時間戳
}
```

## 錯誤處理機制

監控器內建完善的錯誤處理機制：

### 1. 自動重連
- 連接丟失時自動嘗試重連
- 支援重連延遲和重試次數配置

### 2. 連續錯誤監控
- 監控連續錯誤次數（默認最多 5 次）
- 超過限制時自動停止監控防止無限循環

### 3. 異常捕獲
- `ModbusException`: Modbus 協議異常
- `asyncio.CancelledError`: 任務取消異常
- `Exception`: 其他未預期異常

### 4. 日誌記錄
```python
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 日誌級別說明:
# INFO: 連接狀態、監控啟動/停止
# WARNING: 連接丟失、數據讀取失敗
# ERROR: 嚴重錯誤、異常情況
```

## 使用範例

### 完整使用範例

```python
#!/usr/bin/env python3
import asyncio
import logging
from async_modbus_monitor import AsyncModbusMonitor, ModbusConfig, RegisterConfig

async def main():
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Modbus 連接配置
    config = ModbusConfig(
        host='192.168.30.21',
        port=502,
        device_id=1,
        poll_interval=1.0,
        timeout=5.0,
        retries=3
    )
    
    monitor = AsyncModbusMonitor(config)
    
    try:
        # 連接設備
        if await monitor.connect():
            print("🔗 連接成功!")
            
            # 方法1: 直接讀取
            holding_config = RegisterConfig(
                address=0,
                count=10, 
                register_type='holding',
                name='測試寄存器'
            )
            
            data = await monitor.read_register(holding_config)
            if data:
                print(f"📊 讀取結果: {data['values']}")
            
            # 方法2: 持續監控
            monitor.add_register(0, 10, 'holding', 'Holding_0-9')
            monitor.add_register(10, 5, 'holding', 'Holding_10-14')
            
            print("🔄 開始持續監控... (Ctrl+C 停止)")
            await monitor.monitor_continuously()
            
    except KeyboardInterrupt:
        print("\n⏹️ 使用者中斷，停止監控...")
        monitor.stop()
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
    finally:
        await monitor.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## 停止監控

### 正常停止
- 使用 `Ctrl+C` (KeyboardInterrupt)
- 調用 `monitor.stop()` 方法

### 異常停止
- 連續錯誤超過限制（默認 5 次）
- 網路連接失敗超過重試次數

## 效能考量

1. **輪詢間隔**: 根據設備性能調整 `poll_interval`
2. **並發讀取**: `read_all_registers()` 使用 `asyncio.gather()` 並發執行
3. **連接重用**: 保持連接活躍，避免頻繁連接/斷開
4. **錯誤限制**: 避免無限重試造成資源浪費

## 注意事項

1. **網路設置**
   - 確保 Modbus 設備 IP 地址和端口正確
   - 檢查防火牆設置，確保端口 502 可通訊

2. **設備配置**
   - 確認設備 ID (Slave ID) 正確
   - 根據設備文檔配置正確的寄存器地址和類型

3. **效能調整**  
   - 調整輪詢間隔避免過載設備
   - 大量寄存器讀取時考慮分批處理

4. **錯誤處理**
   - 監控日誌輸出，及時發現連接問題
   - 根據實際情況調整重試次數和超時時間

## API 版本相容性

此實作基於 pymodbus 3.0+ 版本開發，使用正確的函數參數：
- `device_id=` 參數用於指定設備 ID
- `count=` 參數用於指定讀取數量
- 支援所有主要的 Modbus 功能碼

## 參考文檔

- [PyModbus 官方文檔](https://pymodbus.readthedocs.io/en/latest/)
- [Modbus 協議規範](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)
- [Python asyncio 文檔](https://docs.python.org/3/library/asyncio.html)