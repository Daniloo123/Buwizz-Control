document.getElementById('motor1-slider').addEventListener('input', function () {
    let motor1Speed = this.value;
    fetch('/set_motor_speed', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            motor: 1,
            speed: motor1Speed
        }),
    });
});

document.getElementById('motor4-slider').addEventListener('input', function () {
    let motor4Speed = this.value;
    fetch('/set_motor_speed', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            motor: 4,
            speed: motor4Speed
        }),
    });
});
