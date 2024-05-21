document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.start-button').forEach(button => {
        button.addEventListener('click', function() {
            const device = this.getAttribute('data-device');
            const passes = document.querySelector(`input[id="passes-${device}"]`).value;
            const zeroPass = document.querySelector(`input[id="zero_pass-${device}"]`).checked;

            const wipeRequest = {
                device: device,
                passes: passes,
                zero_pass: zeroPass
            };

            fetch('/wipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify([wipeRequest])
            })
            .then(response => response.json())
            .then(data => {
                let progressContainer = document.getElementById('progress-container');
                let errorContainer = document.getElementById('error-container');
                progressContainer.innerHTML = '';
                errorContainer.innerHTML = '';

                data.forEach(result => {
                    if (result.status === 'started') {
                        progressContainer.innerHTML += `Wiping process started for ${result.device}<br>`;
                    } else {
                        errorContainer.innerHTML += `Error for ${result.device}: ${result.message}<br>`;
                    }
                });

                // Start polling for status updates
                setInterval(fetchStatus, 3000);
            });
        });
    });

    document.querySelectorAll('.stop-button').forEach(button => {
        button.addEventListener('click', function() {
            const device = this.getAttribute('data-device');
            fetch('/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ device: device })
            })
            .then(response => response.json())
            .then(data => {
                let progressContainer = document.getElementById('progress-container');
                let errorContainer = document.getElementById('error-container');
                if (data.status === 'stopped') {
                    progressContainer.innerHTML += `Wiping process stopped for ${data.device}<br>`;
                } else {
                    errorContainer.innerHTML += `Error stopping process for ${data.device}<br>`;
                }
            });
        });
    });

    function fetchStatus() {
        fetch('/status')
        .then(response => response.json())
        .then(data => {
            for (const device in data) {
                const statusMessage = data[device];
                document.querySelector(`#error-${device}`).value = statusMessage;
            }
        });
    }
});
