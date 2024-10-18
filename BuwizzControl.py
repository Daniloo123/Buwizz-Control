import asyncio
import logging
from bleak import BleakClient, BleakScanner
import sys
import termios
import tty

logging.basicConfig(level="INFO")

# BuWizz Bluetooth service UUID
CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"

# Globale variabelen voor motorsnelheden
motor_port_data_1 = 0  # Snelheid voor motor 1 (poort 1)
motor_port_data_4 = 0  # Snelheid voor motor 4 (poort 4)
max_speed = 127  # Maximale snelheid voor de motoren
speed_increment = 5  # Hoeveelheid waarmee de snelheid per stap toeneemt

# Functie om toetsenbordinput asynchroon te lezen op Unix-systemen
async def read_input():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            yield ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

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

def convert_speed_to_byte(speed):
    """Zet de snelheidswaarde om naar een byte (0-255) voor de motorcontrole"""
    if speed < 0:
        # Voor negatieve snelheden: voeg 256 toe (bijv. -5 wordt 251)
        return 256 + speed
    return speed

async def send_motor_command(client, speed_1, speed_4):
    """Verstuur motorsnelheidscommando naar BuWizz"""
    # Converteer de snelheidswaarden naar bytes (0-255)
    speed_1_byte = convert_speed_to_byte(speed_1)
    speed_4_byte = convert_speed_to_byte(speed_4)

    # Creëer de bytearray voor de motoren
    b_array = bytearray([0x30, speed_1_byte, 0x00, 0x00, speed_4_byte, 0x00, 0x00, 0x00, 0x00])

    logging.info(f"Sending speeds - Motor 1: {speed_1} ({speed_1_byte}), Motor 4: {speed_4} ({speed_4_byte})")
    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, b_array, response=False)

async def motor_control(client):
    global motor_port_data_1, motor_port_data_4
    logging.info("Start de motorbesturingslus...")

    while True:
        # Besturing voor motor 1 (poort 1) met de boven- en onderpijltjes
        if keyboard.is_pressed('up'):
            motor_port_data_1 = min(motor_port_data_1 + speed_increment, max_speed)  # Vooruit
        elif keyboard.is_pressed('down'):
            motor_port_data_1 = max(motor_port_data_1 - speed_increment, -max_speed)  # Achteruit
        else:
            motor_port_data_1 = 0  # Stop motor 1 wanneer er geen toets is ingedrukt

        # Besturing voor motor 4 (poort 4) met de links- en rechtspijltjes
        if keyboard.is_pressed('right'):
            motor_port_data_4 = min(motor_port_data_4 + speed_increment, max_speed)  # Vooruit
        elif keyboard.is_pressed('left'):
            motor_port_data_4 = max(motor_port_data_4 - speed_increment, -max_speed)  # Achteruit
        else:
            motor_port_data_4 = 0  # Stop motor 4 wanneer er geen toets is ingedrukt

        logging.info(f"Motor 1 snelheid: {motor_port_data_1}, Motor 4 snelheid: {motor_port_data_4}")
        await send_motor_command(client, motor_port_data_1, motor_port_data_4)

        await asyncio.sleep(0.1)  # Controleer de snelheid elke 100 ms

async def main():
    logging.info("Laten we beginnen!")
    device = await select_bluetooth_device()

    async with BleakClient(device.address) as client:
        logging.info("Verbonden met BuWizz!")
        motor_task = asyncio.create_task(motor_control(client))

        try:
            await motor_task
        except KeyboardInterrupt:
            logging.info("Beëindiging...")
            motor_task.cancel()

asyncio.run(main())
