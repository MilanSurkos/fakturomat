/**
 * main.js - Site-wide JavaScript
 * 
 * This file contains site-wide JavaScript functionality that's not specific to any single page.
 * For invoice form functionality, see invoices/static/invoices/js/invoice-form.js
 */

/**
 * Display an error message to the user in a consistent way
 * @param {string} message - The error message to display
 */
function showErrorToUser(message) {
    // Check if we have a toast notification system
    const toastContainer = document.getElementById('toast-container');
    if (toastContainer && typeof bootstrap !== 'undefined') {
        // Use Bootstrap toast if available
        const toastEl = document.createElement('div');
        toastEl.className = 'toast align-items-center text-white bg-danger border-0';
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        
        // Remove the toast after it's hidden
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    } else {
        // Fallback to alert if no toast system is available
        alert(message);
    }
}

// Global error handler for uncaught exceptions
window.addEventListener('error', function(event) {
    console.error('Uncaught error:', event.error || event.message, event);
    
    // Don't show error message for errors from scripts in other domains
    if (event.filename && !event.filename.startsWith(window.location.origin) && 
        !event.filename.startsWith(window.location.hostname) &&
        !event.filename.startsWith('/')) {
        return;
    }
    
    // Show a user-friendly error message
    const errorMessage = event.error?.message || 'An unexpected error occurred. Please try again.';
    showErrorToUser(errorMessage);
});

// Initialize any site-wide functionality when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Site initialized');
    
    // Add any site-wide initialization code here
    // For example, tooltips, modals, or other global UI components
    
    // Example: Initialize Bootstrap tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
        }
      }
    } else {
      console.log('No invoice form found on this page');
    }
    
    console.log('Application initialization completed successfully');
    
  } catch (error) {
    console.error('Error during application initialization:', error);
    showErrorToUser('An error occurred while initializing the application. Please refresh the page and try again.');
  }
});

/**
 * Display an error message to the user
 * @param {string} message - The error message to display
 */
function showErrorToUser(message) {
  try {
    console.error('Showing error to user:', message);
    
    // Create error element if it doesn't exist
    let errorContainer = document.getElementById('error-container');
    if (!errorContainer) {
      errorContainer = document.createElement('div');
      errorContainer.id = 'error-container';
      document.body.prepend(errorContainer);
    }
    
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    errorContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
      try {
        const alert = new bootstrap.Alert(alertDiv);
        alert.close();
      } catch (e) {
        console.error('Error dismissing alert:', e);
      }
    }, 10000);
    
  } catch (error) {
    console.error('Error showing error message to user:', error);
    // Last resort - use alert
    alert(message);
  }
}

// Global error handler for uncaught exceptions
window.addEventListener('error', function(event) {
  console.error('Uncaught error:', event.error || event.message, event);
  showErrorToUser('An unexpected error occurred. Please try again.');
  return false; // Prevent default browser error handling
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
  console.error('Unhandled promise rejection:', event.reason);
  showErrorToUser('An unexpected error occurred. Please try again.');
  event.preventDefault(); // Prevent default browser error handling
});
