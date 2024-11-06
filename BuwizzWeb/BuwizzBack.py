import asyncio
import logging
from bleak import BleakClient, BleakScanner

logging.basicConfig(level="INFO")

CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"
STATUS_REPORT_UUID = "50052901-74fb-4481-88b3-9919b1676e93"  # UUID voor statusrapport characteristic

async def select_bluetooth_device():
    devices = await BleakScanner.discover()
    for n, device in enumerate(devices):
        logging.info(f"[{n}] {device}")
    index = int(input("Selecteer apparaatindex: "))
    return devices[index]

async def enable_status_notifications(client):
    """Activeer de statusrapport notificaties."""
    await client.start_notify(STATUS_REPORT_UUID, handle_status_report)
    logging.info("Statusrapport notificaties ingeschakeld.")

async def handle_status_report(sender, data):
    """Verwerk het statusrapport om de motorstroom te monitoren."""
    # Motorstromen zijn opgeslagen in bytes 3-8 van het statusrapport
    motor_currents = [byte * 0.015 for byte in data[3:9]]  # Elk byte * 0.015 A
    logging.info(f"Motorstromen: {motor_currents} A")

    # Detecteer limieten door te kijken naar hoge stroomwaarden voor poort 4
    current_motor_4 = motor_currents[3]  # Poort 4
    if current_motor_4 > 0.5:  # Stel een limietwaarde in, bijvoorbeeld 0.5 A
        logging.info("Fysieke limiet gedetecteerd op poort 4.")

async def main():
    device = await select_bluetooth_device()

    async with BleakClient(device.address) as client:
        logging.info("Verbonden met BuWizz.")
        
        # Schakel de statusrapport notificaties in
        await enable_status_notifications(client)

        # Houd de verbinding open om notificaties te ontvangen
        await asyncio.sleep(60)  # Houdt het programma 60 seconden actief voor testen

asyncio.run(main())
