import { UIController } from './ui.js';
import { AudioController } from './audio.js';
import { api } from './api.js';
import { store } from './state.js';
import { DOM_IDS } from './config.js';

class App {
    constructor() {
        this.ui = new UIController();
        this.audio = new AudioController(this.ui);
        this.init();
    }

    async init() {
        this.createParticles();
        await this.checkHealth();

        // Hook up generation
        this.ui.onGenerate = () => this.handleGenerate();
    }

    async checkHealth() {
        try {
            const health = await api.getHealth();
            if (health.status === 'healthy') {
                const dot = document.getElementById(DOM_IDS.STATUS_DOT);
                const text = document.getElementById(DOM_IDS.STATUS_TEXT);
                if (dot) dot.classList.add('online');
                if (text) text.textContent = 'System Ready';

                // Show GPU info
                if (health.gpu_name) {
                    const langBadge = document.getElementById(DOM_IDS.DETECTED_LANG);
                    if (langBadge) {
                        langBadge.textContent = health.gpu_name.split(' ')[0];
                        langBadge.hidden = false;
                    }
                }
            }
        } catch (e) {
            console.error("Backend offline");
        }
    }

    async handleGenerate() {
        const textInput = document.getElementById(DOM_IDS.TEXT_INPUT);
        const text = textInput ? textInput.value.trim() : '';

        if (!text) {
            this.ui.showError("Please enter text");
            return;
        }

        this.ui.setGenerating(true);
        try {
            const settings = store.get('settings');
            const refFile = store.get('referenceAudioFile');

            const res = await api.generateSpeech(
                text,
                settings.expressiveness,
                settings.guidance,
                refFile
            );

            // Handle response
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);

            // Get filename
            const cd = res.headers.get('Content-Disposition');
            const filename = cd ? cd.split('filename=')[1].replace(/"/g, '') : `gen_${Date.now()}.wav`;

            // Add to audio controller
            this.audio.addToQueue({
                name: `Speech ${store.get('audioQueue').length + 1}`,
                filename: filename,
                url: url,
                timestamp: Date.now()
            });

        } catch (e) {
            this.ui.showError(e.message);
        } finally {
            this.ui.setGenerating(false);
        }
    }

    createParticles() {
        const container = document.getElementById('particles');
        if (!container) return;
        for (let i = 0; i < 15; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            p.style.left = Math.random() * 100 + '%';
            p.style.top = Math.random() * 100 + '%';
            p.style.animationDelay = Math.random() * 5 + 's';
            container.appendChild(p);
        }
    }
}

// Start App
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
