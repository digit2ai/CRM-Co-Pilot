// static/js/custom.js
/*
 * Add your custom JavaScript here
 * This file is loaded after main.js, so you can extend or override functionality
 */

// Example custom functionality:

/*
// Add custom keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + N = New Project
    if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
        event.preventDefault();
        if (typeof showModal === 'function') {
            showModal('createProjectModal');
        }
    }
});
*/

/*
// Add custom project card animations
document.addEventListener('DOMContentLoaded', function() {
    const projectCards = document.querySelectorAll('.project-card');
    
    projectCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
});
*/

/*
// Add custom form enhancements
function enhanceForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add floating labels
        const inputs = form.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                if (!this.value) {
                    this.parentElement.classList.remove('focused');
                }
            });
        });
    });
}
*/

/*
// Add custom API response handling
const originalMakeRequest = window.makeRequest;
window.makeRequest = async function(url, method = 'GET', data = null) {
    console.log(`Making ${method} request to ${url}`);
    
    try {
        const result = await originalMakeRequest(url, method, data);
        console.log('Request successful:', result);
        return result;
    } catch (error) {
        console.error('Request failed:', error);
        // Add custom error handling here
        throw error;
    }
};
*/

/*
// Add custom theme switcher
function addThemeSwitcher() {
    const header = document.querySelector('.header');
    const themeButton = document.createElement('button');
    themeButton.className = 'btn btn-secondary';
    themeButton.innerHTML = '🌙';
    themeButton.title = 'Toggle Dark Mode';
    
    themeButton.addEventListener('click', function() {
        document.body.classList.toggle('dark-theme');
        themeButton.innerHTML = document.body.classList.contains('dark-theme') ? '☀️' : '🌙';
        
        // Save preference
        localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
    });
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeButton.innerHTML = '☀️';
    }
    
    header.querySelector('div').appendChild(themeButton);
}
*/

// Initialize custom functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 Custom scripts loaded');
    
    // Uncomment the functions you want to use:
    // enhanceForms();
    // addThemeSwitcher();
    
    // Add your custom initialization code here
});

// Export custom functions if needed
window.CustomProjectManager = {
    // Add your custom functions here
    // example: enhanceForms
};