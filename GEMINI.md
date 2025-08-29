# Project Overview

This project, "Async Modbus Monitor," is an asynchronous Modbus data monitor built using the `pymodbus` library. Its primary purpose is to continuously monitor Modbus devices and collect data from various register types (holding, input, coils, discrete inputs). Key features include high-performance asynchronous client capabilities, continuous monitoring with configurable polling intervals, automatic reconnection, robust error handling, and flexible data processing through custom callbacks.

The project is written in Python and leverages `asyncio` for asynchronous operations.

# Building and Running

## Installation

To install the necessary dependencies, run the following command:

```bash
pip install pymodbus>=3.0.0
```

It is recommended to use a Python virtual environment for dependency management.

## Basic Usage

To use the monitor, you can import `AsyncModbusMonitor` and `ModbusConfig` from `async_modbus_monitor.py` and set up your configuration:

```python
from async_modbus_monitor import AsyncModbusMonitor, ModbusConfig
import asyncio

async def main():
    # Configure connection
    config = ModbusConfig(
        host='127.0.0.1',  # Your Modbus device IP
        port=502,
        device_id=1,
        poll_interval=2.0
    )

    # Create monitor
    monitor = AsyncModbusMonitor(config)

    # Add registers to monitor
    monitor.add_register(0, 10, 'holding', 'Holding_0-9')
    monitor.add_register(100, 5, 'input', 'Input_100-104')

    # Start monitoring
    if await monitor.connect():
        await monitor.monitor_continuously()

asyncio.run(main())
```

## Using Example Configuration

An example configuration is provided in `example_config.py`. You can run it directly using:

```bash
python example_config.py
```

## Stopping Monitoring

Monitoring can be stopped by pressing `Ctrl+C` or by calling the `monitor.stop()` method programmatically.

# Development Conventions

*   **Language:** Python
*   **Asynchronous Framework:** `asyncio`
*   **Modbus Library:** `pymodbus` (version 3.0.0 or higher)
*   **Configuration:** Modbus connection and register configurations are managed via the `ModbusConfig` class and `add_register` method.
*   **Error Handling:** Includes automatic reconnection, retry logic, continuous error limits, and comprehensive exception handling with logging.
*   **Logging:** Standard Python `logging` module is used for logging.
