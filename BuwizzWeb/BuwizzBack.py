from flask import Flask, render_template, jsonify
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
async def scan_devices():
    devices = await BleakScanner.discover()
    devices_list = [{"name": device.name, "address": device.address} for device in devices]
    return jsonify(devices_list)

@app.route('/connect/<address>')
async def connect_device(address):
    client = BleakClient(address)
    await client.connect()
    return jsonify({"status": "connected"})

@app.route('/disconnect')
async def disconnect_device():
    # Voeg disconnect logica hier toe
    return jsonify({"status": "disconnected"})

# Functie om motorsnelheid aan te passen
@app.route('/motor_control', methods=['POST'])
async def motor_control():
    # Hier voeg je de code toe om de snelheid te verwerken en naar de BuWizz te sturen
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True)
