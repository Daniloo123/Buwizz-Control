import asyncio
import logging
from bleak import BleakClient, BleakScanner
import keyboard  # Zorg ervoor dat je deze module hebt geïnstalleerd met `pip install keyboard`
import sys

logging.basicConfig(level="INFO")

CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"

# Globale variabelen voor motorsnelheden en posities
motor_port_data_1 = 0  # Snelheid voor motor 1 (rijden op poort 1)
prev_motor_port_data_1 = None  # Voor controle op verandering
max_speed = 127  # Maximale snelheid voor de motoren
speed_increment = 5  # Hoeveelheid waarmee de snelheid per stap toeneemt voor motor 1

# Variabelen voor de stuurmotor (poort 4)
target_position_4 = 25  # Middenpositie (20 graden)
current_position_4 = 25  # Begin in de middenpositie voor sturen
max_turn = 50  # Maximale draaihoek
min_turn = 0  # Minimale draaihoek
step_turn = 5  # Draaihoek per toetsdruk
speed_factor_4 = 5  # Factor voor stuurresponsiviteit

async def select_bluetooth_device():
    """Scan voor Bluetooth-apparaten en selecteer er een."""
    while True:
        logging.info("Scannen naar apparaten...")
        devices = await BleakScanner.discover()
        n = 0
        for device in devices:
            logging.info(f"[{n}] {device}")
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
    """Verstuur snelheidscommando's naar poort 1 en poort 4."""
    
    # Zet negatieve snelheden om in waardes tussen 128 en 255
    def transform_speed(speed):
        return speed if speed >= 0 else 256 + speed

    # Transformatie van snelheden
    transformed_speed_1 = transform_speed(speed_1)
    transformed_speed_4 = transform_speed(speed_4)

    # Maak de bytearray met de aangepaste snelheden
    b_array = bytearray([0x30, transformed_speed_1, 0x00, 0x00, transformed_speed_4, 0x00, 0x00, 0x00, 0x00])
    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, b_array, response=False)
    logging.debug(f"Verstuur snelheid poort 1: {speed_1}, poort 4: {speed_4}")

async def control_drive_motor(client):
    """Controleer de rijsnelheid op poort 1 op basis van pijltjestoetsen."""
    global motor_port_data_1, prev_motor_port_data_1

    while True:
        # Houd bij of de toets is ingedrukt
        key_pressed = False

        # Pas snelheid aan op basis van 'up' en 'down' toetsen
        if keyboard.is_pressed('down'):
            motor_port_data_1 = min(motor_port_data_1 + speed_increment, max_speed)
            key_pressed = True
        elif keyboard.is_pressed('up'):
            motor_port_data_1 = max(motor_port_data_1 - speed_increment, -max_speed)
            key_pressed = True
        else:
            motor_port_data_1 = 0  # Stop motor 1 wanneer er geen toets is ingedrukt

        # Stuur de snelheid opnieuw als deze veranderd is of als de toets nog steeds is ingedrukt
        if motor_port_data_1 != prev_motor_port_data_1 or key_pressed:
            await send_motor_command(client, motor_port_data_1, 0)  # Poort 4 snelheid op 0 houden
            prev_motor_port_data_1 = motor_port_data_1

        await asyncio.sleep(0.01)  # Pauze voor responsiviteit

async def auto_calibrate_motor(client):
    """Kalibreer de stuurmotor (poort 4) automatisch om linker- en rechterlimieten te vinden."""
    left_limit = None
    right_limit = None
    current_position = 0
    calibration_speed = 80

    # Stap 1: Linkerlimiet detecteren
    logging.info("Beweeg langzaam naar linkerlimiet.")
    while True:
        await send_motor_command(client, 0, -calibration_speed)
        await asyncio.sleep(0.1)
        if current_position <= -50:
            left_limit = current_position
            await send_motor_command(client, 0, 0)
            logging.info(f"Linkerlimiet gedetecteerd op {left_limit} graden.")
            break
        current_position -= 1  # Simuleer positie-update

    # Stap 2: Rechterlimiet detecteren
    logging.info("Beweeg langzaam naar rechterlimiet.")
    current_position = 0  # Reset voor rechterlimiet
    while True:
        await send_motor_command(client, 0, calibration_speed)
        await asyncio.sleep(0.1)
        if current_position >= 50:
            right_limit = current_position
            await send_motor_command(client, 0, 0)
            logging.info(f"Rechterlimiet gedetecteerd op {right_limit} graden.")
            break
        current_position += 1  # Simuleer positie-update

    # Middenpositie berekenen en afstellen
    if left_limit is not None and right_limit is not None:
        rough_center = (left_limit + right_limit) // 2
        logging.info(f"Initieel midden berekend op {rough_center} graden.")
        await fine_tune_to_center(client, rough_center, current_position)

async def fine_tune_to_center(client, center_position, current_position):
    """Beweeg de stuurmotor naar het midden."""
    while abs(center_position - current_position) > 1:
        speed = 50 if center_position > current_position else -51
        await send_motor_command(client, 0, speed)
        current_position += speed * 0.05
        await asyncio.sleep(0.1)

    await send_motor_command(client, 0, 0)
    logging.info("Kalibratie voltooid: Motor staat in het midden.")

async def control_steering_motor(client):
    """Regelt de stuurpositie van poort 4 (met grenzen op links en rechts) op basis van pijltjestoetsen."""
    global current_position_4, target_position_4

    while True:
        # Links/rechts pijltjestoetsen aanpassen binnen de limieten
        if keyboard.is_pressed('right'):
            target_position_4 = max(target_position_4 - step_turn, min_turn)
        elif keyboard.is_pressed('left'):
            target_position_4 = min(target_position_4 + step_turn, max_turn)

        # Snelheid berekenen op basis van afstand tot doelpositie
        distance = target_position_4 - current_position_4
        speed_4 = int(max(min(distance * speed_factor_4, 127), -127))

        # Verzend het stuurcommando en update de huidige positie
        await send_motor_command(client, 0, speed_4)
        current_position_4 += speed_4 * 0.05

        # Stop de motor wanneer het doel is bereikt
        if abs(distance) < step_turn:
            await send_motor_command(client, 0, 0)
            current_position_4 = target_position_4

        await asyncio.sleep(0.02)  # Pauze voor hoge responsiviteit

async def main():
    device = await select_bluetooth_device()

    async with BleakClient(device.address) as client:
        logging.info("Verbonden met BuWizz.")
        
        # Start de kalibratie en besturingstaken
        await auto_calibrate_motor(client)
        drive_task = asyncio.create_task(control_drive_motor(client))
        steering_task = asyncio.create_task(control_steering_motor(client))

        await drive_task
        await steering_task

asyncio.run(main())
