let selectedDeviceAddress = null;

async function scanDevices() {
    // Toon de scan-knop niet zichtbaar als het scannen bezig is, of zet iets anders om aan te geven dat de scan loopt
    const connectButton = document.getElementById('connect-btn');
    connectButton.style.display = "none";  // Verberg de connect-knop tijdens de scan

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
}

function selectDevice(address, listItem) {
    selectedDeviceAddress = address;
    document.getElementById('connect-btn').disabled = false;

    // Mark the selected item
    document.querySelectorAll('.device-item').forEach(item => item.classList.remove('selected'));
    listItem.classList.add('selected');
}

async function connectSelectedDevice() {
    if (selectedDeviceAddress) {
        const response = await fetch(`/connect/${selectedDeviceAddress}`);
        const result = await response.json();
        document.getElementById('status-indicator').textContent = result.status;
        document.getElementById('status-indicator').classList.toggle("connected", result.status === "Connected");
    }
}

// Dark mode toggle
// Haal de dark mode switch op
const darkModeSwitch = document.getElementById('darkModeSwitch');

// Controleer de opgeslagen dark mode instelling bij het laden van de pagina
if (localStorage.getItem('darkMode') === 'enabled') {
    document.body.classList.add('dark-mode');
    darkModeSwitch.checked = true; // Zorg ervoor dat de toggle in de juiste staat staat
}

// Voeg een event listener toe om de dark mode in te schakelen of uit te schakelen
darkModeSwitch.addEventListener('change', () => {
    if (darkModeSwitch.checked) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'enabled'); // Bewaar de voorkeur in localStorage
    } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'disabled'); // Bewaar de voorkeur in localStorage
    }
});


