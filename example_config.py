#!/usr/bin/env python3
"""
Example configuration file for async Modbus monitor
Modify these settings according to your Modbus device setup
"""

from async_modbus_monitor import AsyncModbusMonitor, ModbusConfig
import asyncio
import logging


async def data_processor(data):
    """Custom data processing function"""
    print(f"\n🔄 Processing {len(data)} readings...")
    
    for item in data:
        name = item['name']
        values = item['values']
        
        # Example: Process specific registers
        if 'Holding' in name:
            # Process holding registers (e.g., setpoints, configuration)
            avg_value = sum(values) / len(values) if values else 0
            print(f"   {name}: Average = {avg_value:.2f}")
            
        elif 'Input' in name:
            # Process input registers (e.g., sensor readings)
            print(f"   {name}: Sensors = {values}")
            
        elif 'Coils' in name:
            # Process coils (e.g., digital outputs)
            active_coils = [i for i, v in enumerate(values) if v]
            print(f"   {name}: Active coils = {active_coils}")


async def main():
    """Configure and run the Modbus monitor"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Configure Modbus connection
    config = ModbusConfig(
        host='192.168.30.21',      # Change to your Modbus device IP
        port=502,              # Standard Modbus TCP port
        device_id=1,           # Modbus device ID (slave ID)
        poll_interval=1.0,     # Poll every 1 second
        timeout=3.0,           # 3 second timeout
        retries=3              # Retry 3 times on failure
    )
    
    # Create monitor instance
    monitor = AsyncModbusMonitor(config)
    
    # Configure registers to monitor
    # Format: address, count, register_type, name
    
    # Holding Registers (Read/Write) - typically for setpoints, configuration
    monitor.add_register(0, 5, 'holding', 'Temperature_Setpoints')
    monitor.add_register(10, 3, 'holding', 'Control_Parameters')
    
    # Input Registers (Read Only) - typically for sensor readings, measurements  
    monitor.add_register(100, 8, 'input', 'Temperature_Sensors')
    monitor.add_register(200, 4, 'input', 'Pressure_Sensors')
    
    # Coils (Digital Outputs) - typically for control signals
    monitor.add_register(0, 16, 'coils', 'Output_Controls')
    
    # Discrete Inputs (Digital Inputs) - typically for status signals
    monitor.add_register(100, 8, 'discrete_inputs', 'Alarm_Status')
    
    print("Starting Modbus Monitor...")
    print(f"Target: {config.host}:{config.port}")
    print(f"Device ID: {config.device_id}")
    print(f"Poll Interval: {config.poll_interval}s")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Start monitoring with custom data processor
        await monitor.monitor_continuously(data_callback=data_processor)
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping monitor...")
        monitor.stop()
        
    except Exception as e:
        logging.error(f"Error: {e}")
        monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())