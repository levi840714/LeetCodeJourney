// Simple configuration for LeetCode Journey Chrome Extension

// Configuration constants
const CONFIG = {
    LOCAL_API: 'http://127.0.0.1:5000',
    STORAGE_KEYS: {
        API_URL: 'leetcode_journey_api_url',
        USE_CLOUD: 'leetcode_journey_use_cloud'
    }
};

/**
 * Simple configuration manager
 */
class SimpleConfigManager {
    constructor() {
        this.apiUrl = CONFIG.LOCAL_API;
        this.useCloud = false;
        this.initialized = false;
    }
    
    /**
     * Initialize with error handling
     */
    async init() {
        try {
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                const result = await this.getFromStorage();
                this.apiUrl = result[CONFIG.STORAGE_KEYS.API_URL] || CONFIG.LOCAL_API;
                this.useCloud = result[CONFIG.STORAGE_KEYS.USE_CLOUD] || false;
            }
        } catch (error) {
            console.warn('Storage not available, using defaults:', error);
        }
        this.initialized = true;
    }
    
    /**
     * Get data from storage with Promise wrapper
     */
    getFromStorage() {
        return new Promise((resolve) => {
            try {
                chrome.storage.local.get([
                    CONFIG.STORAGE_KEYS.API_URL,
                    CONFIG.STORAGE_KEYS.USE_CLOUD
                ], (result) => {
                    if (chrome.runtime.lastError) {
                        console.warn('Storage error:', chrome.runtime.lastError);
                        resolve({});
                    } else {
                        resolve(result);
                    }
                });
            } catch (error) {
                console.warn('Storage access failed:', error);
                resolve({});
            }
        });
    }
    
    /**
     * Get API endpoint with /log path
     */
    getApiEndpoint() {
        const baseUrl = this.apiUrl.endsWith('/') ? this.apiUrl.slice(0, -1) : this.apiUrl;
        return `${baseUrl}/log`;
    }
    
    /**
     * Save configuration
     */
    async saveConfig(url, useCloud = false) {
        this.apiUrl = url.endsWith('/') ? url.slice(0, -1) : url;
        this.useCloud = useCloud;
        
        try {
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                await this.saveToStorage();
                // Notify other parts of the extension about config change
                this.notifyConfigChange();
                console.log('Config saved successfully:', { apiUrl: this.apiUrl, useCloud: this.useCloud });
            } else {
                throw new Error('Chrome storage not available');
            }
        } catch (error) {
            console.error('Failed to save config:', error);
            throw error; // Re-throw to let caller handle
        }
    }
    
    /**
     * Notify about config changes
     */
    notifyConfigChange() {
        // Send message to content script and popup
        if (typeof chrome !== 'undefined' && chrome.runtime) {
            chrome.runtime.sendMessage({
                type: 'CONFIG_UPDATED',
                config: this.getConfig()
            }).catch(() => {
                // Ignore errors if no listeners
            });
        }
    }
    
    /**
     * Save to storage with Promise wrapper
     */
    saveToStorage() {
        return new Promise((resolve, reject) => {
            try {
                const dataToSave = {
                    [CONFIG.STORAGE_KEYS.API_URL]: this.apiUrl,
                    [CONFIG.STORAGE_KEYS.USE_CLOUD]: this.useCloud
                };
                
                console.log('Attempting to save to storage:', dataToSave);
                
                chrome.storage.local.set(dataToSave, () => {
                    if (chrome.runtime.lastError) {
                        console.error('Storage save error:', chrome.runtime.lastError);
                        reject(new Error(chrome.runtime.lastError.message));
                    } else {
                        console.log('Successfully saved to storage');
                        resolve();
                    }
                });
            } catch (error) {
                console.error('Storage save failed:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Test endpoint connectivity
     */
    async testEndpoint(baseUrl, timeout = 2000) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            
            const testUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
            const response = await fetch(testUrl, {
                method: 'GET',
                signal: controller.signal,
                mode: 'cors'
            });
            
            clearTimeout(timeoutId);
            return response.status < 500;
        } catch (error) {
            console.debug(`Endpoint test failed for ${baseUrl}:`, error.message);
            return false;
        }
    }
    
    /**
     * Auto-detect best endpoint (only if no saved config exists)
     */
    async autoDetect() {
        // If user has explicitly saved a cloud config, respect it
        if (this.useCloud && this.apiUrl !== CONFIG.LOCAL_API) {
            console.log('User has saved cloud config, testing it first');
            if (await this.testEndpoint(this.apiUrl)) {
                return 'cloud';
            } else {
                console.log('Saved cloud config failed, falling back to local');
            }
        }
        
        // Test local as fallback
        if (await this.testEndpoint(CONFIG.LOCAL_API)) {
            // Only save if no cloud config was explicitly set
            if (!this.useCloud) {
                await this.saveConfig(CONFIG.LOCAL_API, false);
            }
            return 'local';
        }
        
        return 'none';
    }
    
    /**
     * Get current config
     */
    getConfig() {
        return {
            apiUrl: this.apiUrl,
            useCloud: this.useCloud,
            endpoint: this.getApiEndpoint()
        };
    }
}

// Create global instance
window.SIMPLE_CONFIG = new SimpleConfigManager();