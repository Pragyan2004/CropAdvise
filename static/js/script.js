document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupMobileMenu();
    setupFormValidation();
    setupRangeInputs();
    animateStats();
    if (document.querySelector('.dashboard')) {
        initCharts();
    }
    setupScrollAnimations();
}

function setupMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    
    if (hamburger) {
        hamburger.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            hamburger.classList.toggle('active');
        });
    }
    
    const navItems = document.querySelectorAll('.nav-links a');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navLinks.classList.remove('active');
            hamburger.classList.remove('active');
        });
    });
}
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const inputs = this.querySelectorAll('input[required], textarea[required], select[required]');
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    highlightError(input, 'This field is required');
                } else {
                    clearError(input);
                    if (input.type === 'number') {
                        const min = parseFloat(input.min);
                        const max = parseFloat(input.max);
                        const value = parseFloat(input.value);
                        
                        if (!isNaN(min) && value < min) {
                            isValid = false;
                            highlightError(input, `Value must be at least ${min}`);
                        }
                        
                        if (!isNaN(max) && value > max) {
                            isValid = false;
                            highlightError(input, `Value must be at most ${max}`);
                        }
                    }
                    if (input.name === 'ph' && (input.value < 0 || input.value > 14)) {
                        isValid = false;
                        highlightError(input, 'pH must be between 0 and 14');
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Please fix the errors in the form', 'error');
                const firstError = this.querySelector('.error-message');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });
    
    const realTimeInputs = document.querySelectorAll('input[required], textarea[required]');
    realTimeInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (!this.value.trim()) {
                highlightError(this, 'This field is required');
            } else {
                clearError(this);
            }
        });
    });
}

function setupRangeInputs() {
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    rangeInputs.forEach(input => {
        const valueDisplay = document.createElement('div');
        valueDisplay.className = 'range-value';
        valueDisplay.textContent = input.value;
        input.parentNode.appendChild(valueDisplay);
        
        input.addEventListener('input', function() {
            valueDisplay.textContent = this.value;
            const value = (this.value - this.min) / (this.max - this.min) * 100;
            this.style.background = `linear-gradient(to right, var(--primary-color) 0%, var(--primary-color) ${value}%, #e0e0e0 ${value}%, #e0e0e0 100%)`;
        });
        
        const value = (input.value - input.min) / (input.max - input.min) * 100;
        input.style.background = `linear-gradient(to right, var(--primary-color) 0%, var(--primary-color) ${value}%, #e0e0e0 ${value}%, #e0e0e0 100%)`;
    });
}

function highlightError(input, message) {
    clearError(input);
    
    input.style.borderColor = '#d32f2f';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

function clearError(input) {
    input.style.borderColor = '';
    
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        input.parentNode.removeChild(existingError);
    }
}

function showNotification(message, type = 'info') {
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

function animateStats() {
    const counters = document.querySelectorAll('.stat-number');
    if (counters.length === 0) return;
    
    let animated = false;
    
    function checkIfInView() {
        counters.forEach(counter => {
            const position = counter.getBoundingClientRect();
            
            if (position.top < window.innerHeight && position.bottom >= 0) {
                if (!animated) {
                    animated = true;
                    
                    counters.forEach(counter => {
                        const target = +counter.getAttribute('data-target');
                        const count = +counter.innerText;
                        const increment = Math.ceil(target / 200);
                        
                        function updateCount() {
                            if (count < target) {
                                counter.innerText = Math.min(count + increment, target);
                                setTimeout(updateCount, 10);
                            }
                        }
                        
                        updateCount();
                    });
                    
                    window.removeEventListener('scroll', checkIfInView);
                }
            }
        });
    }
    checkIfInView();
    window.addEventListener('scroll', checkIfInView);
}

function setupScrollAnimations() {
    const animatedElements = document.querySelectorAll('.card, .feature-cards .card, .crop-card, .parameter-card');
    
    function checkIfInView() {
        animatedElements.forEach(element => {
            const position = element.getBoundingClientRect();
            
            if (position.top < window.innerHeight - 50 && position.bottom >= 0) {
                element.style.animation = 'fadeInUp 0.8s ease forwards';
                element.style.opacity = '0';
            }
        });
    }
    
    checkIfInView();
    window.addEventListener('scroll', checkIfInView);
}
async function predictCropAPI(formData) {
    try {
        showNotification('Processing your request...', 'info');
        
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Recommendation generated successfully!', 'success');
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
        
        return data;
    } catch (error) {
        console.error('Error:', error);
        showNotification('Network error. Please try again.', 'error');
        return { success: false, error: 'Network error' };
    }
}

function initCharts() {
    console.log('Charts would be initialized here');
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(container => {
        container.style.animation = 'fadeInUp 1s ease forwards';
    });
}
function enhanceCards() {
    const cards = document.querySelectorAll('.card, .crop-card, .parameter-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px)';
            card.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        });
    });
}
enhanceCards();
function setupLoadingButtons() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('.submit-btn');
            if (submitBtn) {
                // Use setTimeout to ensure the form submission starts before disabling
                setTimeout(() => {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                    submitBtn.style.pointerEvents = 'none';
                    submitBtn.style.opacity = '0.7';
                }, 0);
            }
        });
    });
}

setupLoadingButtons();

