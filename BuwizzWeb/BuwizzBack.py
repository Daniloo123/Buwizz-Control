from bleak import BleakClient

# BuWizz BLE device address
DEVICE_ADDRESS = "D8:36:DC:FD:9C:F0"  # Replace with your BuWizz 3.0 MAC address
SERVICE_UUID = "936E67B1-1999-B388-8144-FB74D1920550"  # BuWizz service UUID
CHARACTERISTIC_UUID = "50052901-74fb-4481-88b3-9919b1676e93"  # Application characteristic

# Motor control command (0x31) - for Port 1 motor, Port 4 servo
motor_control_command = bytearray([
    0x31,                    # Command for extended motor control
    0x00, 0x00, 0x00, 0x7F,  # Port 1 full forward (127 in 32-bit int)
    0x00, 0x00, 0x00, 0x00,  # Port 2 (not used, 0)
    0x00, 0x00, 0x00, 0x00,  # Port 3 (not used, 0)
    0xFF, 0xFF, 0xFF, 0x7F,  # Port 4: servo position (-90 degrees)
    0x00, 0x00,              # Port 5-6 (not used)
    0x00,                    # Brake flags (no brakes)
    0x00                     # LUT options (no LUT)
])

# Battery status command
status_enable_command = bytearray([0x01])

async def control_buwizz():
    async with BleakClient(DEVICE_ADDRESS) as client:
        # Enable status notifications (battery level, voltage, etc.)
        await client.write_gatt_char(CHARACTERISTIC_UUID, status_enable_command)

        # Write motor control command (e.g., to move forward/backward and set servo)
        await client.write_gatt_char(CHARACTERISTIC_UUID, motor_control_command)

        # Read notifications (e.g., battery status)
        def notification_handler(sender, data):
            battery_voltage = 9.0 + data[2] * 0.05
            print(f"Battery Voltage: {battery_voltage:.2f} V")
        
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        await asyncio.sleep(5)  # Keep reading data for 5 seconds
        await client.stop_notify(CHARACTERISTIC_UUID)

# Run the asyncio event loop
import asyncio
asyncio.run(control_buwizz())
