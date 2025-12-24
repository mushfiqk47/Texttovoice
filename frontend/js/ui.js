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
        console.log("UI: Binding events");
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
        this.dom.CLEAR_CACHE_BTN?.addEventListener('click', () => this.clearGpuCache());

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

    // Voice Library Methods
    async openVoiceLibrary() {
        console.log("UI: Opening Voice Library");
        if (!this.dom.VOICE_LIBRARY_MODAL) {
            console.error("UI: Modal element not found");
            return;
        }

        try {
            const data = await api.getVoices();
            console.log("Voices loaded:", data);
            this.renderVoiceList(data.voices);
            this.dom.VOICE_LIBRARY_MODAL.hidden = false;
        } catch (e) {
            console.error(e);
            this.showError('Failed to load voice library');
        }
    }

    renderVoiceList(voices) {
        const list = document.getElementById(DOM_IDS.VOICE_LIST);
        if (!list) return;

        if (voices.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <p>No saved voices yet</p>
                </div>`;
            return;
        }

        list.innerHTML = voices.map(voice => `
            <div class="voice-item">
                <div class="voice-info">
                    <span class="voice-name">${voice.name}</span>
                    <span class="voice-meta">${voice.size_kb} KB</span>
                </div>
                <div class="voice-actions">
                    <button class="icon-btn select-voice-btn" data-filename="${voice.filename}" title="Use Voice">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M5 13l4 4L19 7"/>
                        </svg>
                    </button>
                    <button class="icon-btn delete-voice-btn" data-name="${voice.name}" title="Delete" style="color: var(--danger);">
                         <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');

        // Bind events
        list.querySelectorAll('.select-voice-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.selectVoice(btn.dataset.filename);
                this.dom.VOICE_LIBRARY_MODAL.hidden = true;
            });
        });

        list.querySelectorAll('.delete-voice-btn').forEach(btn => {
            btn.addEventListener('click', () => this.handleVoiceDelete(btn.dataset.name));
        });
    }

    selectVoice(filename) {
        // Fetch the file and create a File object to simulate upload
        fetch(`/voices/${filename}`)
            .then(res => res.blob())
            .then(blob => {
                const file = new File([blob], filename, { type: blob.type });
                this.handleFileSelect({ target: { files: [file] } });
            })
            .catch(e => this.showError('Failed to load voice'));
    }

    async handleVoiceDelete(name) {
        if (!confirm(`Delete voice "${name}"?`)) return;

        try {
            await api.deleteVoice(name);
            // Reload list
            const data = await api.getVoices();
            this.renderVoiceList(data.voices);
        } catch (e) {
            this.showError(e.message);
        }
    }

    async saveVoice() {
        console.log("UI: Saving Voice");
        // Updated to use DOM_IDS.SAVE_VOICE_BTN if needed, but logic is called from event listener
        const file = store.get('referenceAudioFile');
        if (!file) {
            this.showError('No audio file to save');
            return;
        }

        const name = prompt("Enter a name for this voice preset:");
        if (!name) return;

        try {
            await api.saveVoice(name, file);
            alert('Voice saved to library!');
        } catch (e) {
            this.showError(e.message);
        }
    }

    async clearGpuCache() {
        const btn = this.dom.CLEAR_CACHE_BTN;
        const status = this.dom.CACHE_STATUS;
        if (!btn) return;

        try {
            btn.disabled = true;
            if (status) {
                status.hidden = false;
                status.textContent = "Clearing...";
                status.style.color = "var(--text-muted)";
            }

            const res = await api.clearGpuCache();

            if (status) {
                status.textContent = "Cache Cleared";
                status.style.color = "var(--success)";

                // Show memory usage if available
                if (res.memory_allocated_mb) {
                    setTimeout(() => {
                        status.textContent = `${res.memory_allocated_mb}MB / ${res.memory_reserved_mb}MB`;
                    }, 1500);
                }
            }
        } catch (e) {
            console.error(e);
            if (status) {
                status.textContent = "Failed";
                status.style.color = "var(--danger)";
            }
            this.showError('Failed to clear GPU cache');
        } finally {
            btn.disabled = false;
            // Hide status after delay
            setTimeout(() => {
                if (status) status.hidden = true;
            }, 5000);
        }
    }

    async handleBookFile(e) {
        const file = e.target.files[0];
        if (!file) return;

        store.set('bookFile', file);
        if (this.dom.BOOK_UPLOAD_AREA) this.dom.BOOK_UPLOAD_AREA.hidden = true;

        // Show loading state
        const textWrapper = document.getElementById(DOM_IDS.BOOK_TEXT_WRAPPER);
        const textInput = document.getElementById(DOM_IDS.BOOK_TEXT_INPUT);

        if (textWrapper) {
            textWrapper.hidden = false;
            if (textInput) textInput.value = "Reading file...";
        }

        try {
            const data = await api.parseBook(file);
            store.set('bookText', data.content);
            store.set('bookChapters', []); // Reset chapters until split

            // Update UI
            if (textInput) textInput.value = data.content;
            this.updateBookStats(data.content.length);

        } catch (e) {
            this.showError(e.message);
            if (this.dom.BOOK_UPLOAD_AREA) this.dom.BOOK_UPLOAD_AREA.hidden = false;
            if (textWrapper) textWrapper.hidden = true;
        }
    }

    updateBookStats(charCount = 0, wordCount = 0, chapterCount = 0) {
        const elChar = document.getElementById(DOM_IDS.BOOK_CHAR_COUNT);
        const elWord = document.getElementById(DOM_IDS.BOOK_WORD_COUNT);
        const elChap = document.getElementById(DOM_IDS.BOOK_CHAPTER_COUNT);

        if (elChar) elChar.textContent = `${charCount} characters`;
        // Estimate words if not provided
        if (wordCount === 0 && charCount > 0) wordCount = Math.round(charCount / 5);
        if (elWord) elWord.textContent = `${wordCount} words`;
        if (elChap) elChap.textContent = `${chapterCount} chapters`;
    }

    splitChapters() {
        const text = store.get('bookText');
        if (!text) {
            this.showError("No book content to split");
            return;
        }

        // Simple splitting logic (double double newlines)
        const possibleChapters = text.split(/\n\s*\n\s*\n/);

        // If that didn't work well (too few), try single double newline
        let pieces = possibleChapters;
        if (pieces.length < 2) {
            pieces = text.split(/\n\s*\n/);
        }

        const chapters = pieces
            .map((content, idx) => ({
                id: idx + 1,
                title: `Chapter ${idx + 1}`,
                content: content.trim()
            }))
            .filter(c => c.content.length > 50); // Filter tiny chunks

        store.set('bookChapters', chapters);
        this.renderChapters(chapters);
        this.updateBookStats(text.length, 0, chapters.length);

        if (this.dom.GENERATE_ALL_BTN) this.dom.GENERATE_ALL_BTN.disabled = false;
    }

    renderChapters(chapters) {
        const list = document.getElementById(DOM_IDS.CHAPTERS_LIST);
        if (!list) return;

        if (chapters.length === 0) {
            list.innerHTML = `<div class="empty-state"><p>No chapters found</p></div>`;
            return;
        }

        list.innerHTML = chapters.map(c => `
            <div class="chapter-item" style="padding: 10px; border-bottom: 1px solid var(--border);">
                <div class="chapter-info">
                    <span class="chapter-title" style="font-weight:bold;">${c.title}</span>
                    <span class="chapter-meta" style="font-size:0.8rem; color:var(--text-secondary); margin-left:10px;">${c.content.length} chars</span>
                </div>
            </div>
        `).join('');
    }

    async generateAllChapters() {
        const chapters = store.get('bookChapters');
        if (!chapters || chapters.length === 0) return;

        this.ui_setBookGenerating(true);
        const total = chapters.length;
        let completed = 0;

        // Settings
        const settings = store.get('settings');
        const refFile = store.get('referenceAudioFile');

        for (const chapter of chapters) {
            try {
                // Update progress
                this.updateBookProgress(completed, total, `Generating ${chapter.title}...`);

                // Scroll to make sure user sees progress
                const container = document.getElementById(DOM_IDS.BOOK_PROGRESS_CONTAINER);
                if (container) container.scrollIntoView({ behavior: 'smooth', block: 'center' });

                // Generate
                const res = await api.generateSpeech(
                    chapter.content,
                    settings.expressiveness,
                    settings.guidance,
                    refFile
                );

                // Handle result
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);

                // Get filename
                const cd = res.headers.get('Content-Disposition');
                const filename = cd ? cd.split('filename=')[1].replace(/"/g, '') : `chapter_${chapter.id}.wav`;

                // Add to audio controller queue (access via window.app)
                if (window.app && window.app.audio) {
                    window.app.audio.addToQueue({
                        name: `${chapter.title}`,
                        filename: filename,
                        url: url,
                        timestamp: Date.now()
                    });
                }

                completed++;
                this.updateBookProgress(completed, total);

            } catch (e) {
                console.error(`Failed chapter ${chapter.id}:`, e);
                this.updateBookProgress(completed, total, `Error on ${chapter.title}`);
                await new Promise(r => setTimeout(r, 2000)); // Pause on error
            }
        }

        this.updateBookProgress(total, total, "Done!");
        setTimeout(() => this.ui_setBookGenerating(false), 2000);
    }

    ui_setBookGenerating(isGenerating) {
        if (this.dom.GENERATE_ALL_BTN) {
            this.dom.GENERATE_ALL_BTN.disabled = isGenerating;
            this.dom.GENERATE_ALL_BTN.innerHTML = isGenerating ?
                `<div class="loading-spinner"></div><span>Generating...</span>` :
                `<span>Generate All</span>`;
        }
        const container = document.getElementById(DOM_IDS.BOOK_PROGRESS_CONTAINER);
        if (container) container.hidden = !isGenerating;
    }

    updateBookProgress(current, total, text) {
        const bar = document.getElementById(DOM_IDS.BOOK_PROGRESS_BAR);
        const txt = document.getElementById(DOM_IDS.BOOK_PROGRESS_TEXT);

        if (bar) bar.style.width = `${(current / total) * 100}%`;
        if (txt) txt.textContent = text || `${current}/${total} Chapters Generated`;
    }

    // Trigger callback
    onGenerateClick() {
        if (this.onGenerate) this.onGenerate();
    }
}
