// static/js/main.js

// Global JavaScript functions for the Project Manager application

/**
 * Show modal by ID
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
}

/**
 * Hide modal by ID
 */
function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
    }
}

/**
 * Show alert notification
 */
function showAlert(message, type = 'success') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    document.body.appendChild(alertDiv);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 4000);

    // Allow manual removal by clicking
    alertDiv.addEventListener('click', () => {
        alertDiv.remove();
    });
}

/**
 * Show loading spinner on button
 */
function showLoading(buttonElement, originalText) {
    buttonElement.disabled = true;
    buttonElement.innerHTML = `<span class="spinner"></span> ${originalText || 'Loading...'}`;
}

/**
 * Hide loading spinner on button
 */
function hideLoading(buttonElement, originalText) {
    buttonElement.disabled = false;
    buttonElement.innerHTML = originalText;
}

/**
 * Make HTTP request with error handling
 */
async function makeRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        
        // Handle different response types
        let result;
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            result = await response.json();
        } else {
            result = await response.text();
        }
        
        if (!response.ok) {
            throw new Error(result.message || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return result;
    } catch (error) {
        console.error('Request failed:', error);
        showAlert(error.message, 'error');
        throw error;
    }
}

/**
 * Confirm action with user
 */
function confirmAction(message, onConfirm, onCancel = null) {
    if (confirm(message)) {
        onConfirm();
    } else if (onCancel) {
        onCancel();
    }
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'Not set';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format relative time (e.g., "2 days ago")
 */
function formatRelativeTime(dateString) {
    if (!dateString) return 'Unknown';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    
    return `${Math.floor(diffDays / 365)} years ago`;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Toggle element visibility
 */
function toggleVisibility(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Smooth scroll to element
 */
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showAlert('Copied to clipboard!', 'success');
    } catch (err) {
        console.error('Failed to copy: ', err);
        showAlert('Failed to copy to clipboard', 'error');
    }
}

/**
 * Form validation helper
 */
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#de350b';
            isValid = false;
        } else {
            field.style.borderColor = '#dfe1e6';
        }
    });
    
    return isValid;
}

/**
 * Reset form validation styles
 */
function resetFormValidation(formElement) {
    const fields = formElement.querySelectorAll('.form-control');
    fields.forEach(field => {
        field.style.borderColor = '#dfe1e6';
    });
}

/**
 * Auto-resize textarea
 */
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

/**
 * Initialize tooltips (if you want to add them later)
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const text = event.target.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #172b4d;
        color: white;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        z-index: 1002;
        white-space: nowrap;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = event.target.getBoundingClientRect();
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
    
    event.target._tooltip = tooltip;
}

function hideTooltip(event) {
    const tooltip = event.target._tooltip;
    if (tooltip) {
        tooltip.remove();
        delete event.target._tooltip;
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Close modal when clicking outside
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    };

    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal[style*="block"]');
            openModals.forEach(modal => {
                modal.style.display = 'none';
            });
            document.body.style.overflow = 'auto';
        }
    });

    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', () => autoResizeTextarea(textarea));
        autoResizeTextarea(textarea); // Initial resize
    });

    // Form validation on submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(form)) {
                event.preventDefault();
                showAlert('Please fill in all required fields', 'error');
            }
        });
    });

    // Initialize tooltips
    initTooltips();

    // Add loading states to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        if (button.type === 'submit') {
            button.addEventListener('click', function() {
                const form = button.closest('form');
                if (form && validateForm(form)) {
                    const originalText = button.textContent;
                    showLoading(button, 'Saving...');
                    
                    // Reset after form submission (adjust timing as needed)
                    setTimeout(() => {
                        hideLoading(button, originalText);
                    }, 2000);
                }
            });
        }
    });

    console.log('🏋️ Project Manager initialized successfully!');
});

// Export functions for use in other scripts
window.ProjectManager = {
    showModal,
    hideModal,
    showAlert,
    makeRequest,
    confirmAction,
    formatDate,
    formatRelativeTime,
    escapeHtml,
    debounce,
    toggleVisibility,
    scrollToElement,
    copyToClipboard,
    validateForm,
    resetFormValidation,
    autoResizeTextarea,
    showLoading,
    hideLoading
};