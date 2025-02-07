$(document).ready(function() {
    const dropBox = $('#drop-box');
    const resultBox = $('#result');
    const numberInput = $('#number-input');
    const chart1Image = $('#chart1-img');
    const chart2Image = $('#chart2-img');
    const chart3Image = $('#chart3-img');
    const chart4Image = $('#chart4-img');
    const chart5Image = $('#chart5-img');
    const chart6Image = $('#chart6-img');
    const chart7Image = $('#chart7-img');
    const chart8Image = $('#chart8-img');
    const chart9Image = $('#chart9-img');
    const chart10Image = $('#chart10-img');
    const chart11Image = $('#chart11-img');
    const chart12Image = $('#chart12-img');
    //TÄNNE AINA LISÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ------------
    const csvDownloadLink = $('#csv-download-link');

    // Handle drag over event
    dropBox.on('dragover', function(event) {
        event.preventDefault();
        dropBox.addClass('dragover');
    });

    // Handle drag leave event
    dropBox.on('dragleave', function(event) {
        dropBox.removeClass('dragover');
    });

    // Handle drop event
    dropBox.on('drop', function(event) {
        event.preventDefault();
        dropBox.removeClass('dragover');
        
        // Get the file from the drop
        const file = event.originalEvent.dataTransfer.files[0];
        const numberValue = numberInput.val(); // Get the number from input field

        if (file && file.type === 'text/csv' && numberValue) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('number', numberValue); // Add the number value to the form data

            // Send the file to the server using AJAX
            $.ajax({
                url: '/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {

                    // Reset images (hide previously displayed ones)
                    chart1Image.hide();
                    chart2Image.hide();
                    chart3Image.hide();
                    chart4Image.hide();
                    chart5Image.hide();
                    chart6Image.hide();
                    chart7Image.hide();
                    chart8Image.hide();
                    chart9Image.hide();
                    chart10Image.hide();
                    chart11Image.hide();
                    chart12Image.hide();


                    if (response.chart1) {
                        chart1Image.attr('src', response.chart1).show();
                        chart1Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart2) {
                        chart2Image.attr('src', response.chart2).show();
                        chart2Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart3) {
                        chart3Image.attr('src', response.chart3).show();
                        chart3Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart4) {
                        chart4Image.attr('src', response.chart4).show();
                        chart4Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart5) {
                        chart5Image.attr('src', response.chart5).show();
                        chart5Image.css({'width': '80%', 'max-width': '400px', 'height': 'auto'});
                    }
                    if (response.chart6) {
                        chart6Image.attr('src', response.chart6).show();
                        chart6Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart7) {
                        chart7Image.attr('src', response.chart7).show();
                        chart7Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart8) {
                        chart8Image.attr('src', response.chart8).show();
                        chart8Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart9) {
                        chart9Image.attr('src', response.chart9).show();
                        chart9Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart10) {
                        chart10Image.attr('src', response.chart10).show();
                        chart10Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart11) {
                        chart11Image.attr('src', response.chart11).show();
                        chart11Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }
                    if (response.chart12) {
                        chart12Image.attr('src', response.chart12).show();
                        chart12Image.css({'width': '80%', 'max-width': '1200px', 'height': 'auto'});
                    }

                },
                error: function(xhr, status, error) {
                    const err = xhr.responseJSON || {};
                    resultBox.html(`Error: ${err.error || error}`);
                }
            });
        } else {
            resultBox.html('Please drop a valid CSV file.');
        }
    });
});