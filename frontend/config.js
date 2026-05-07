// Set to your Cloud Run URL for production, keep localhost for local dev.
export const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://contract-analyzer-twcbgtbasa-ew.a.run.app';
