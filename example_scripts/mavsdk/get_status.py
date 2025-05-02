import asyncio
from mavsdk import System


async def main():
    # Drohnenobjekt initialisieren und Verbindung herstellen
    drone = System()
    print("starting")
    await drone.connect(system_address="serial:///dev/ttyAMA0:57600")
    print("Verbunden mit Pixhawk --> Abruf von Telemetriedaten")

    # Batteriestatus abrufen
    battery_data = await get_battery_status(drone)
    print(battery_data)


async def get_battery_status(drone):
    """
    Auslesen des aktuellen Batteriestatus (Spannung und verbleibende Prozent)
    von der Drohne mithilfe der MAVSDK-Telemetrie.
    """
    async for battery in drone.telemetry.battery():
        return battery

# Hauptfunktion starten (asyncio Event Loop)
asyncio.run(main())
