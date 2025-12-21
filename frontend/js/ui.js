import { DOM_IDS, CONFIG } from './config.js';
import { store } from './state.js';
import { api } from './api.js';

export class UIController {
    constructor() {
        this.dom = this.cacheDOM();
        this.bindEvents();
        this.restoreState();
    }

    cacheDOM() {
        const dom = {};
        for (const [key, selector] of Object.entries(DOM_IDS)) {
            // Check if selector is a class or ID
            if (selector.startsWith('.')) {
                dom[key] = document.querySelectorAll(selector);
            } else {
                dom[key] = document.getElementById(selector);
            }
        }

        // Extra special elements
        dom.SIDEBAR_EL = document.querySelector(DOM_IDS.SIDEBAR);
        dom.OUTPUT_PANEL_EL = document.querySelector(DOM_IDS.OUTPUT_PANEL);

        return dom;
    }

    bindEvents() {
        // Navigation
        this.dom.NAV_ITEMS.forEach(item => {
            item.addEventListener('click', () => this.switchMode(item.dataset.mode));
        });

        // Toggle Sidebar/Queue
        this.dom.SIDEBAR_TOGGLE?.addEventListener('click', () => this.toggleSidebar());
        this.dom.QUEUE_TOGGLE?.addEventListener('click', () => this.toggleQueue());

        // Quick Inputs
        this.dom.TEXT_INPUT?.addEventListener('input', (e) => this.handleTextInput(e));
        this.dom.TAG_BUTTONS.forEach(btn => {
            btn.addEventListener('click', () => this.insertTag(btn.dataset.tag));
        });

        // Sliders
        this.dom.EXPRESSIVENESS_SLIDER?.addEventListener('input', (e) => {
            if (this.dom.EXPRESSIVENESS_VALUE)
                this.dom.EXPRESSIVENESS_VALUE.textContent = parseFloat(e.target.value).toFixed(2);
            store.set('settings', { ...store.get('settings'), expressiveness: e.target.value });
        });

        this.dom.GUIDANCE_SLIDER?.addEventListener('input', (e) => {
            if (this.dom.GUIDANCE_VALUE)
                this.dom.GUIDANCE_VALUE.textContent = parseFloat(e.target.value).toFixed(2);
            store.set('settings', { ...store.get('settings'), guidance: e.target.value });
        });

        // File Upload
        this.dom.UPLOAD_AREA?.addEventListener('click', () => this.dom.AUDIO_UPLOAD?.click());
        this.dom.AUDIO_UPLOAD?.addEventListener('change', (e) => this.handleFileSelect(e));
        this.dom.REMOVE_FILE_BTN?.addEventListener('click', () => this.removeFile());
        this.bindDragDrop(this.dom.UPLOAD_AREA, this.handleFileSelect.bind(this));

        // Actions
        this.dom.GENERATE_BTN?.addEventListener('click', () => this.onGenerateClick());
        this.dom.RESET_SETTINGS_BTN?.addEventListener('click', () => this.resetSettings());

        // Book Handling
        this.dom.BOOK_UPLOAD_AREA?.addEventListener('click', () => this.dom.BOOK_FILE_UPLOAD?.click());
        this.dom.BOOK_FILE_UPLOAD?.addEventListener('change', (e) => this.handleBookFile(e));
        this.dom.SPLIT_CHAPTERS_BTN?.addEventListener('click', () => this.splitChapters());
        this.dom.GENERATE_ALL_BTN?.addEventListener('click', () => this.generateAllChapters());

        // Voice Library
        this.dom.VOICE_LIBRARY_CARD?.addEventListener('click', () => this.openVoiceLibrary());
        this.dom.CLOSE_VOICE_LIBRARY_BTN?.addEventListener('click', () => {
            if (this.dom.VOICE_LIBRARY_MODAL) this.dom.VOICE_LIBRARY_MODAL.hidden = true;
        });
        this.dom.SAVE_VOICE_BTN?.addEventListener('click', () => this.saveVoice());
    }

