#!/usr/bin/env python3
"""
Async Modbus Data Monitor
Continuously monitors Modbus data using async client with configurable polling intervals.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException


@dataclass
class ModbusConfig:
    """Configuration for Modbus connection and monitoring"""
    host: str
    port: int = 502
    device_id: int = 1
    poll_interval: float = 1.0
    timeout: float = 3.0
    retries: int = 3


@dataclass
class RegisterConfig:
    """Configuration for register monitoring"""
    address: int
    count: int = 1
    register_type: str = 'holding'  # holding, input, coils, discrete_inputs
    name: str = None


class AsyncModbusMonitor:
    """Asynchronous Modbus data monitor"""
    
    def __init__(self, config: ModbusConfig):
        self.config = config
        self.client: Optional[AsyncModbusTcpClient] = None
        self.running = False
        self.logger = logging.getLogger(__name__)
        self.registers_to_monitor: List[RegisterConfig] = []
        
    def add_register(self, address: int, count: int = 1, 
                    register_type: str = 'holding', name: str = None):
        """Add a register to monitor"""
        reg_config = RegisterConfig(
            address=address, 
            count=count, 
            register_type=register_type,
            name=name or f"{register_type}_{address}"
        )
        self.registers_to_monitor.append(reg_config)
        
    async def connect(self) -> bool:
        """Connect to Modbus device"""
        try:
            self.client = AsyncModbusTcpClient(
                host=self.config.host,
                port=self.config.port,
                timeout=self.config.timeout,
                retries=self.config.retries
            )
            
            await self.client.connect()
            
            if self.client.connected:
                self.logger.info(f"Connected to Modbus device at {self.config.host}:{self.config.port}")
                return True
            else:
                self.logger.error("Failed to connect to Modbus device")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Modbus device"""
        if self.client:
            self.client.close()
            self.logger.info("Disconnected from Modbus device")
    
    async def read_register(self, reg_config: RegisterConfig) -> Optional[Dict[str, Any]]:
        """Read a single register configuration"""
        if not self.client or not self.client.connected:
            return None
            
        try:
            if reg_config.register_type == 'holding':
                result = await self.client.read_holding_registers(
                    reg_config.address,
                    count=reg_config.count,
                    device_id=self.config.device_id
                )
                values = result.registers if not result.isError() else None
                
            elif reg_config.register_type == 'input':
                result = await self.client.read_input_registers(
                    reg_config.address,
                    count=reg_config.count,
                    device_id=self.config.device_id
                )
                values = result.registers if not result.isError() else None
                
            elif reg_config.register_type == 'coils':
                result = await self.client.read_coils(
                    reg_config.address,
                    count=reg_config.count,
                    device_id=self.config.device_id
                )
                values = result.bits if not result.isError() else None
                
            elif reg_config.register_type == 'discrete_inputs':
                result = await self.client.read_discrete_inputs(
                    reg_config.address,
                    count=reg_config.count,
                    device_id=self.config.device_id
                )
                values = result.bits if not result.isError() else None
                
            else:
                self.logger.error(f"Unknown register type: {reg_config.register_type}")
                return None
            
            if values is not None:
                return {
                    'name': reg_config.name,
                    'address': reg_config.address,
                    'type': reg_config.register_type,
                    'values': values[:reg_config.count] if isinstance(values, list) else [values],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.error(f"Error reading {reg_config.name}: {result}")
                return None
                
        except ModbusException as exc:
            self.logger.error(f"Modbus exception reading {reg_config.name}: {exc}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error reading {reg_config.name}: {e}")
            return None
    
    async def read_all_registers(self) -> List[Dict[str, Any]]:
        """Read all configured registers"""
        tasks = [self.read_register(reg) for reg in self.registers_to_monitor]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Task failed with exception: {result}")
        
        return valid_results
    
    async def monitor_continuously(self, data_callback=None):
        """Continuously monitor Modbus data"""
        self.running = True
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        self.logger.info(f"Starting continuous monitoring (interval: {self.config.poll_interval}s)")
        
        while self.running:
            try:
                if not self.client or not self.client.connected:
                    self.logger.warning("Connection lost, attempting to reconnect...")
                    if not await self.connect():
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            self.logger.error("Max consecutive connection errors reached, stopping monitor")
                            break
                        await asyncio.sleep(self.config.poll_interval)
                        continue
                
                data = await self.read_all_registers()
                
                if data:
                    consecutive_errors = 0
                    if data_callback:
                        await data_callback(data)
                    else:
                        self.log_data(data)
                else:
                    consecutive_errors += 1
                    self.logger.warning(f"No data received (consecutive errors: {consecutive_errors})")
                
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error("Max consecutive read errors reached, stopping monitor")
                    break
                    
                await asyncio.sleep(self.config.poll_interval)
                
            except asyncio.CancelledError:
                self.logger.info("Monitor task cancelled")
                break
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Unexpected error in monitor loop: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error("Max consecutive errors reached, stopping monitor")
                    break
                await asyncio.sleep(self.config.poll_interval)
        
        self.running = False
        await self.disconnect()
    
    def log_data(self, data: List[Dict[str, Any]]):
        """Log data to console (default callback)"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"\n=== Modbus Data ({timestamp}) ===")
        for item in data:
            values_str = ', '.join(str(v) for v in item['values'])
            print(f"  {item['name']}: [{values_str}]")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False


async def custom_data_handler(data: List[Dict[str, Any]]):
    """Example custom data handler"""
    print(f"\n📊 Custom Handler - Received {len(data)} register readings")
    for item in data:
        print(f"   {item['name']}: {item['values'][0]} (Address: {item['address']})")


async def main():
    """Example usage"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config = ModbusConfig(
        host='192.168.30.21',  # Change to your Modbus device IP
        port=502,
        device_id=1,
        poll_interval=1,
        timeout=5.0
    )
    
    monitor = AsyncModbusMonitor(config)
    
    try:
        if await monitor.connect():
            print("Connected successfully! Reading Holding registers...")
            
            # Method 1: Use read_register function directly to read Holding registers
            print("\n=== Method 1: Direct read_register calls ===")
            holding_reg_config = RegisterConfig(
                address=0,
                count=10,
                register_type='holding',
                name='Holding_0-9'
            )
            
            # Read holding register data multiple times
            for i in range(3):
                print(f"\n--- Direct Reading {i+1} ---")
                
                # Read holding registers using read_register function
                holding_data = await monitor.read_register(holding_reg_config)
                
                if holding_data:
                    print(f"Register Name: {holding_data['name']}")
                    print(f"Address: {holding_data['address']}")
                    print(f"Type: {holding_data['type']}")
                    print(f"Values: {holding_data['values']}")
                    print(f"Timestamp: {holding_data['timestamp']}")
                else:
                    print("Failed to read holding register data")
                
                # Wait before next reading
                await asyncio.sleep(1)
            
            print("\n=== Method 2: Continuous monitoring with monitor_continuously ===")
            
            # Method 2: Use monitor_continuously function
            # Add registers to monitor
            monitor.add_register(address=0, count=10, register_type='holding', name='Holding_0-9')
            monitor.add_register(address=10, count=5, register_type='holding', name='Holding_10-14')
            
            # Start continuous monitoring with custom data handler
            print("Starting continuous monitoring... (Press Ctrl+C to stop)")
            await monitor.monitor_continuously(data_callback=custom_data_handler)
            
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()
    except Exception as e:
        logging.error(f"Error in main: {e}")
        monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())