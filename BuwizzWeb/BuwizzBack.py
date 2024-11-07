import asyncio
import logging
from bleak import BleakClient, BleakScanner
import keyboard  # Zorg ervoor dat je deze module hebt geïnstalleerd met `pip install keyboard`

logging.basicConfig(level="INFO")

CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"

async def select_bluetooth_device():
    devices = await BleakScanner.discover()
    for n, device in enumerate(devices):
        logging.info(f"[{n}] {device}")
    index = int(input("Selecteer apparaatindex: "))
    return devices[index]

async def send_speed_command(client, speed):
    """Stuur een snelheidscommando naar de motor op poort 4."""
    command = bytearray([0x30] + [0x00]*6 + [0x00]*2)
    command[4] = speed & 0xFF  # Snelheid voor poort 4
    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, command, response=False)
    logging.debug(f"Verstuur snelheid: {speed}")

async def auto_calibrate_motor(client):
    """Automatische kalibratie: bepaal linker- en rechterlimieten en bereken midden."""
    left_limit = None
    right_limit = None
    current_position = 0
    calibration_speed = 80  # Gematigde snelheid voor limietdetectie

    # Stap 1: Beweeg naar de linkerlimiet
    logging.info("Beweeg langzaam naar linkerlimiet.")
    while True:
        await send_speed_command(client, -calibration_speed)  # Beweeg naar links met gematigde snelheid
        await asyncio.sleep(0.1)

        # Simuleer detectie van linkerlimiet (bijv. door toename in weerstand)
        if current_position <= -40:  # Stel -40 in als fictieve linkerlimiet
            left_limit = current_position
            await send_speed_command(client, 0)  # Stop de motor
            logging.info(f"Linkerlimiet gedetecteerd op {left_limit} graden.")
            break
        current_position -= 1  # Simuleer positie-update naar links

    # Stap 2: Beweeg naar de rechterlimiet
    logging.info("Beweeg langzaam naar rechterlimiet.")
    current_position = 0  # Reset fictieve positie voor de simulatie
    while True:
        await send_speed_command(client, calibration_speed)  # Beweeg naar rechts met gematigde snelheid
        await asyncio.sleep(0.1)

        # Simuleer detectie van rechterlimiet (bijv. door toename in weerstand)
        if current_position >= 40:  # Stel 40 in als fictieve rechterlimiet
            right_limit = current_position
            await send_speed_command(client, 0)  # Stop de motor
            logging.info(f"Rechterlimiet gedetecteerd op {right_limit} graden.")
            break
        current_position += 1  # Simuleer positie-update naar rechts

    # Stap 3: Bereken het midden en fijne afstemming
    if left_limit is not None and right_limit is not None:
        rough_center = (left_limit + right_limit) // 2
        logging.info(f"Initieel midden berekend op {rough_center} graden.")

        # Beweeg naar het berekende midden
        await fine_tune_to_center(client, rough_center, current_position)

async def fine_tune_to_center(client, center_position, current_position):
    """Beweeg de motor langzaam naar het midden voor nauwkeurige afstemming."""
    logging.info("Start fijne afstemming voor middenpositie.")
    while abs(center_position - current_position) > 1:
        # Bereken de snelheid en richting naar het midden
        speed = 50 if center_position > current_position else -51
        await send_speed_command(client, speed)
        current_position += speed * 0.05  # Simuleer de positieverandering
        await asyncio.sleep(0.1)

    # Stop de motor bij het bereiken van het midden
    await send_speed_command(client, 0)
    logging.info("Kalibratie voltooid: Motor staat nauwkeurig in het midden.")

async def pseudo_servo_control(client):
    """Controleer de motorpositie als pseudo-servo met pijltjestoetsen."""
    target_position = 20  # Middenpositie (20 graden)
    max_turn = 40  # Maximale draaihoek in graden
    min_turn = 0   # Minimale draaihoek in graden
    step = 5       # Hoeveel graden per toetsdruk
    current_position = 20  # Begin in de middenpositie
    speed_factor = 5       # Verhoogde factor voor snellere respons

    while True:
        # Pas doelpositie aan op basis van pijltjestoetsen
        if keyboard.is_pressed('left'):
            target_position = max(target_position - step, min_turn)
            logging.debug(f"Linkerpijl ingedrukt. Nieuwe doelpositie: {target_position}")
        elif keyboard.is_pressed('right'):
            target_position = min(target_position + step, max_turn)
            logging.debug(f"Rechterpijl ingedrukt. Nieuwe doelpositie: {target_position}")

        # Bereken snelheid op basis van afstand tot de doelpositie
        distance = target_position - current_position
        speed = int(max(min(distance * speed_factor, 127), -127))  # Verhoogde snelheidslimiet [-127, 127]

        # Verstuur snelheidscommando en simuleer positie-update
        await send_speed_command(client, speed)
        current_position += speed * 0.05  # Snellere update voor current_position

        # Stop de motor wanneer de doelpositie is bereikt
        if abs(distance) < step:
            await send_speed_command(client, 0)
            current_position = target_position  # Update huidige positie naar doelpositie

        await asyncio.sleep(0.02)  # Kortere pauze voor hogere responsiviteit

async def main():
    device = await select_bluetooth_device()

    async with BleakClient(device.address) as client:
        logging.info("Verbonden met BuWizz.")
        
        # Voer automatische kalibratie uit met langzamere limietdetectie
        await auto_calibrate_motor(client)
        
        # Start de real-time besturing met pijltjestoetsen
        await pseudo_servo_control(client)

asyncio.run(main())
