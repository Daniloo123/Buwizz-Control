bleak import BleakClient
import asyncio
from random import randint
from time import sleep
#50058000-74fb-4481-88b3-9919b1676e93

address = "D8:36:DC:FD:9C:F0"
characteristic_uuid = "50058000-74fb-4481-88b3-9919b1676e93"    #Zorg ervoor dat dit de juiste UUID is

async def control_buwizz():
    async with BleakClient(address) as client:
        if client.is_connected:
            print("Verbonden met BuWizz 3.0")

            try:
                output_level_command = bytearray([0x11, 0x04])
                await client.write_gatt_char(characteristic_uuid, output_level_command)
                print("Output level ingesteld")

                # Houd de verbinding open
                while True:
                    command = input("Voer een commando in of typ 'exit' om de verbinding te verbreken: ")
                    if command.lower() == 'exit':
                        print("Verbinding verbreken...")
                        break
                    elif command.lower() == '1':
                        #Motor 1 met snelheid 100 laten draaien
                        motor_1_command = bytearray([0x10, 50, 176, 0, 0, 0x00])
                        await client.write_gatt_char(characteristic_uuid, motor_1_command)
                        print("Motor 1 commando verzonden")
                    elif command.lower() == 'stop':
                        stop_command = bytearray([0x10, 0, 0, 0, 0, 0x00])
                        await client.write_gatt_char(characteristic_uuid, stop_command)
                        print("Alle motoren gestopt")

            except Exception as e:
                print(f"Fout bij het verzenden van het commando: {e}")
        else:
            print("Verbinding mislukt")

asyncio.run(control_buwizz())
