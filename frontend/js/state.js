/**
 * Simple State Management with Listeners
 */
class StateManager {
    constructor() {
        this.state = {
            currentMode: 'quick',
            isGenerating: false,
            referenceAudioFile: null,
            audioQueue: [],
            currentAudioIndex: -1,
            bookChapters: [],
            bookText: '',
            detectedLang: null,
            settings: {
                expressiveness: 1.0,
                guidance: 0.5
            }
        };
        this.listeners = new Map();
    }

    get(key) {
        return this.state[key];
    }

    set(key, value) {
        if (this.state[key] !== value) {
            this.state[key] = value;
            this.notify(key, value);
        }
    }

    update(key, fn) {
        const newValue = fn(this.state[key]);
        this.set(key, newValue);
    }

    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);
    }

    notify(key, value) {
        if (this.listeners.has(key)) {
            this.listeners.get(key).forEach(cb => cb(value));
        }
    }
}

export const store = new StateManager();
