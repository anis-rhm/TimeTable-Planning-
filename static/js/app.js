// JavaScript for the timetable generator application

document.addEventListener('DOMContentLoaded', function() {
    const generateForm = document.getElementById('generateForm');
    const generateBtn = document.getElementById('generateBtn');
    
    if (generateForm && generateBtn) {
        generateForm.addEventListener('submit', function(e) {
            // Add loading state to button
            generateBtn.classList.add('btn-loading');
            generateBtn.disabled = true;
            
            // Show progress indication
            showProgress();
        });
    }
    
    // Form validation
    const generationsInput = document.getElementById('generations');
    const populationInput = document.getElementById('population_size');
    
    if (generationsInput) {
        generationsInput.addEventListener('input', function() {
            validateInput(this, 50, 1000);
        });
    }
    
    if (populationInput) {
        populationInput.addEventListener('input', function() {
            validateInput(this, 50, 500);
        });
    }
});

function validateInput(input, min, max) {
    const value = parseInt(input.value);
    
    if (value < min || value > max) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
    } else {
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
    }
}

function showProgress() {
    const progressHtml = `
        <div class="progress-container mt-3">
            <div class="alert alert-info">
                <i class="fas fa-cogs me-2"></i>
                <strong>Generating timetable...</strong> This may take a few moments.
            </div>
            <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 100%">
                    Optimizing schedule...
                </div>
            </div>
        </div>
    `;
    
    const form = document.getElementById('generateForm');
    if (form) {
        form.insertAdjacentHTML('afterend', progressHtml);
    }
}

// API functions for future use
async function generateTimetableAPI(generations, populationSize) {
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                generations: generations,
                population_size: populationSize
            })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error generating timetable:', error);
        throw error;
    }
}

// Utility functions
function formatTime(slot) {
    const timeSlots = {
        0: "8:00 - 10:00",
        1: "10:30 - 12:30",
        2: "13:30 - 15:30",
        3: "16:00 - 18:00"
    };
    return timeSlots[slot] || `Slot ${slot + 1}`;
}

function getSessionTypeColor(sessionType) {
    const colors = {
        'theory': '#28a745',
        'practical': '#ffc107',
        'history': '#17a2b8',
        'test': '#dc3545'
    };
    return colors[sessionType.toLowerCase()] || '#007bff';
}

// Export functions for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateTimetableAPI,
        formatTime,
        getSessionTypeColor
    };
}