let selectedDeviceAddress = null;

async function scanDevices() {
    // Toon de scan-knop niet zichtbaar als het scannen bezig is, of zet iets anders om aan te geven dat de scan loopt
    const connectButton = document.getElementById('connect-btn');
    const scanButton = document.getElementById('scan-btn');
    connectButton.style.display = "none";  // Verberg de connect-knop tijdens de scan
    scanButton.style.display = "none";    // Verberg de scan-knop tijdens het scannen

    const response = await fetch('/scan');
    const devices = await response.json();
    const devicesList = document.getElementById('devices');
    devicesList.innerHTML = '';  // Maak de lijst leeg voordat we nieuwe apparaten toevoegen

    if (devices.length > 0) {
        devices.forEach(device => {
            const listItem = document.createElement('li');
            listItem.textContent = `${device.name} - ${device.address}`;
            listItem.classList.add("device-item");
            listItem.onclick = () => selectDevice(device.address, listItem);
            devicesList.appendChild(listItem);
        });

        // Maak de "Connect"-knop zichtbaar nadat de scan is voltooid
        connectButton.style.display = "inline-block"; // Maak de knop zichtbaar
        connectButton.disabled = false; // Zet de knop in een actieve toestand
    } else {
        alert('No devices found.');
    }

    // Herstel de scan-knop zodra de scan is voltooid
    scanButton.style.display = "inline-block";  // Maak de scan-knop weer zichtbaar
}

function selectDevice(address, listItem) {
    selectedDeviceAddress = address;
    document.getElementById('connect-btn').disabled = false;

    // Markeer de geselecteerde item
    document.querySelectorAll('.device-item').forEach(item => item.classList.remove('selected'));
    listItem.classList.add('selected');
}

async function connectSelectedDevice() {
    if (selectedDeviceAddress) {
        try {
            // Stuur een POST-verzoek naar de server met het geselecteerde apparaatadres
            const response = await fetch('/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ device_address: selectedDeviceAddress })
            });

            // Controleer of de response van de server succesvol was
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json(); // Verkrijg het resultaat van de server
            console.log('Server response:', result); // Log de server response voor debugging

            alert(result.message); // Toon een alert met het serverbericht

            // Update de statusindicator en voeg de klasse "connected" toe als verbonden
            document.getElementById('status-indicator').textContent = "Connected";
            document.getElementById('status-indicator').classList.remove("disconnected");
            document.getElementById('status-indicator').classList.add("connected");

            // Verberg de connect-knop en toon enkel het verbonden apparaat in de lijst
            document.getElementById('connect-btn').style.display = "none"; // Verberg de connect knop
            document.getElementById('scan-btn').style.display = "none"; // Verberg de scan knop

            // Markeer de verbonden item in de lijst en zorg dat alleen deze zichtbaar is
            const deviceItems = document.querySelectorAll('.device-item');
            deviceItems.forEach(item => {
                if (item.textContent.includes(selectedDeviceAddress)) {
                    item.classList.add('connected');
                } else {
                    item.style.display = 'none';  // Verberg andere apparaten
                }
            });

        } catch (error) {
            console.error('Connection failed:', error);
            alert('Connection failed. Please try again.');
        }
    } else {
        alert('Please select a Bluetooth device to connect.');
    }
}

// Functie om de verbinding te verbreken
async function disconnectDevice() {
    try {
        // Verzenden van de POST-aanroep naar de /disconnect route van de server
        const response = await fetch('/disconnect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Verwerken van de JSON-response
        const result = await response.json();

        if (response.ok) {
            // Indien succesvol, geef een bericht weer
            alert(result.message);

            // Controleer of de server een instructie geeft om de pagina te verversen
            if (result.refresh) {
                // Verfris de pagina
                window.location.reload();
            } else {
                // Update de UI of schakelt knoppen in/uit
                updateButtonStates(false);  // Bijv. schakelt de connectieknop weer in
            }
        } else {
            // Bij een mislukking, geef een foutmelding weer
            alert(`Error: ${result.message}`);
        }
    } catch (error) {
        // Bij een netwerk- of serverfout
        alert("Er is een fout opgetreden bij het verbreken van de verbinding.");
        console.error(error);
    }
}

