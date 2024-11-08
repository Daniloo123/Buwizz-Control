from flask import Flask, render_template, jsonify, request
import asyncio
import logging
from bleak import BleakClient, BleakScanner

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

    # Gebruik app.app_context() om de connectie binnen de juiste context te maken
    try:
        with app.app_context():  # Zorg ervoor dat de applicatiecontext is ingesteld
            result = asyncio.run(connect(device_address))
            return jsonify(result)
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
        return {'status': 'connected', 'message': f'Connected to {device_address}'}
    except Exception as e:
        logging.error(f"Failed to connect: {e}")
        return {'status': 'failed', 'message': str(e)}


# Route om een apparaat te verbreken
@app.route('/disconnect', methods=['POST'])
def disconnect_device():
    try:
        # Zorg ervoor dat de juiste event loop wordt gebruikt met asyncio.run()
        result = asyncio.run(disconnect_from_device())

        # Na het verbreken van de verbinding, stuur een refresh-instructie naar de client
        return jsonify({
            'status': 'disconnected',
            'message': 'Bluetooth verbinding verbroken.',
            'refresh': True  # Dit is de nieuwe instructie om de pagina te vernieuwen
        })
    except Exception as e:
        logging.error(f"Failed to disconnect: {e}")
        return jsonify({'status': 'failed', 'message': str(e)}), 500


# Functie om de verbinding te verbreken
async def disconnect_from_device():
    global client, connected_device
    if client is not None and client.is_connected:
        await client.disconnect()
        connected_device = None
        logging.info("Disconnected from device")

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