    bindDragDrop(element, callback) {
        if (!element) return;
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            element.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            element.addEventListener(eventName, () => element.classList.add('drag-over'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            element.addEventListener(eventName, () => element.classList.remove('drag-over'), false);
        });

        element.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            callback({ target: { files: files } });
        }, false);
    }

    switchMode(mode) {
        store.set('currentMode', mode);

        // Update Nav
        this.dom.NAV_ITEMS.forEach(item => {
            item.classList.toggle('active', item.dataset.mode === mode);
        });

        // Update Panels
        // Hide all first
        [this.dom.QUICK_MODE, this.dom.BOOK_MODE, this.dom.SETTINGS_MODE].forEach(el => {
            if (el) el.classList.remove('active');
        });

        // Show active
        if (mode === 'quick' && this.dom.QUICK_MODE) this.dom.QUICK_MODE.classList.add('active');
        if (mode === 'book' && this.dom.BOOK_MODE) this.dom.BOOK_MODE.classList.add('active');
        if (mode === 'settings' && this.dom.SETTINGS_MODE) this.dom.SETTINGS_MODE.classList.add('active');

        // Update Title
        if (this.dom.PAGE_TITLE) {
            const titles = { quick: 'Quick TTS', book: 'Book Mode', settings: 'Settings' };
            this.dom.PAGE_TITLE.textContent = titles[mode] || 'Quick TTS';
        }
    }

    toggleSidebar() {
        if (this.dom.SIDEBAR_EL) {
            this.dom.SIDEBAR_EL.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', this.dom.SIDEBAR_EL.classList.contains('collapsed'));
        }
    }

    toggleQueue() {
        if (this.dom.OUTPUT_PANEL_EL) {
            const isHidden = this.dom.OUTPUT_PANEL_EL.classList.toggle('hidden');
            localStorage.setItem('queueHidden', isHidden);
            this.updateQueueToggleBtn(isHidden);
        }
    }

    updateQueueToggleBtn(isHidden) {
        if (!this.dom.QUEUE_TOGGLE) return;
        const span = this.dom.QUEUE_TOGGLE.querySelector('span');
        if (isHidden) {
            this.dom.QUEUE_TOGGLE.classList.add('dim');
            if (span) span.textContent = 'Show Queue';
        } else {
            this.dom.QUEUE_TOGGLE.classList.remove('dim');
            if (span) span.textContent = 'Queue';
        }
    }

    restoreState() {
        const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (collapsed && this.dom.SIDEBAR_EL) this.dom.SIDEBAR_EL.classList.add('collapsed');

        const queueHidden = localStorage.getItem('queueHidden') === 'true';
        if (queueHidden && this.dom.OUTPUT_PANEL_EL) this.dom.OUTPUT_PANEL_EL.classList.add('hidden');
        this.updateQueueToggleBtn(queueHidden);
    }

    // ... Input handling logic
    handleTextInput(e) {
        const len = e.target.value.length;
        if (this.dom.CHAR_COUNT) this.dom.CHAR_COUNT.textContent = len;
    }

    insertTag(tag) {
        const input = this.dom.TEXT_INPUT;
        if (!input) return;

        const start = input.selectionStart;
        const end = input.selectionEnd;
        const text = input.value;
        const before = text.substring(0, start);
        const after = text.substring(end);

        input.value = before + ' ' + tag + ' ' + after;
        input.focus();
        // Update char count
        this.handleTextInput({ target: input });
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('audio/')) {
            this.showError('Invalid file type');
            return;
        }

        store.set('referenceAudioFile', file);
        if (this.dom.UPLOAD_AREA) this.dom.UPLOAD_AREA.hidden = true;
        if (this.dom.UPLOADED_FILE) this.dom.UPLOADED_FILE.hidden = false;
        if (this.dom.FILE_NAME) this.dom.FILE_NAME.textContent = file.name;
    }

    removeFile() {
        store.set('referenceAudioFile', null);
        if (this.dom.UPLOAD_AREA) this.dom.UPLOAD_AREA.hidden = false;
        if (this.dom.UPLOADED_FILE) this.dom.UPLOADED_FILE.hidden = true;
        if (this.dom.AUDIO_UPLOAD) this.dom.AUDIO_UPLOAD.value = '';
    }

    resetSettings() {
        if (this.dom.EXPRESSIVENESS_SLIDER) {
            this.dom.EXPRESSIVENESS_SLIDER.value = 1.0;
            if (this.dom.EXPRESSIVENESS_VALUE) this.dom.EXPRESSIVENESS_VALUE.textContent = "1.00";
        }
        if (this.dom.GUIDANCE_SLIDER) {
            this.dom.GUIDANCE_SLIDER.value = 0.5;
            if (this.dom.GUIDANCE_VALUE) this.dom.GUIDANCE_VALUE.textContent = "0.50";
        }
        this.removeFile();
        store.set('settings', { expressiveness: 1.0, guidance: 0.5 });
    }

    showError(msg) {
        if (this.dom.ERROR_MESSAGE) this.dom.ERROR_MESSAGE.textContent = msg;
        if (this.dom.ERROR_STATE) this.dom.ERROR_STATE.hidden = false;
        setTimeout(() => {
            if (this.dom.ERROR_STATE) this.dom.ERROR_STATE.hidden = true;
        }, 5000);
    }

    setGenerating(isGenerating) {
        store.set('isGenerating', isGenerating);
        if (!this.dom.GENERATE_BTN) return;

        this.dom.GENERATE_BTN.disabled = isGenerating;
        if (isGenerating) {
            this.dom.GENERATE_BTN.innerHTML = `<div class="loading-spinner"></div><span>Generating...</span>`;
        } else {
            this.dom.GENERATE_BTN.innerHTML = `
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                <span>Generate Speech</span>`;
        }
    }

    // Trigger callback
    onGenerateClick() {
        if (this.onGenerate) this.onGenerate();
    }
}
