// labels.js — Label selection & edit sidepanel for device detail

// ─── Panel helpers ────────────────────────────────────────────────────────────

function toggleLabelSelectionPanel() {
    const panel = document.getElementById('label-selection-panel');
    if (!panel) return;
    // Close actions dropdown if open
    document.getElementById('device-actions-menu')?.classList.add('hidden');
    panel.classList.toggle('hidden');
}

function closeLabelSelectionPanel() {
    const panel = document.getElementById('label-selection-panel');
    if (panel) panel.classList.add('hidden');
}

function openLabelEditPanel(labelId) {
    const panel = document.getElementById('label-edit-panel');
    if (!panel) return;
    panel.classList.remove('hidden');

    const title = document.getElementById('label-edit-title');
    const form  = document.getElementById('label-edit-form');

    if (labelId) {
        title.textContent = 'Edit Label';
        form.action = `/labels/${labelId}/edit/`;
        loadLabelDetails(labelId);
    } else {
        title.textContent = 'New Label';
        form.action = labelCreateUrl;
        clearLabelEditForm();
    }
}

function closeLabelEditPanel() {
    const panel = document.getElementById('label-edit-panel');
    if (!panel) return;
    panel.classList.add('hidden');
    hideLabelEditErrors();

    // Return to selection panel if it was open before
    const selPanel = document.getElementById('label-selection-panel');
    if (selPanel && selPanel.dataset.wasOpen === 'true') {
        selPanel.dataset.wasOpen = 'false';
        selPanel.classList.remove('hidden');
    }
}

// Open label edit from inside the selection panel (hides selection panel first)
function openLabelEditFromSelection(labelId) {
    const selPanel = document.getElementById('label-selection-panel');
    if (selPanel && !selPanel.classList.contains('hidden')) {
        selPanel.dataset.wasOpen = 'true';
        selPanel.classList.add('hidden');
    }
    openLabelEditPanel(labelId);
}

// ─── Form helpers ─────────────────────────────────────────────────────────────

function loadLabelDetails(labelId) {
    labelId = Number(labelId);
    const label = (typeof allLabels !== 'undefined' ? allLabels : []).find(l => l.id === labelId);
    if (!label) { console.error('Label not found:', labelId); return; }

    document.getElementById('label_edit_id').value          = label.id;
    document.getElementById('label_edit_name').value        = label.name;
    document.getElementById('label_edit_color').value       = label.color;
    document.getElementById('label-edit-color-hex').textContent = label.color;
    document.getElementById('label_edit_description').value = label.description || '';
    hideLabelEditErrors();
}

function clearLabelEditForm() {
    document.getElementById('label_edit_id').value          = '';
    document.getElementById('label_edit_name').value        = '';
    document.getElementById('label_edit_color').value       = '#3B82F6';
    document.getElementById('label-edit-color-hex').textContent = '#3B82F6';
    document.getElementById('label_edit_description').value = '';
    hideLabelEditErrors();
}

function showLabelEditErrors(errors) {
    const container = document.getElementById('label-edit-errors');
    const list      = document.getElementById('label-edit-error-list');
    list.innerHTML  = '';

    if (typeof errors === 'object' && !Array.isArray(errors)) {
        for (const [field, messages] of Object.entries(errors)) {
            messages.forEach(msg => {
                const li = document.createElement('li');
                li.textContent = field === '__all__' ? msg : `${field}: ${msg}`;
                list.appendChild(li);
            });
        }
    } else if (Array.isArray(errors)) {
        errors.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = msg;
            list.appendChild(li);
        });
    }
    container.classList.remove('hidden');
}

function hideLabelEditErrors() {
    const container = document.getElementById('label-edit-errors');
    if (container) container.classList.add('hidden');
}

// ─── Submit label form via AJAX ───────────────────────────────────────────────

function submitLabelEditForm() {
    const form = document.getElementById('label-edit-form');
    const saveBtn = document.querySelector('#label-edit-panel button[onclick="submitLabelEditForm()"]');
    const originalText = saveBtn ? saveBtn.textContent : 'Save';
    if (saveBtn) { saveBtn.textContent = 'Saving…'; saveBtn.disabled = true; }

    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const label = data.label;
            const msg = document.getElementById('label_edit_id').value
                ? `Label "${label.name}" updated successfully.`
                : `Label "${label.name}" created successfully.`;
            sessionStorage.setItem('pending_toast_message', msg);
            sessionStorage.setItem('pending_toast_type', 'success');
            location.reload();
        } else {
            showLabelEditErrors(data.errors || ['Unknown error.']);
        }
    })
    .catch(() => showLabelEditErrors(['Network error. Please try again.']))
    .finally(() => {
        if (saveBtn) { saveBtn.textContent = originalText; saveBtn.disabled = false; }
    });
}

