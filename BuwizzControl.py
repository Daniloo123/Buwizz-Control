from bleak import BleakClient
import asyncio
from random import randint
from time import sleep
import numpy as np
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
                    
                    for i in range(10):
                        CHARACTERISTIC_UUID = "936e2901-1999-b388-8144fb74d1920550" #uit de api docs gehaald door mar
                        CHARACTERISTIC_UUID = "50058000-74fb-4481-88b3-9919b1676e93" #uit de buwizz gehaald
                        CHARACTERISTIC_UUID = "50052901-74fb-4481-88b3-9919b1676e93" #aangepast door mar
                        LED_STATUS = randint(1, 16)
                        nparr = np.array([36, LED_STATUS])
                        data = await client.write_gatt_char(CHARACTERISTIC_UUID, nparr.tobytes())
                        sleep(0.5)
                        exit()
            except Exception as e:
                print(f"Fout bij het verzenden van het commando: {e}")
        else:
            print("Verbinding mislukt")

asyncio.run(control_buwizz())
