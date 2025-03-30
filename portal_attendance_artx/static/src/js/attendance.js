odoo.define('portal_attendance_artx.attendance', [], function (require) {
    console.log('hey I am Mohammad!');

    var isCheckIn = true;  // Default to true, assuming initial action is Check-In

    // Function to update button status and color by checking attendance status
    var updateButtonStatus = async function() {
        try {
            const response = await fetch('/portal/get_attendance_status', {
                method: 'GET'
            });
            const data = await response.json();  // Parse the JSON response

            const button = document.getElementById('attendanceBtn');
            const btnText = document.getElementById('btnText');

            if (data.success) {
                if (data.message === 'Currently checked in') {
                    btnText.textContent = 'Click to Check Out';
                    button.classList.remove('btn-success');
                    button.classList.add('btn-danger');  // Make it red for Check-Out
                    isCheckIn = false;  // Next action will be check-out
                } else {
                    btnText.textContent = 'Click to Check In';
                    button.classList.remove('btn-danger');
                    button.classList.add('btn-success');  // Make it green for Check-In
                    isCheckIn = true;  // Next action will be check-in
                }
            } else {
                btnText.textContent = 'Click to Check In';
                button.classList.remove('btn-danger');
                button.classList.add('btn-success');  // Default to green if unknown
                isCheckIn = true;
            }
        } catch (error) {
            console.error('Error fetching attendance status:', error);
            btnText.textContent = 'Click to Check In';
            button.classList.remove('btn-danger');
            button.classList.add('btn-success');
            isCheckIn = true;  // On error, assume next action is check-in
        }
    };

    // Function to handle button click for check-in/check-out
    var _onButton = async function(e) {
        const currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');

        let formData = new FormData();
        if (isCheckIn) {
            formData.append('check_in', currentTime);  // Append check-in time
        } else {
            formData.append('check_out', currentTime);  // Append check-out time
        }

        try {
            const response = await fetch('/portal/add_attendance', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();  // Parse the JSON response

            if (data.success) {
                // Toggle button state and colors
                const button = document.getElementById('attendanceBtn');
                const btnText = document.getElementById('btnText');

                if (isCheckIn) {
                    btnText.textContent = 'Click to Check Out';
                    button.classList.remove('btn-success');
                    button.classList.add('btn-danger');  // Set to red for check-out
                } else {
                    btnText.textContent = 'Click to Check In';
                    button.classList.remove('btn-danger');
                    button.classList.add('btn-success');  // Set to green for check-in
                }

                isCheckIn = !isCheckIn;  // Toggle the state for next action
            } else {
                alert('Failed to record attendance: ' + data.message);
            }
        } catch (error) {
            alert('An error occurred while recording attendance');
            console.error(error);
        }
    };

    // Attach the event listener to the button
    var button = document.getElementById("attendanceBtn");
    if (button) {
        button.addEventListener('click', _onButton);
        updateButtonStatus();  // Check the current status when the page loads
    }
});