// ─── Selection panel helpers ──────────────────────────────────────────────────

function searchLabelByName(query) {
    document.querySelectorAll('#label-selection-list .label-item').forEach(item => {
        const name = item.dataset.labelName || '';
        item.classList.toggle('hidden', query && !name.includes(query.toLowerCase()));
    });
}

function applyLabelSelection() {
    const checked = [...document.querySelectorAll('.label-checkbox:checked')].map(cb => cb.value);

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                      document.cookie.match(/csrftoken=([^;]+)/)?.[1];

    const formData = new FormData();
    checked.forEach(id => formData.append('labels', id));
    if (csrftoken) formData.append('csrfmiddlewaretoken', csrftoken);

    fetch(deviceUpdateLabelsUrl, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            refreshLabelsBar(data.labels);
            closeLabelSelectionPanel();
        } else {
            console.error('Failed to update labels', data);
        }
    })
    .catch(err => console.error('Label update error:', err));
}

// Re-render the labels bar above Overview
function refreshLabelsBar(labels) {
    const bar = document.getElementById('device-labels-bar');
    if (!bar) return;
    bar.innerHTML = '';

    if (labels.length === 0) {
        bar.innerHTML = '<span class="text-gray-400 text-xs italic" id="device-labels-empty">No labels</span>';
        return;
    }

    labels.forEach(label => {
        const a = document.createElement('a');
        a.href  = `/?label=${label.id}`;
        a.className = 'inline-flex items-center px-3 py-1 rounded-full text-white text-xs font-semibold hover:opacity-80 transition-opacity';
        a.style.backgroundColor = label.color;
        a.title = label.description || '';
        a.textContent = label.name;
        bar.appendChild(a);
    });
}

// After creating a new label: add a row to the selection list panel
function addLabelToSelectionPanel(label) {
    const list = document.getElementById('label-selection-list');
    if (!list) return;

    // Remove "no labels" placeholder if present
    const empty = list.querySelector('p.text-gray-500');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = 'flex items-center group/rule label-item';
    div.dataset.labelName = label.name.toLowerCase();
    div.innerHTML = `
        <input type="checkbox" id="label-sel-${label.id}" value="${label.id}" class="hidden peer label-checkbox" checked>
        <label for="label-sel-${label.id}" class="flex-1 flex justify-between items-center py-1 px-4 bg-white rounded cursor-pointer hover:bg-gray-200 peer-checked:bg-amber-100 peer-checked:hover:bg-yellow-600/50 font-light">
            <span class="flex items-center gap-2">
                <span class="inline-block w-3 h-3 rounded-full flex-shrink-0" style="background-color: ${label.color};"></span>
                ${escapeHtml(label.name)}
            </span>
            <button type="button" onclick="openLabelEditFromSelection(${label.id})" class="group relative rounded-full p-1 bg-transparent" title="Edit label">
                <div class="opacity-0 group-hover:opacity-100 absolute inset-0 bg-black/10 rounded-full"></div>
                <svg class="size-4 align-middle invisible group-hover/label:visible relative z-10" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
                </svg>
            </button>
        </label>`;
    list.appendChild(div);
}

// After editing a label: update its name/color chip in the selection panel
function updateLabelChipInPanel(label) {
    const item = document.querySelector(`.label-item[data-label-name]`);
    // Find by checkbox value since name may have changed
    const checkbox = document.getElementById(`label-sel-${label.id}`);
    if (!checkbox) return;

    const row = checkbox.closest('.label-item');
    if (!row) return;
    row.dataset.labelName = label.name.toLowerCase();

    const dot = row.querySelector('span.rounded-full.flex-shrink-0');
    if (dot) dot.style.backgroundColor = label.color;

    const nameSpan = dot ? dot.parentElement : null;
    if (nameSpan) {
        // Replace text node (last child after the dot span)
        [...nameSpan.childNodes].forEach(n => { if (n.nodeType === Node.TEXT_NODE) n.remove(); });
        nameSpan.appendChild(document.createTextNode(label.name));
    }
}

function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ─── Event listeners ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    // Close buttons on selection panel
    document.querySelectorAll('.button-label-selection-panel').forEach(btn => {
        btn.addEventListener('click', () => closeLabelSelectionPanel());
    });

    // Close buttons on edit panel
    document.querySelectorAll('.button-label-edit-panel').forEach(btn => {
        btn.addEventListener('click', () => closeLabelEditPanel());
    });

    // Live hex preview in the color picker
    const colorInput = document.getElementById('label_edit_color');
    const hexDisplay = document.getElementById('label-edit-color-hex');
    if (colorInput && hexDisplay) {
        colorInput.addEventListener('input', () => { hexDisplay.textContent = colorInput.value; });
    }
});
