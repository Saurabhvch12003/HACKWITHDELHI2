// Global utility functions and main JavaScript logic

// Toast notification system
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toastId = 'toast-' + Date.now();
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast toast-${type} show`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="toast-header">
            <i class="fas ${iconMap[type]} me-2"></i>
            <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after duration
    setTimeout(() => {
        const toastElement = document.getElementById(toastId);
        if (toastElement) {
            toastElement.remove();
        }
    }, duration);
    
    // Add click handler for close button
    toast.querySelector('.btn-close').addEventListener('click', () => {
        toast.remove();
    });
}

// Loading state management
function setLoadingState(element, loading = true) {
    if (!element) return;
    
    if (loading) {
        element.disabled = true;
        const originalText = element.innerHTML;
        element.setAttribute('data-original-text', originalText);
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    } else {
        element.disabled = false;
        const originalText = element.getAttribute('data-original-text');
        if (originalText) {
            element.innerHTML = originalText;
            element.removeAttribute('data-original-text');
        }
    }
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// Debounce function for search and input handling
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

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!', 'success');
        return true;
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            
            if (successful) {
                showToast('Copied to clipboard!', 'success');
                return true;
            } else {
                throw new Error('Copy command failed');
            }
        } catch (fallbackErr) {
            document.body.removeChild(textArea);
            showToast('Failed to copy to clipboard', 'error');
            return false;
        }
    }
}

// Smooth scrolling to element
function scrollToElement(elementId, offset = 0) {
    const element = document.getElementById(elementId);
    if (element) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }
}

// Local storage utilities
const storage = {
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Failed to save to localStorage:', e);
            return false;
        }
    },
    
    get: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Failed to read from localStorage:', e);
            return defaultValue;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Failed to remove from localStorage:', e);
            return false;
        }
    },
    
    clear: () => {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('Failed to clear localStorage:', e);
            return false;
        }
    }
};

// Theme management
const theme = {
    init: function() {
        const savedTheme = storage.get('theme', 'dark');
        this.set(savedTheme);
    },
    
    set: function(themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        storage.set('theme', themeName);
    },
    
    toggle: function() {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = current === 'dark' ? 'light' : 'dark';
        this.set(newTheme);
        return newTheme;
    }
};

// API request utilities
const api = {
    request: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    get: function(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    },
    
    post: function(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data),
        });
    },
    
    put: function(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },
    
    delete: function(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
};

// Form validation utilities
const validation = {
    rules: {
        required: (value) => value && value.trim() !== '',
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        minLength: (value, min) => value && value.length >= min,
        maxLength: (value, max) => value && value.length <= max,
        number: (value) => !isNaN(value) && !isNaN(parseFloat(value)),
        url: (value) => {
            try {
                new URL(value);
                return true;
            } catch {
                return false;
            }
        }
    },
    
    validate: function(value, rules) {
        const errors = [];
        
        for (const rule of rules) {
            if (typeof rule === 'string') {
                if (!this.rules[rule](value)) {
                    errors.push(`Field must satisfy: ${rule}`);
                }
            } else if (typeof rule === 'object') {
                const { type, param, message } = rule;
                if (!this.rules[type](value, param)) {
                    errors.push(message || `Field must satisfy: ${type}`);
                }
            }
        }
        
        return errors;
    },
    
    validateForm: function(formElement) {
        const errors = {};
        const inputs = formElement.querySelectorAll('[data-validate]');
        
        inputs.forEach(input => {
            const rules = JSON.parse(input.getAttribute('data-validate'));
            const fieldErrors = this.validate(input.value, rules);
            
            if (fieldErrors.length > 0) {
                errors[input.name] = fieldErrors;
                this.showFieldError(input, fieldErrors[0]);
            } else {
                this.hideFieldError(input);
            }
        });
        
        return Object.keys(errors).length === 0;
    },
    
    showFieldError: function(input, message) {
        this.hideFieldError(input);
        
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error text-danger mt-1';
        errorElement.textContent = message;
        
        input.classList.add('is-invalid');
        input.parentNode.appendChild(errorElement);
    },
    
    hideFieldError: function(input) {
        input.classList.remove('is-invalid');
        const existingError = input.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }
};

// Animation utilities
const animations = {
    fadeIn: function(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        const start = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    },
    
    fadeOut: function(element, duration = 300) {
        const start = performance.now();
        const startOpacity = parseFloat(getComputedStyle(element).opacity);
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = startOpacity * (1 - progress);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        };
        
        requestAnimationFrame(animate);
    },
    
    slideDown: function(element, duration = 300) {
        element.style.height = '0px';
        element.style.overflow = 'hidden';
        element.style.display = 'block';
        
        const targetHeight = element.scrollHeight;
        const start = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.height = (targetHeight * progress) + 'px';
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.height = 'auto';
                element.style.overflow = 'visible';
            }
        };
        
        requestAnimationFrame(animate);
    },
    
    slideUp: function(element, duration = 300) {
        const startHeight = element.offsetHeight;
        const start = performance.now();
        
        element.style.overflow = 'hidden';
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.height = (startHeight * (1 - progress)) + 'px';
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
                element.style.height = 'auto';
                element.style.overflow = 'visible';
            }
        };
        
        requestAnimationFrame(animate);
    }
};

// Intersection Observer for animations
const observeAnimations = () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    // Observe elements with animation classes
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
};

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    theme.init();
    
    // Initialize animations
    observeAnimations();
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                setLoadingState(submitBtn, true);
                
                // Reset loading state after 5 seconds as fallback
                setTimeout(() => {
                    setLoadingState(submitBtn, false);
                }, 5000);
            }
        });
    });
    
    // Handle file input styling
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            const label = document.querySelector(`label[for="${this.id}"]`);
            if (label && this.files.length > 0) {
                const fileName = this.files[0].name;
                const fileSize = formatFileSize(this.files[0].size);
                label.textContent = `${fileName} (${fileSize})`;
            }
        });
    });
    
    // Add click-to-copy functionality to code blocks
    document.querySelectorAll('pre code, .code-block').forEach(block => {
        block.style.cursor = 'pointer';
        block.title = 'Click to copy';
        
        block.addEventListener('click', function() {
            copyToClipboard(this.textContent);
        });
    });
    
    // Handle external links
    document.querySelectorAll('a[href^="http"]').forEach(link => {
        if (!link.hasAttribute('target')) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
    
    console.log('🚀 Space Station Tool Detection System initialized');
});

// Handle page visibility change for performance optimization
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause non-critical operations
        console.log('Page hidden - pausing operations');
    } else {
        // Page is visible, resume operations
        console.log('Page visible - resuming operations');
    }
});

// Handle online/offline status
window.addEventListener('online', function() {
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showToast('Connection lost - some features may not work', 'warning');
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(() => {
            const perfData = performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log(`Page load time: ${pageLoadTime}ms`);
            
            // Log to analytics if needed
            if (pageLoadTime > 3000) {
                console.warn('Slow page load detected');
            }
        }, 0);
    });
}

// Export utilities for use in other scripts
window.SpaceToolUtils = {
    showToast,
    setLoadingState,
    formatTimestamp,
    formatFileSize,
    debounce,
    copyToClipboard,
    scrollToElement,
    storage,
    theme,
    api,
    validation,
    animations
};