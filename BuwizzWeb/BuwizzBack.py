from flask import Flask, render_template, jsonify, request
import asyncio
import logging
from bleak import BleakClient, BleakScanner
import threading

app = Flask(__name__)

# Log configuratie
logging.basicConfig(level=logging.INFO)

# BuWizz service UUID
CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"

# Globale variabelen voor motorsnelheden
motor_port_data_1 = 0
motor_port_data_4 = 0
client = None
max_speed = 127
speed_increment = 50
speed_increment_motor_4 = 25
connected_device = None
battery_level = None  # Stel in op de waarde die je uit het apparaat haalt
motor_currents = [0, 0, 0, 0]  # Voor de vier motorpoorten
battery_voltage = None  # Voor de batterijspanning

# UUID's van de verschillende services en characteristics
UNKNOWN_SERVICE_UUID = "500592d1-74fb-4481-88b3-9919b1676e93"
UNKNOWN_CHARACTERISTICS = [
    "50058000-74fb-4481-88b3-9919b1676e93",
    "50052901-74fb-4481-88b3-9919b1676e93",
    "50053903-74fb-4481-88b3-9919b1676e93",
    "50053901-74fb-4481-88b3-9919b1676e93",
    "50053904-74fb-4481-88b3-9919b1676e93",
    "50053902-74fb-4481-88b3-9919b1676e93"
]

