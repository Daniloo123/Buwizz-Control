import asyncio
import logging
from bleak import BleakClient, BleakScanner
import sys

logging.basicConfig(level="INFO")

# BuWizz Bluetooth service UUID
CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"

# Globale variabelen voor motorsnelheden
motor_port_data_1 = 0  # Snelheid voor motor 1 (poort 1)
motor_port_data_4 = 0  # Snelheid voor motor 4 (poort 4)
prev_motor_port_data_1 = None  # Voor controle op verandering
prev_motor_port_data_4 = None  # Voor controle op verandering
max_speed = 127  # Maximale snelheid voor de motoren
speed_increment = 5  # Hoeveelheid waarmee de snelheid per stap toeneemt voor motor 1
speed_increment_motor_4 = 2  # Lagere snelheidsstappen voor motor 4

async def select_bluetooth_device():
    """Scan voor Bluetooth-apparaten en selecteer er een"""
    while True:
        logging.info("Scannen naar apparaten...")
        devices = await BleakScanner.discover()
        n = 0
        for device in devices:
            logging.info(f"Apparaat {n}: {device}")
            n += 1
        try:
            selected_device = int(input("Selecteer apparaatgebruiksnummer: "))
            device = devices[selected_device]
            return device
        except KeyboardInterrupt:
            exit()
        except (IndexError, UnboundLocalError, ValueError):
            logging.info("Probeer het opnieuw")

async def send_motor_command(client, speed_1, speed_4):
    """Verstuur motorsnelheidscommando naar BuWizz"""
    
    # Zet negatieve snelheden om in waardes tussen 128 en 255
    def transform_speed(speed):
        if speed < 0:
            return 256 + speed  # Hierdoor wordt -1 -> 255, -127 -> 129 etc.
        return speed

    # Pas de snelheden aan
    transformed_speed_1 = transform_speed(speed_1)
    transformed_speed_4 = transform_speed(speed_4)

    # Maak de bytearray met de aangepaste snelheden
    b_array = bytearray([0x30, transformed_speed_1, 0x00, 0x00, transformed_speed_4, 0x00, 0x00, 0x00, 0x00])
    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, b_array, response=False)

async def motor_control(client):
    global motor_port_data_1, motor_port_data_4, prev_motor_port_data_1, prev_motor_port_data_4
    logging.info("Start de motorbesturingslus...")

    while True:
        # Vraag invoer van de gebruiker
        user_input = input("Gebruik W/S voor motor 1 (vooruit/achteruit), A/D voor motor 4 (links/rechts), ! om te stoppen: ")
        
        if user_input.lower() == 's':
            motor_port_data_1 = max(motor_port_data_1 - speed_increment, -max_speed)  # Achteruit
        elif user_input.lower() == 'w':
            motor_port_data_1 = min(motor_port_data_1 + speed_increment, max_speed)  # Vooruit
        elif user_input.lower() == 'a':
            motor_port_data_4 = max(motor_port_data_4 - speed_increment_motor_4, -max_speed)  # Draaien naar links
        elif user_input.lower() == 'd':
            motor_port_data_4 = min(motor_port_data_4 + speed_increment_motor_4, max_speed)  # Draaien naar rechts
        elif user_input == '!':
            logging.info("Beëindiging door invoer van '!'.")
            break
        else:
            logging.info("Ongeldige invoer, probeer het opnieuw.")

        # Alleen verzenden als de snelheid veranderd is
        if motor_port_data_1 != prev_motor_port_data_1 or motor_port_data_4 != prev_motor_port_data_4:
            logging.info(f"Motor 1 snelheid: {motor_port_data_1}, Motor 4 snelheid: {motor_port_data_4}")
            await send_motor_command(client, motor_port_data_1, motor_port_data_4)

            # Update de vorige snelheden
            prev_motor_port_data_1 = motor_port_data_1
            prev_motor_port_data_4 = motor_port_data_4

        await asyncio.sleep(0.001)  # Verlaag de delay tot 1 ms voor snellere controle

async def main():
    logging.info("Laten we beginnen!")
    device = await select_bluetooth_device()

    async with BleakClient(device.address) as client:
        logging.info("Verbonden met BuWizz!")
        
        # Start de motorbesturingslus
        await motor_control(client)

asyncio.run(main())
