import asyncio
import logging
import random

from bleak import BleakClient, BleakScanner

"""wuwizz.py
Attempt at running BuWizz device with python3.

In the end we need to be able to:
    V - Connect to the device.
    V - Be able to run some commands and read incoming data. So try to get some
      data first, then we make an attempt at moving this Buwizz.
    - Create all commands and make sure they run reliably. We should be able to
      'input("forward")' for example to send the forward command to the device.
    - Finally, make this app run in the backend for a web UI. 

Sources:
    Official API:
      - https://buwizz.com/BuWizz_3.0_API_3.6_web.pdf
    Getting started with python Bluetooth:
      - https://medium.com/@protobioengineering/how-to-talk-to-bluetooth-devices-with-python-part-1-getting-data-30617bb43985
    bleak readthedocs:
      - https://bleak.readthedocs.io/en/latest/
    bleak examples:
      - https://github.com/hbldh/bleak/tree/master/examples

To-do:
    - Learn about how communication to bluetooth devices work. If we know this,
      the rest of the backend is going to be easy.
      https://novelbits.io/bluetooth-gatt-services-characteristics/
      https://devzone.nordicsemi.com/guides/short-range-guides/b/bluetooth-low-energy/posts/ble-characteristics-a-beginners-tutorial
      https://www.oreilly.com/library/view/getting-started-with/9781491900550/ch04.html
      https://github.com/hbldh/bleak/blob/develop/examples/philips_hue.py
      https://github.com/neozenith/buwizz-pro3-bluetooth-python/tree/main/src/buwizz_pro3_bluetooth_python
"""

"""Import asyncio to run this app asynchronious, logging to log and print,
numpy for converting responses to human readible data, bleak for bluetooth."""

logging.basicConfig(level="INFO")

"""Client Characteristic Configuration Descriptors (CCCD)"""
APPLICATION = "2901"
BOOTLOADER = "8000"
UART1 = "3901"
UART2 = "3902"
UART3 = "3903"
UART4 = "3904"

"""BUWIZZ SERVICE UUID"""
CHARACTERISTIC_APPLICATION_UUID = "50052901-74fb-4481-88b3-9919b1676e93"


async def select_bluetooth_device():
    """Scan for bluetooth devices and select one"""
    while True:
        logging.info("Scanning for devices...")
        devices = await BleakScanner.discover()
        n = 0
        for device in devices:
            logging.info(f"DEVICE: {n}: {device}")
            '''if device.address == "D8:36:DC:FD:9C:F0":
                return device'''
            n += 1
        try:
            selected_device = int(input("Select device number: "))
            device = devices[selected_device]
            return device
        except KeyboardInterrupt:
            exit()
        except (IndexError, UnboundLocalError, ValueError):
            logging.info("Do better")


async def add_cccd(uuid, cccd):
    if len(cccd) != 4:
        logging.info("Come on, man!")
        exit()
    return uuid[:4] + cccd + uuid[8:]


async def convert_rgb(rgb):
    scale = 0xFF
    adjusted = [max(1, chan) for chan in rgb]
    total = sum(adjusted)
    adjusted = [int(round(chan / total * scale)) for chan in adjusted]

    return bytearray([0x36, adjusted[0], adjusted[1], adjusted[2],
                      adjusted[3], adjusted[4], adjusted[5],
                      adjusted[6], adjusted[7], adjusted[8],
                      adjusted[9], adjusted[10], adjusted[11]])


async def taste_the_rainbow():
    color = await convert_rgb([random.randint(0, 256), random.randint(0, 256), random.randint(0, 256),
                         random.randint(0, 256), random.randint(0, 256), random.randint(0, 256),
                         random.randint(0, 256), random.randint(0, 256), random.randint(0, 256),
                         random.randint(0, 256), random.randint(0, 256), random.randint(0, 256)])
    return color


async def main():
    """For now we will make it all work in the CLI. later on we should be able
    to do everything via a GUI"""
    logging.info("Let's do this!")
    """Select a bluetooth device"""
    device = await select_bluetooth_device()

    """Connect to the BuWizz device and keep connection persistant... Check bleak examples for better presistancy."""
    async with BleakClient(device.address) as client:
        for service in client.services:
            logging.info(service.uuid)
            for char in service.characteristics:
                logging.info(char)
        while True:
            try:
                logging.info("Here we go!")
                """Attempts at trying to decipher bluetooth"""

                """Attempt at setting LED status randomly"""
                for i in range(1):
                    """Random colors"""
                    b_array = await taste_the_rainbow()
                    logging.info(b_array)

                    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, b_array, response=False)
                    await asyncio.sleep(.5)

                """Attempt at making a motor move"""
                motor_port_data_1 = 50
                motor_port_data_4 = 10
                # motor_port_data_1 is a signed 8-bit value. Ranges go from -127 to 128.
                # speak 127 converts to -127 and 129 converts to 128 as it goes
                # from 0 to 256 instead of from -127 to 128.
                for i in range(5):
                    motor_port_data_1 += 1
                    # logging.info(f"LOL: {motor_port_data_1}: {motor_port_data_1.to_bytes(1, 'big')}")
                    b_array = bytearray([0x30, motor_port_data_1, 0x00,  0x00, motor_port_data_4, 0x00, 0x00, 0, 0])  # have only check with the first motor data entry
                    await client.write_gatt_char(CHARACTERISTIC_APPLICATION_UUID, b_array, response=False)
                    await asyncio.sleep(3)
                exit()
            except KeyboardInterrupt:
                exit()


asyncio.run(main())
