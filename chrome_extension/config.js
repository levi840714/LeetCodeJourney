// Configuration management for LeetCode Journey Chrome Extension

const CONFIG = {
    // Default API endpoints
    LOCAL_API: 'http://127.0.0.1:5000',
    CLOUD_FUNCTIONS_API: '', // Will be set dynamically
    
    // Storage keys
    STORAGE_KEYS: {
        API_URL: 'leetcode_journey_api_url',
        USE_CLOUD: 'leetcode_journey_use_cloud'
    },
    
    // Default configuration
    DEFAULT_CONFIG: {
        apiUrl: 'http://127.0.0.1:5000',
        useCloud: false
    }
};

/**
 * Configuration manager class
 */
class ConfigManager {
    constructor() {
        this.config = { ...CONFIG.DEFAULT_CONFIG };
        this.initialized = false;
    }
    
    /**
     * Initialize configuration by loading from storage
     */
    async init() {
        try {
            // Check if chrome.storage is available
            if (!chrome || !chrome.storage || !chrome.storage.local) {
                console.warn('Chrome storage API not available, using default config');
                this.config = { ...CONFIG.DEFAULT_CONFIG };
                this.initialized = true;
                return;
            }

            // Use Promise wrapper for older Chrome versions
            const result = await new Promise((resolve, reject) => {
                chrome.storage.local.get([
                    CONFIG.STORAGE_KEYS.API_URL,
                    CONFIG.STORAGE_KEYS.USE_CLOUD
                ], (result) => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError);
                    } else {
                        resolve(result);
                    }
                });
            });
            
            this.config.apiUrl = result[CONFIG.STORAGE_KEYS.API_URL] || CONFIG.DEFAULT_CONFIG.apiUrl;
            this.config.useCloud = result[CONFIG.STORAGE_KEYS.USE_CLOUD] || CONFIG.DEFAULT_CONFIG.useCloud;
            
            this.initialized = true;
        } catch (error) {
            console.error('Failed to load configuration:', error);
            // Use default config if storage fails
            this.config = { ...CONFIG.DEFAULT_CONFIG };
            this.initialized = true;
        }
    }
    
    /**
     * Get current API endpoint URL
     */
    getApiUrl() {
        if (!this.initialized) {
            console.warn('ConfigManager not initialized, using default config');
            return CONFIG.DEFAULT_CONFIG.apiUrl;
        }
        return this.config.apiUrl;
    }
    
    /**
     * Get full API endpoint with /log path
     */
    getApiEndpoint() {
        const baseUrl = this.getApiUrl();
        return baseUrl.endsWith('/') ? `${baseUrl}log` : `${baseUrl}/log`;
    }
    
    /**
     * Check if using cloud functions
     */
    isUsingCloud() {
        return this.config.useCloud;
    }
    
    /**
     * Update API URL
     */
    async setApiUrl(url, useCloud = false) {
        // Validate URL format
        if (!this.isValidUrl(url)) {
            throw new Error('Invalid URL format');
        }
        
        this.config.apiUrl = url.endsWith('/') ? url.slice(0, -1) : url;
        this.config.useCloud = useCloud;
        
        // Save to storage if available
        if (chrome && chrome.storage && chrome.storage.local) {
            try {
                await new Promise((resolve, reject) => {
                    chrome.storage.local.set({
                        [CONFIG.STORAGE_KEYS.API_URL]: this.config.apiUrl,
                        [CONFIG.STORAGE_KEYS.USE_CLOUD]: this.config.useCloud
                    }, () => {
                        if (chrome.runtime.lastError) {
                            reject(chrome.runtime.lastError);
                        } else {
                            resolve();
                        }
                    });
                });
            } catch (error) {
                console.warn('Failed to save configuration to storage:', error);
            }
        }
    }
    
    /**
     * Switch to local development mode
     */
    async useLocalDevelopment() {
        await this.setApiUrl(CONFIG.LOCAL_API, false);
    }
    
    /**
     * Switch to cloud functions mode
     */
    async useCloudFunctions(cloudUrl) {
        if (!cloudUrl) {
            throw new Error('Cloud Functions URL is required');
        }
        await this.setApiUrl(cloudUrl, true);
    }
    
    /**
     * Reset to default configuration
     */
    async reset() {
        this.config = { ...CONFIG.DEFAULT_CONFIG };
        if (chrome && chrome.storage && chrome.storage.local) {
            try {
                await new Promise((resolve, reject) => {
                    chrome.storage.local.clear(() => {
                        if (chrome.runtime.lastError) {
                            reject(chrome.runtime.lastError);
                        } else {
                            resolve();
                        }
                    });
                });
            } catch (error) {
                console.warn('Failed to clear storage:', error);
            }
        }
    }
    
    /**
     * Get current configuration
     */
    getConfig() {
        return { ...this.config };
    }
    
    /**
     * Validate URL format
     */
    isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }
    
    /**
     * Auto-detect configuration based on connectivity
     */
    async autoDetectBestEndpoint() {
        // Try local development first
        if (await this.testEndpoint(CONFIG.LOCAL_API)) {
            await this.useLocalDevelopment();
            return 'local';
        }
        
        // If cloud URL is configured, try it
        if (this.config.useCloud && this.config.apiUrl !== CONFIG.LOCAL_API) {
            if (await this.testEndpoint(this.config.apiUrl)) {
                return 'cloud';
            }
        }
        
        return 'none';
    }
    
    /**
     * Test if an endpoint is available
     */
    async testEndpoint(baseUrl, timeout = 3000) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            
            // Test with a simple GET request to the base URL first
            let testUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
            
            const response = await fetch(testUrl, {
                method: 'GET',
                signal: controller.signal,
                mode: 'cors' // Explicitly set CORS mode
            });
            
            clearTimeout(timeoutId);
            
            // Accept any status that's not a server error or network error
            // For Cloud Functions, we might get 404 for the root, but that's still a valid response
            return response.status < 500;
        } catch (error) {
            // Try alternative test with /log endpoint if base URL fails
            try {
                const controller2 = new AbortController();
                const timeoutId2 = setTimeout(() => controller2.abort(), 1000);
                
                const testUrl2 = baseUrl.endsWith('/') ? `${baseUrl}log` : `${baseUrl}/log`;
                const response2 = await fetch(testUrl2, {
                    method: 'OPTIONS', // Try OPTIONS for CORS preflight
                    signal: controller2.signal,
                    mode: 'cors'
                });
                
                clearTimeout(timeoutId2);
                return response2.status < 500;
            } catch (error2) {
                console.debug(`Endpoint test failed for ${baseUrl}:`, error.message);
                return false;
            }
        }
    }
}

// Create global instance
const configManager = new ConfigManager();

// Export for use in other scripts
window.CONFIG_MANAGER = configManager;