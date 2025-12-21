import { CONFIG } from './config.js';

class ApiClient {
    async getHealth() {
        const res = await fetch(`${CONFIG.API_BASE_URL}/health`);
        return await res.json();
    }

    async generateSpeech(text, exaggeration, cfgWeight, referenceAudio) {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('exaggeration', exaggeration);
        formData.append('cfg_weight', cfgWeight);
        if (referenceAudio) {
            formData.append('reference_audio', referenceAudio);
        }

        const res = await fetch(`${CONFIG.API_BASE_URL}/generate`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Generation failed' }));
            throw new Error(err.detail);
        }

        return res;
    }

    async parseBook(file) {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch(`${CONFIG.API_BASE_URL}/parse-book`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to parse book');
        }
        return await res.json();
    }

    async getVoices() {
        const res = await fetch(`${CONFIG.API_BASE_URL}/voices`);
        return await res.json();
    }

    async saveVoice(name, file) {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('audio', file);

        const res = await fetch(`${CONFIG.API_BASE_URL}/voices`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail);
        }
        return await res.json();
    }

    async deleteVoice(name) {
        const res = await fetch(`${CONFIG.API_BASE_URL}/voices/${name}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete voice');
        return await res.json();
    }

    async deleteAudio(filename) {
        const res = await fetch(`${CONFIG.API_BASE_URL}/audio/${filename}`, {
            method: 'DELETE'
        });
        if (!res.ok && res.status !== 404) {
            throw new Error('Failed to delete audio');
        }
    }

    async clearGpuCache() {
        const res = await fetch(`${CONFIG.API_BASE_URL}/gpu-cleanup`, { method: 'POST' });
        if (!res.ok) throw new Error('Cleanup failed');
        return await res.json();
    }
}

export const api = new ApiClient();
