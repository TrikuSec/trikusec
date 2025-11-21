/**
 * Modal Dialog Component
 * Reusable modal for confirmations, alerts, and other dialogs
 */

let modalState = {
    onConfirm: null,
    onCancel: null,
    previousFocus: null,
    focusableElements: null,
    firstFocusable: null,
    lastFocusable: null,
};

/**
 * Show modal dialog
 * @param {Object} options - Configuration options
 * @param {string} options.title - Modal title
 * @param {string} options.message - Modal message (can be HTML)
 * @param {string} [options.confirmText='Confirm'] - Confirm button text
 * @param {string} [options.cancelText='Cancel'] - Cancel button text
 * @param {string} [options.variant='danger'] - Variant: 'danger', 'warning', 'info'
 * @param {Function} options.onConfirm - Callback when confirmed
 * @param {Function} [options.onCancel] - Optional callback when cancelled
 */
function showModal(options) {
    const {
        title,
        message,
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        variant = 'danger',
        onConfirm,
        onCancel = null,
    } = options;

    // Store callbacks
    modalState.onConfirm = onConfirm;
    modalState.onCancel = onCancel;

    // Get modal elements
    const backdrop = document.getElementById('modal-backdrop');
    const container = document.getElementById('modal-container');
    const dialog = document.getElementById('modal-dialog');
    const icon = document.getElementById('modal-icon');
    const titleEl = document.getElementById('modal-title');
    const messageEl = document.getElementById('modal-message');
    const confirmButton = document.getElementById('modal-confirm-button');
    const cancelButton = document.getElementById('modal-cancel-button');

    // Set content
    titleEl.textContent = title;
    messageEl.innerHTML = message;

    // Configure variant styles
    const variants = {
        danger: {
            iconBg: 'bg-red-100',
            iconColor: 'text-red-600',
            iconSvg: '<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>',
            confirmBg: 'bg-red-600 hover:bg-red-500',
        },
        warning: {
            iconBg: 'bg-yellow-100',
            iconColor: 'text-yellow-600',
            iconSvg: '<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>',
            confirmBg: 'bg-yellow-600 hover:bg-yellow-500',
        },
        info: {
            iconBg: 'bg-blue-100',
            iconColor: 'text-blue-600',
            iconSvg: '<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" /></svg>',
            confirmBg: 'bg-blue-600 hover:bg-blue-500',
        },
    };

    const variantConfig = variants[variant] || variants.danger;

    // Set icon
    icon.className = `mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full sm:mx-0 sm:h-10 sm:w-10 ${variantConfig.iconBg} ${variantConfig.iconColor}`;
    icon.innerHTML = variantConfig.iconSvg;

    // Set button styles and text
    confirmButton.className = `inline-flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm sm:ml-3 sm:w-auto ${variantConfig.confirmBg}`;
    confirmButton.textContent = confirmText;
    cancelButton.textContent = cancelText;

    // Store previous focus
    modalState.previousFocus = document.activeElement;

    // Show modal
    backdrop.classList.remove('hidden');
    container.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent body scroll

    // Get focusable elements
    const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    modalState.focusableElements = dialog.querySelectorAll(focusableSelectors);
    modalState.firstFocusable = modalState.focusableElements[0];
    modalState.lastFocusable = modalState.focusableElements[modalState.focusableElements.length - 1];

    // Focus first element
    setTimeout(() => {
        confirmButton.focus();
    }, 100);
}

/**
 * Hide modal dialog
 */
function hideModal() {
    const backdrop = document.getElementById('modal-backdrop');
    const container = document.getElementById('modal-container');

    backdrop.classList.add('hidden');
    container.classList.add('hidden');
    document.body.style.overflow = ''; // Restore body scroll

    // Restore previous focus
    if (modalState.previousFocus) {
        modalState.previousFocus.focus();
    }

    // Clear callbacks
    modalState.onConfirm = null;
    modalState.onCancel = null;
    modalState.previousFocus = null;
}

/**
 * Handle confirm button click
 */
function handleModalConfirm() {
    if (modalState.onConfirm) {
        modalState.onConfirm();
    }
    hideModal();
}

/**
 * Handle cancel button click
 */
function handleModalCancel() {
    if (modalState.onCancel) {
        modalState.onCancel();
    }
    hideModal();
}

/**
 * Handle keyboard events
 */
function handleModalKeydown(event) {
    const container = document.getElementById('modal-container');
    if (container.classList.contains('hidden')) {
        return;
    }

    // Escape key closes modal
    if (event.key === 'Escape') {
        handleModalCancel();
        return;
    }

    // Tab key traps focus within modal
    if (event.key === 'Tab') {
        if (event.shiftKey) {
            // Shift+Tab
            if (document.activeElement === modalState.firstFocusable) {
                event.preventDefault();
                modalState.lastFocusable.focus();
            }
        } else {
            // Tab
            if (document.activeElement === modalState.lastFocusable) {
                event.preventDefault();
                modalState.firstFocusable.focus();
            }
        }
    }

    // Enter key on confirm button
    if (event.key === 'Enter' && document.activeElement.id === 'modal-confirm-button') {
        event.preventDefault();
        handleModalConfirm();
    }
}

// Initialize modal event listeners
document.addEventListener('DOMContentLoaded', function() {
    const confirmButton = document.getElementById('modal-confirm-button');
    const cancelButton = document.getElementById('modal-cancel-button');
    const backdrop = document.getElementById('modal-backdrop');

    if (confirmButton) {
        confirmButton.addEventListener('click', handleModalConfirm);
    }

    if (cancelButton) {
        cancelButton.addEventListener('click', handleModalCancel);
    }

    if (backdrop) {
        backdrop.addEventListener('click', handleModalCancel);
    }

    // Keyboard event listener
    document.addEventListener('keydown', handleModalKeydown);
});

