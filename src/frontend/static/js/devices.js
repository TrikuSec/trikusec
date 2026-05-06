// Toggle actions dropdown menu
function toggleActionsMenu() {
    const actionsMenu = document.getElementById('device-actions-menu');
    actionsMenu?.classList.toggle('hidden');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const actionsButton = document.getElementById('device-actions-button');
    const actionsMenu = document.getElementById('device-actions-menu');

    if (actionsButton && actionsMenu && !actionsButton.contains(event.target) && !actionsMenu.contains(event.target)) {
        actionsMenu.classList.add('hidden');
    }
});

// Delete device with confirmation
function deleteDevice(deviceId, hostname) {
    // Get CSRF token first
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                      document.cookie.match(/csrftoken=([^;]+)/)?.[1];

    if (!csrftoken) {
        showModal({
            title: 'Error',
            message: 'CSRF token not found. Please refresh the page and try again.',
            confirmText: 'OK',
            variant: 'danger',
            onConfirm: () => {},
        });
        return;
    }

    // Show confirmation modal
    showModal({
        title: 'Delete Device',
        message: `Are you sure you want to delete device <strong>"${hostname}"</strong>?<br><br>This will permanently remove the device and all its reports.`,
        confirmText: 'Delete',
        cancelText: 'Cancel',
        variant: 'danger',
        onConfirm: () => {
            // Send DELETE request via POST (Django doesn't support DELETE method easily)
            fetch(`/device/${deviceId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Redirect to device list page
                    window.location.href = '/devices/';
                } else {
                    showModal({
                        title: 'Error',
                        message: 'Error deleting device: ' + (data.message || 'Unknown error'),
                        confirmText: 'OK',
                        variant: 'danger',
                        onConfirm: () => {},
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showModal({
                    title: 'Error',
                    message: 'Error deleting device. Please try again.',
                    confirmText: 'OK',
                    variant: 'danger',
                    onConfirm: () => {},
                });
            });
        },
    });
}

// Device search toggle + column customization

const DEVICE_OPTIONAL_COLUMNS = [
    'uptime',
    'trikusec_plugin',
    'antivirus',
    'vulnerable_packages',
    'non_compliant_days',
];
const DEVICE_COLUMN_PREFS_KEY = 'trikusec.device-list.optional-columns.v1';
const DEVICE_MAX_TOTAL_COLUMNS = 10;
// Existing non-optional table columns that remain always visible
const DEVICE_MANDATORY_COLUMNS = 8;

document.addEventListener('DOMContentLoaded', function() {
    const searchContainer = document.getElementById('device-search-container');
    const searchInput = document.getElementById('device-search-input');
    const deviceRows = document.querySelectorAll('tbody tr[data-device-name]');

    const columnsToggleButton = document.getElementById('device-columns-toggle');
    const columnsPanel = document.getElementById('device-columns-panel');
    const columnsLimitMsg = document.getElementById('device-columns-limit-msg');
    const columnCheckboxes = document.querySelectorAll('[data-column-checkbox]');

    function filterDevices(term) {
        const normalized = term.trim().toLowerCase();

        deviceRows.forEach((row) => {
            const deviceName = row.getAttribute('data-device-name') || '';
            const matches = !normalized || deviceName.includes(normalized);
            row.classList.toggle('hidden', !matches);
        });
    }

    function loadOptionalColumnsPreference() {
        try {
            const raw = localStorage.getItem(DEVICE_COLUMN_PREFS_KEY);
            if (!raw) {
                // Keep legacy columns visible by default; optional ones start hidden
                return [];
            }
            const parsed = JSON.parse(raw);
            if (!Array.isArray(parsed)) {
                return [];
            }
            return parsed.filter((key) => DEVICE_OPTIONAL_COLUMNS.includes(key));
        } catch (_) {
            return [];
        }
    }

    function saveOptionalColumnsPreference(selectedColumns) {
        try {
            localStorage.setItem(DEVICE_COLUMN_PREFS_KEY, JSON.stringify(selectedColumns));
        } catch (_) {
            // Ignore persistence errors (e.g., private browsing quota restrictions)
        }
    }

    function updateColumnSelectionLimits(selectedColumns) {
        if (!columnCheckboxes.length) {
            return;
        }

        const maxOptionalColumns = DEVICE_MAX_TOTAL_COLUMNS - DEVICE_MANDATORY_COLUMNS;
        const maxReached = selectedColumns.length >= maxOptionalColumns;

        columnCheckboxes.forEach((checkbox) => {
            if (!checkbox.checked) {
                checkbox.disabled = maxReached;
            }
        });

        if (columnsLimitMsg) {
            columnsLimitMsg.classList.toggle('hidden', !maxReached);
        }
    }

    function applyOptionalColumns(selectedColumns) {
        DEVICE_OPTIONAL_COLUMNS.forEach((columnKey) => {
            const shouldShow = selectedColumns.includes(columnKey);
            const nodes = document.querySelectorAll(`[data-optional-column="${columnKey}"]`);
            nodes.forEach((node) => node.classList.toggle('hidden', !shouldShow));
        });

        columnCheckboxes.forEach((checkbox) => {
            const columnKey = checkbox.getAttribute('data-column-checkbox');
            checkbox.checked = selectedColumns.includes(columnKey);
        });

        updateColumnSelectionLimits(selectedColumns);
    }

    // Use event delegation on document to avoid Firefox issues with hidden elements
    document.addEventListener('click', function(e) {
        const searchToggle = e.target.closest('#device-search-toggle');
        const columnsToggle = e.target.closest('#device-columns-toggle');

        if (searchToggle && searchContainer) {
            const wasOpen = searchContainer.classList.contains('max-w-xs');

            searchContainer.classList.toggle('max-w-xs');
            searchContainer.classList.toggle('opacity-100');

            if (!wasOpen && searchInput) {
                setTimeout(() => searchInput.focus(), 150);
            } else if (wasOpen) {
                if (searchInput) {
                    searchInput.value = '';
                }
                filterDevices('');
            }
        }

        if (columnsToggle && columnsPanel) {
            columnsPanel.classList.toggle('hidden');
        } else if (columnsPanel && columnsToggleButton && !columnsPanel.classList.contains('hidden')) {
            if (!columnsPanel.contains(e.target) && !columnsToggleButton.contains(e.target)) {
                columnsPanel.classList.add('hidden');
            }
        }
    });

    if (searchInput) {
        searchInput.addEventListener('input', (event) => {
            filterDevices(event.target.value);
        });
    }

    if (columnCheckboxes.length) {
        let selectedColumns = loadOptionalColumnsPreference();
        applyOptionalColumns(selectedColumns);

        columnCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', (event) => {
                const columnKey = event.target.getAttribute('data-column-checkbox');
                if (!columnKey) {
                    return;
                }

                if (event.target.checked) {
                    if (!selectedColumns.includes(columnKey)) {
                        selectedColumns = [...selectedColumns, columnKey];
                    }
                } else {
                    selectedColumns = selectedColumns.filter((key) => key !== columnKey);
                }

                applyOptionalColumns(selectedColumns);
                saveOptionalColumnsPreference(selectedColumns);
            });
        });
    }
});
