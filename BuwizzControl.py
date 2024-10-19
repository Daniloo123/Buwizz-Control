import asyncio
import logging
from bleak import BleakClient, BleakScanner
import keyboard  # Zorg ervoor dat je deze module hebt geïnstalleerd met `pip install keyboard`
import sys
import struct

logging.basicConfig(level="INFO")

# BuWizz Bluetooth service UUID
CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"

# Globale variabelen voor motorsnelheden en servoposities
motor_port_data_1 = 0  # Snelheid voor motor 1 (poort 1)
motor_port_data_4 = 0  # Hoek voor motor 4 (poort 4) als servo
prev_motor_port_data_1 = None  # Voor controle op verandering
prev_motor_port_data_4 = None  # Voor controle op verandering
max_speed = 127  # Maximale snelheid voor de motoren
max_position = 90  # Maximale positie voor de servo
min_position = -90  # Minimale positie voor de servo
speed_increment = 5  # Hoeveelheid waarmee de snelheid per stap toeneemt voor motor 1
position_increment = 5  # Hoeveelheid waarmee de servopositie per stap verandert voor motor 4

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

async def send_motor_command(client, speed_1, position_4):
    """Verstuur motorsnelheidscommando naar BuWizz met commando 0x31, waarbij motor 4 als servo is ingesteld"""

    # Zet de snelheid om naar een 32-bit gesigneerde waarde voor motor 1
    motor_1_ref = struct.pack("<i", speed_1)  # Little-endian gesigneerde 32-bit int

    # Poorten 2 en 3 worden niet gebruikt, dus stel ze in op 0
    motor_2_ref = struct.pack("<i", 0)
    motor_3_ref = struct.pack("<i", 0)

    # Motor 4 als servo: De positie wordt gebruikt (bijvoorbeeld graden -90 tot +90)
    motor_4_ref = struct.pack("<i", position_4)  # Little-endian gesigneerde 32-bit int voor servo-positie

    # Poorten 5 en 6 worden niet gebruikt, stel ze in op 0
    motor_5_6_ref = bytearray([0x00, 0x00])

    # Brake flags (bijv. geen rem, dus alles op 0)
    brake_flags = 0x00

    # LUT-opties (standaard uitgeschakeld, zet alles op 0)
    lut_options = 0x00

    # Bouw de volledige bytearray op
    b_array = bytearray([0x31])  # Commando byte 0x31
    b_array += motor_1_ref      # 4 bytes voor motor 1 (snelheid)
    b_array += motor_2_ref      # 4 bytes voor motor 2
    b_array += motor_3_ref      # 4 bytes voor motor 3
    b_array += motor_4_ref      # 4 bytes voor motor 4 (positie)
    b_array += motor_5_6_ref    # 2 bytes voor motor 5 en 6
    b_array += bytearray([brake_flags, lut_options])  # Brake flags en LUT opties

    # Stuur de bytearray naar het apparaat
    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, b_array, response=False)

async def check_and_center_servo(client):
    """Controleer de initiële positie van de servo en centreer deze indien nodig."""
    logging.info("Controleren van de servo positie bij opstarten...")

    # Zet de servo naar 90 graden
    await send_motor_command(client, 0, 90)  # Stuur de servo naar 90 graden
    await asyncio.sleep(1)  # Wacht even zodat de servo tijd heeft om te bewegen

    # Zet de servo naar 0 graden
    await send_motor_command(client, 0, 0)  # Stuur de servo naar de neutrale positie (0 graden)
    await asyncio.sleep(1)  # Wacht even zodat de servo tijd heeft om te bewegen

async def motor_control(client):
    global motor_port_data_1, motor_port_data_4, prev_motor_port_data_1, prev_motor_port_data_4
    logging.info("Start de motorbesturingslus...")

    while True:
        # Besturing voor motor 1 (poort 1) met de boven- en onderpijltjes
        if keyboard.is_pressed('down'):
            motor_port_data_1 = min(motor_port_data_1 + speed_increment, max_speed)  # Vooruit
        elif keyboard.is_pressed('up'):
            motor_port_data_1 = max(motor_port_data_1 - speed_increment, -max_speed)  # Achteruit
        else:
            motor_port_data_1 = 0  # Stop motor 1 wanneer er geen toets is ingedrukt

        # Besturing voor motor 4 (poort 4) met de links- en rechtspijltjes
        if keyboard.is_pressed('left'):
            motor_port_data_4 = max(motor_port_data_4 - position_increment, min_position)  # Draaien naar links
        elif keyboard.is_pressed('right'):
            motor_port_data_4 = min(motor_port_data_4 + position_increment, max_position)  # Draaien naar rechts
    
        # Alleen verzenden als de snelheid of positie veranderd is
        if motor_port_data_1 != prev_motor_port_data_1 or motor_port_data_4 != prev_motor_port_data_4:
            logging.info(f"Motor 1 snelheid: {motor_port_data_1}, Motor 4 positie: {motor_port_data_4}")
            await send_motor_command(client, motor_port_data_1, motor_port_data_4)

            # Update de vorige snelheden en posities
            prev_motor_port_data_1 = motor_port_data_1
            prev_motor_port_data_4 = motor_port_data_4

        await asyncio.sleep(0.001)  # Verlaag de delay tot 1 ms voor snellere controle

async def check_for_exit():
    """Luister naar terminal-invoer en stop het programma bij invoer van '!'"""
    while True:
        user_input = await asyncio.to_thread(sys.stdin.read, 1)  # Lees één karakter uit de terminal
        if user_input == '!':
            logging.info("Beëindiging door invoer van '!'.")
            sys.exit(0)  # Beëindig het programma netjes

async def main():
    logging.info("Laten we beginnen!")
    device = await select_bluetooth_device()

    async with BleakClient(device.address) as client:
        logging.info("Verbonden met BuWizz!")

        # Controleer en centreer de servo bij opstarten
        await check_and_center_servo(client)
        
        # Start de motorbesturingslus en de invoerluistertaak
        motor_task = asyncio.create_task(motor_control(client))
        exit_task = asyncio.create_task(check_for_exit())

        try:
            await motor_task
            await exit_task
        except KeyboardInterrupt:
            logging.info("Beëindiging door toetsenbordonderbreking...")
            motor_task.cancel()
            exit_task.cancel()

asyncio.run(main())
