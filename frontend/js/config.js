export const CONFIG = {
    API_BASE_URL: '/api',
    MAX_TEXT_LENGTH: 5000,
    CHUNK_SIZE: 4000,
    ANIMATION: {
        DURATION_FAST: 200,
        DURATION_NORMAL: 300,
        EASE: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
    }
};

export const DOM_IDS = {
    NAV_ITEMS: '.nav-item',
    STATUS_DOT: 'status-dot',
    STATUS_TEXT: 'status-text',
    PAGE_TITLE: 'page-title',
    DETECTED_LANG: 'detected-lang',

    // Panels
    QUICK_MODE: 'quick-mode',
    BOOK_MODE: 'book-mode',
    SETTINGS_MODE: 'settings-mode',

    // Quick TTS
    TEXT_INPUT: 'text-input',
    CHAR_COUNT: 'char-count',
    TAG_BUTTONS: '.tag-btn',
    UPLOAD_AREA: 'upload-area',
    AUDIO_UPLOAD: 'audio-upload',
    UPLOADED_FILE: 'uploaded-file',
    FILE_NAME: 'file-name',
    REMOVE_FILE_BTN: 'remove-file',
    EXPRESSIVENESS_SLIDER: 'expressiveness',
    EXPRESSIVENESS_VALUE: 'expressiveness-value',
    GUIDANCE_SLIDER: 'guidance',
    GUIDANCE_VALUE: 'guidance-value',
    GENERATE_BTN: 'generate-btn',
    ERROR_STATE: 'error-state',
    ERROR_MESSAGE: 'error-message',

    // Book Mode
    BOOK_UPLOAD_AREA: 'book-upload-area',
    BOOK_FILE_UPLOAD: 'book-file-upload',
    BOOK_TEXT_WRAPPER: 'book-text-wrapper',
    BOOK_TEXT_INPUT: 'book-text-input',
    BOOK_STATS: '.book-stats',
    BOOK_CHAR_COUNT: 'book-char-count',
    BOOK_WORD_COUNT: 'book-word-count',
    BOOK_CHAPTER_COUNT: 'book-chapter-count',
    SPLIT_CHAPTERS_BTN: 'split-chapters-btn',
    CHAPTERS_LIST: 'chapters-list',
    GENERATE_ALL_BTN: 'generate-all-btn',
    BOOK_PROGRESS_CONTAINER: 'book-progress-container',
    BOOK_PROGRESS_BAR: 'book-progress-bar',
    BOOK_PROGRESS_TEXT: 'book-progress-text',

    // Outputs
    AUDIO_QUEUE: 'audio-queue',
    CURRENT_PLAYER: 'current-player',
    CURRENT_TRACK_NAME: 'current-track-name',
    AUDIO_PLAYER: 'audio-player',
    DOWNLOAD_CURRENT_BTN: 'download-current-btn',
    DOWNLOAD_ALL_BTN: 'download-all-btn',
    DOWNLOAD_MP3_BTN: 'download-mp3-btn',
    CLEAR_QUEUE_BTN: 'clear-queue-btn',

    // Controls
    SKIP_BACK_BTN: 'skip-back-btn',
    SKIP_FORWARD_BTN: 'skip-forward-btn',
    PLAYBACK_SPEED: 'playback-speed',

    // Settings
    CLEAR_CACHE_BTN: 'clear-cache-btn',
    CACHE_STATUS: 'cache-status',
    RESET_SETTINGS_BTN: 'reset-settings-btn',

    // Layout
    SIDEBAR: '.sidebar',
    OUTPUT_PANEL: '.output-panel',
    SIDEBAR_TOGGLE: 'sidebar-toggle',
    QUEUE_TOGGLE: 'queue-toggle',

    // Library
    VOICE_LIBRARY_CARD: 'voice-library-card',
    VOICE_LIBRARY_MODAL: 'voice-library-modal',
    CLOSE_VOICE_LIBRARY_BTN: 'close-voice-library',
    VOICE_LIST: 'voice-list',
    SAVE_VOICE_BTN: 'save-voice-btn'
};