DEVICE_INFO_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
DEVICE_INFO_CHARACTERISTICS = {
    "Firmware Revision": "00002a26-0000-1000-8000-00805f9b34fb",
    "Serial Number": "00002a25-0000-1000-8000-00805f9b34fb",
    "Model Number": "00002a24-0000-1000-8000-00805f9b34fb",
    "Software Revision": "00002a28-0000-1000-8000-00805f9b34fb",
    "Manufacturer": "00002a29-0000-1000-8000-00805f9b34fb"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
async def scan_devices():
    devices = await BleakScanner.discover()
    devices_list = [{"name": device.name, "address": device.address} for device in devices]
    return jsonify(devices_list)

@app.route('/connect', methods=['POST'])
def connect_device():
    device_address = request.json.get('device_address')  # Verkrijg het apparaatadres uit de JSON payload
    global client

    try:
        # Run de connectie asynchrone taak in een aparte thread
        threading.Thread(target=asyncio.run, args=(connect(device_address),)).start()
        return jsonify({'status': 'connecting', 'message': 'Connected to device'})
    except Exception as e:
        logging.error(f"Failed to connect: {e}")
        return jsonify({'status': 'failed', 'message': str(e)}), 500

# De connectie-logica als asynchrone functie
async def connect(device_address):
    global client, connected_device
    try:
        client = BleakClient(device_address)
        await client.connect()
        connected_device = device_address
        logging.info(f"Connected to {device_address}")
        
        # Start notificaties voor de statusrapporten
        for characteristic_uuid in UNKNOWN_CHARACTERISTICS:
            await client.start_notify(characteristic_uuid, handle_status_report)
            logging.info(f"Notificaties gestart voor {characteristic_uuid}")

        return {'status': 'connected', 'message': f'Connected to {device_address}'}
    except Exception as e:
        logging.error(f"Failed to connect: {e}")
        return {'status': 'failed', 'message': str(e)}

# Functie om de verbinding te verbreken
@app.route('/disconnect', methods=['POST'])
def disconnect_device():
    try:
        # Zorg ervoor dat de juiste event loop wordt gebruikt met asyncio.run()
        result = asyncio.run(disconnect_from_device())

        return jsonify({
            'status': 'disconnected',
            'message': 'Bluetooth verbinding verbroken.',
            'refresh': True
        })
    except Exception as e:
        logging.error(f"Failed to disconnect: {e}")
        return jsonify({'status': 'failed', 'message': str(e)}), 500

async def disconnect_from_device():
    global client, connected_device
    if client is not None and client.is_connected:
        await client.disconnect()
        connected_device = None
        logging.info("Disconnected from device")

@app.route('/status')
def get_status():
    global battery_level, motor_currents, battery_voltage, connected_device
    if connected_device is None:
        return jsonify({'status': 'error', 'message': 'No device connected'})

    return jsonify({
        'battery_level': battery_level * 25 if battery_level is not None else "Unknown",  # Omzetten naar percentage
        'battery_voltage': battery_voltage if battery_voltage is not None else "Unknown",
        'motor_currents': motor_currents if motor_currents else "Unknown"
    })


def handle_status_report(sender, data):
    """Verwerk het statusrapport om de motorstroom en batterijstatus te monitoren."""
    global battery_level, motor_currents, battery_voltage

    # Log de binnenkomende data om te debuggen
    logging.info(f"Ontvangen data: {data.hex()}")

    # Byte 1: Status flags (gebruiken bitwise AND om individuele bits te extraheren)
    status_flags = data[1]
    logging.info(f"Status flags: {status_flags:08b}")  # Toon de statusflags in binaire vorm

    # Extract de batterijstatus (bits 3-4 van status_flags)
    battery_level = (status_flags >> 3) & 0x03  # Batterij niveau wordt bepaald door bits 3-4
    logging.info(f"Extracted battery level: {battery_level}")

    # Batterijspanning: 9V + data[2] * 0.05V
    battery_voltage = 9 + data[2] * 0.05
    logging.info(f"Batterij spanning: {battery_voltage} V")

    # Motorstromen: bytes 3-8 geven de motorstroom (omrekenen naar ampère)
    motor_currents = [data[i] * 0.015 for i in range(3, 9)]
    logging.info(f"Motor currents: {motor_currents}")

    if battery_level is not None:
        battery_percentage = battery_level * 25  # 0 = leeg, 1 = laag, 2 = medium, 3 = vol
        logging.info(f"Batterij percentage: {battery_percentage}%")
    else:
        logging.info("Batterij percentage onbekend.")

        # Functie om motorsnelheid aan te passen
@app.route('/motor_control', methods=['POST'])
async def motor_control():
    global motor_port_data_1, motor_port_data_4, client

    # Verkrijg het richtingcommando van de frontend
    direction = request.json.get('direction')

    # Pas motorsnelheden aan op basis van het commando
    if direction == 'up':
        motor_port_data_1 = max(motor_port_data_1 - speed_increment, -max_speed)  # Achteruit
    elif direction == 'down':
        motor_port_data_1 = min(motor_port_data_1 + speed_increment, max_speed)   # Vooruit
    elif direction == 'left':
        motor_port_data_4 = min(motor_port_data_4 + speed_increment_motor_4, 70)  # Links
    elif direction == 'right':
        motor_port_data_4 = max(motor_port_data_4 - speed_increment_motor_4, -70) # Rechts
    elif direction == 'stop':
        motor_port_data_1 = 0  # Stop motor 1
        motor_port_data_4 = 0  # Stop motor 4

    # Verzend het aangepaste motorcommando naar BuWizz
    await send_motor_command(client, motor_port_data_1, motor_port_data_4)
    return jsonify({"status": "success", "message": f"Executed {direction} command"})
    
async def send_motor_command(client, speed_1, speed_4):
    """Verstuur motorsnelheidscommando naar BuWizz"""
    def transform_speed(speed):
        if speed < 0:
            return 256 + speed  # Hierdoor wordt -1 -> 255, -127 -> 129 etc.
        return speed

    transformed_speed_1 = transform_speed(speed_1)
    transformed_speed_4 = transform_speed(speed_4)
    b_array = bytearray([0x30, transformed_speed_1, 0x00, 0x00, transformed_speed_4, 0x00, 0x00, 0x00, 0x00])
    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, b_array, response=False)


if __name__ == '__main__':
    app.run(debug=True)
