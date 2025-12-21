import { store } from './state.js';
import { api } from './api.js';
import { DOM_IDS } from './config.js';

export class AudioController {
    constructor(ui) {
        this.ui = ui;
        this.player = document.getElementById(DOM_IDS.AUDIO_PLAYER);
        this.queueContainer = document.getElementById(DOM_IDS.AUDIO_QUEUE);
        this.init();
    }

    init() {
        this.loadQueue();

        // Playback Events
        document.getElementById(DOM_IDS.SKIP_BACK_BTN)?.addEventListener('click', () => this.skip(-15));
        document.getElementById(DOM_IDS.SKIP_FORWARD_BTN)?.addEventListener('click', () => this.skip(15));
        document.getElementById(DOM_IDS.PLAYBACK_SPEED)?.addEventListener('change', (e) => {
            if (this.player) this.player.playbackRate = parseFloat(e.target.value);
        });

        document.getElementById(DOM_IDS.DOWNLOAD_CURRENT_BTN)?.addEventListener('click', () => this.downloadCurrent());
        document.getElementById(DOM_IDS.DOWNLOAD_ALL_BTN)?.addEventListener('click', () => this.downloadAll());
        document.getElementById(DOM_IDS.CLEAR_QUEUE_BTN)?.addEventListener('click', () => this.clearQueue());
    }

    addToQueue(item) {
        const queue = store.get('audioQueue');
        queue.push(item);
        store.set('audioQueue', queue);
        this.saveQueue();
        this.renderQueue();
        this.play(queue.length - 1);
    }

    renderQueue() {
        const queue = store.get('audioQueue');
        const currentIndex = store.get('currentAudioIndex');

        if (queue.length === 0) {
            this.queueContainer.innerHTML = `
                <div class="empty-queue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/>
                    </svg>
                    <p>Generated audio will appear here</p>
                </div>`;
            return;
        }

        this.queueContainer.innerHTML = queue.map((item, index) => `
            <div class="audio-item ${index === currentIndex ? 'active' : ''}" data-index="${index}">
                <div class="audio-item-header">
                    <span class="audio-item-name">${item.name}</span>
                    <button class="delete-item-btn" data-index="${index}" title="Delete">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');

        // Re-bind click events
        this.queueContainer.querySelectorAll('.audio-item').forEach(el => {
            el.addEventListener('click', (e) => {
                if (e.target.closest('.delete-item-btn')) return;
                this.play(parseInt(el.dataset.index));
            });
        });

        this.queueContainer.querySelectorAll('.delete-item-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteItem(parseInt(btn.dataset.index));
            });
        });
    }

    play(index) {
        const queue = store.get('audioQueue');
        if (index < 0 || index >= queue.length) return;

        store.set('currentAudioIndex', index);
        const item = queue[index];

        if (this.player) {
            this.player.src = item.url;
            this.player.play();

            const trackName = document.getElementById(DOM_IDS.CURRENT_TRACK_NAME);
            const playerPanel = document.getElementById(DOM_IDS.CURRENT_PLAYER);

            if (trackName) trackName.textContent = item.name;
            if (playerPanel) playerPanel.hidden = false;
        }

        this.renderQueue(); // Re-render to update 'active' class
    }

    skip(seconds) {
        if (this.player) this.player.currentTime += seconds;
    }

    async deleteItem(index) {
        const queue = store.get('audioQueue');
        const item = queue[index];

        if (!confirm(`Delete "${item.name}"?`)) return;

        try {
            await api.deleteAudio(item.filename);
            queue.splice(index, 1);
            store.set('audioQueue', queue);
            this.saveQueue();

            if (store.get('currentAudioIndex') === index) {
                if (this.player) {
                    this.player.pause();
                    this.player.src = '';
                }
                store.set('currentAudioIndex', -1);
                const playerPanel = document.getElementById(DOM_IDS.CURRENT_PLAYER);
                if (playerPanel) playerPanel.hidden = true;
            }
            this.renderQueue();
        } catch (e) {
            console.error(e);
            alert('Failed to delete: ' + e.message);
        }
    }

    async clearQueue() {
        const queue = store.get('audioQueue');
        if (queue.length === 0) return;
        if (!confirm("Clear all items?")) return;

        for (const item of [...queue]) {
            try { await api.deleteAudio(item.filename); } catch (e) { }
        }

        store.set('audioQueue', []);
        store.set('currentAudioIndex', -1);
        this.saveQueue();
        this.renderQueue();
        if (this.player) this.player.src = '';
        document.getElementById(DOM_IDS.CURRENT_PLAYER).hidden = true;
    }

    downloadCurrent() {
        const idx = store.get('currentAudioIndex');
        if (idx === -1) return;
        this.downloadItem(store.get('audioQueue')[idx]);
    }

    downloadAll() {
        store.get('audioQueue').forEach(item => this.downloadItem(item));
    }

    downloadItem(item) {
        const a = document.createElement('a');
        a.href = item.url;
        a.download = item.filename;
        a.click();
    }

    saveQueue() {
        const queue = store.get('audioQueue');
        const simpleQueue = queue.map(i => ({ name: i.name, filename: i.filename, timestamp: i.timestamp }));
        localStorage.setItem('audio_queue', JSON.stringify(simpleQueue));
    }

    loadQueue() {
        const saved = localStorage.getItem('audio_queue');
        if (saved) {
            try {
                const simple = JSON.parse(saved);
                const full = simple.map(i => ({ ...i, url: `/audio/${i.filename}` }));
                store.set('audioQueue', full);
                this.renderQueue();
            } catch (e) { console.error(e); }
        }
    }
}
