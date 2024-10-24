import logging
from flask import Flask, request, jsonify, render_template
import asyncio
from bleak import BleakClient, BleakScanner

app = Flask(__name__)

# Configuratie voor logging
logging.basicConfig(level=logging.INFO)

# BuWizz Bluetooth service UUID
CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"

client = None  # Bluetooth client (Bleak)
connected_device = None  # Houdt het verbonden apparaat bij
motor_port_data_1 = 0
motor_port_data_4 = 0

@app.route('/')
def index():
    """Rendert de webinterface"""
    return render_template('index.html')

# Route om Bluetooth-apparaten te scannen
@app.route('/scan', methods=['GET'])
def scan_bluetooth():
    devices = asyncio.run(scan_for_devices())
    return jsonify({'devices': devices})

# Functie om naar Bluetooth-apparaten te scannen
async def scan_for_devices():
    devices = await BleakScanner.discover()
    return [{'name': d.name, 'address': d.address} for d in devices]

# Route om verbinding te maken met een Bluetooth-apparaat
@app.route('/connect', methods=['POST'])
def connect_bluetooth_device():
    """Verbind met een geselecteerd Bluetooth-apparaat"""
    global client
    device_address = request.form['device_address']

    async def connect():
        global client, connected_device
        try:
            client = BleakClient(device_address)
            await client.connect()
            connected_device = device_address  # Bewaar verbonden apparaat
            return {'status': 'connected'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    connection_status = asyncio.run(connect())
    
    if connection_status['status'] == 'connected':
        return jsonify({'status': 'connected', 'message': f'Verbonden met apparaat {device_address}'})
    else:
        return jsonify({'status': 'error', 'message': f'Fout bij verbinden: {connection_status["message"]}'})

# Route om de Bluetooth-verbinding te verbreken
@app.route('/disconnect', methods=['POST'])
def disconnect_device():
    try:
        asyncio.run(disconnect_from_device())
        return jsonify({'status': 'disconnected', 'message': 'Bluetooth verbinding verbroken.'})
    except Exception as e:
        logging.error(f"Failed to disconnect: {e}")
        return jsonify({'status': 'failed', 'message': str(e)})

# Functie om de verbinding te verbreken
async def disconnect_from_device():
    global client, connected_device
    if client is not None and client.is_connected:
        await client.disconnect()
        connected_device = None
        logging.info("Disconnected from device")

# Functie om de motoren aan te sturen via Bluetooth
async def send_motor_command(speed_1, speed_4):
    def transform_speed(speed):
        return 256 + speed if speed < 0 else speed

    transformed_speed_1 = transform_speed(speed_1)
    transformed_speed_4 = transform_speed(speed_4)
    
    # Maak de bytearray met de aangepaste snelheden
    b_array = bytearray([0x30, transformed_speed_1, 0x00, 0x00, transformed_speed_4, 0x00, 0x00, 0x00, 0x00])
    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, b_array, response=False)
    logging.info(f"Motor 1 snelheid: {transformed_speed_1}, Motor 4 snelheid: {transformed_speed_4}")

# Route om de motorsnelheid in te stellen
@app.route('/set_motor_speed', methods=['POST'])
def set_motor_speed():
    data = request.json
    motor = data.get('motor')
    speed = int(data.get('speed'))
    logging.info(f"Motor {motor} snelheid ingesteld op {speed}")

    if motor == 1:
        asyncio.run(set_motor_1_speed(speed))
    elif motor == 4:
        asyncio.run(set_motor_4_speed(speed))

    return jsonify({'status': 'success'})

async def set_motor_1_speed(speed):
    global motor_port_data_1
    motor_port_data_1 = speed
    await send_motor_command(motor_port_data_1, motor_port_data_4)

async def set_motor_4_speed(speed):
    global motor_port_data_4
    motor_port_data_4 = speed
    await send_motor_command(motor_port_data_1, motor_port_data_4)

if __name__ == '__main__':
    app.run(debug=True)
