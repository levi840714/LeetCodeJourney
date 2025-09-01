// Settings page JavaScript for LeetCode Journey

let configManager;

// DOM Elements
const localRadio = document.getElementById('local-radio');
const cloudRadio = document.getElementById('cloud-radio');
const cloudUrlGroup = document.getElementById('cloud-url-group');
const cloudUrlInput = document.getElementById('cloud-url');
const currentApiSpan = document.getElementById('current-api');
const connectionStatus = document.getElementById('connection-status');
const localStatus = document.getElementById('local-status');
const cloudStatus = document.getElementById('cloud-status');

const saveBtn = document.getElementById('save-settings');
const autoDetectBtn = document.getElementById('auto-detect');
const resetBtn = document.getElementById('reset-settings');
const testBtn = document.getElementById('test-connection');

/**
 * Initialize settings page
 */
document.addEventListener('DOMContentLoaded', async () => {
    configManager = window.SIMPLE_CONFIG;
    await configManager.init();
    
    loadCurrentSettings();
    setupEventListeners();
    testConnections();
});

/**
 * Load current settings from storage
 */
function loadCurrentSettings() {
    const config = configManager.getConfig();
    const apiUrl = config.apiUrl;
    const useCloud = config.useCloud;
    
    // Update current API display
    currentApiSpan.textContent = configManager.getApiEndpoint();
    
    // Set radio buttons
    if (useCloud && apiUrl !== 'http://127.0.0.1:5000') {
        cloudRadio.checked = true;
        cloudUrlInput.value = apiUrl;
        cloudUrlGroup.style.display = 'block';
    } else {
        localRadio.checked = true;
        cloudUrlGroup.style.display = 'none';
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Radio button change handlers
    localRadio.addEventListener('change', () => {
        if (localRadio.checked) {
            cloudUrlGroup.style.display = 'none';
        }
    });
    
    cloudRadio.addEventListener('change', () => {
        if (cloudRadio.checked) {
            cloudUrlGroup.style.display = 'block';
        }
    });
    
    // Button handlers
    saveBtn.addEventListener('click', saveSettings);
    autoDetectBtn.addEventListener('click', autoDetectSettings);
    resetBtn.addEventListener('click', resetSettings);
    testBtn.addEventListener('click', testConnections);
    
    // Cloud URL input validation
    cloudUrlInput.addEventListener('input', () => {
        const url = cloudUrlInput.value;
        if (url && !configManager.isValidUrl(url)) {
            cloudUrlInput.style.borderColor = '#f44336';
        } else {
            cloudUrlInput.style.borderColor = '#ccc';
        }
    });
}

/**
 * Save settings
 */
async function saveSettings() {
    saveBtn.disabled = true;
    saveBtn.textContent = '💾 Saving...';
    
    try {
        if (localRadio.checked) {
            await configManager.useLocalDevelopment();
        } else if (cloudRadio.checked) {
            const cloudUrl = cloudUrlInput.value.trim();
            if (!cloudUrl) {
                throw new Error('Cloud Functions URL is required');
            }
            if (!configManager.isValidUrl(cloudUrl)) {
                throw new Error('Invalid URL format');
            }
            await configManager.useCloudFunctions(cloudUrl);
        }
        
        // Update display
        loadCurrentSettings();
        showStatus('✅ Settings saved successfully!', 'success');
        
        // Test new connection
        setTimeout(testConnections, 1000);
        
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Save Settings';
    }
}

/**
 * Auto-detect best settings
 */
async function autoDetectSettings() {
    autoDetectBtn.disabled = true;
    autoDetectBtn.textContent = '🔍 Detecting...';
    
    showStatus('🔍 Testing available endpoints...', 'info');
    
    try {
        const result = await configManager.autoDetectBestEndpoint();
        
        switch (result) {
            case 'local':
                localRadio.checked = true;
                cloudUrlGroup.style.display = 'none';
                showStatus('✅ Auto-detected: Local development server', 'success');
                break;
            case 'cloud':
                cloudRadio.checked = true;
                cloudUrlGroup.style.display = 'block';
                cloudUrlInput.value = configManager.getConfig().apiUrl;
                showStatus('✅ Auto-detected: Cloud Functions', 'success');
                break;
            case 'none':
                showStatus('⚠️ No endpoints available. Please configure manually.', 'warning');
                break;
        }
        
        loadCurrentSettings();
        testConnections();
        
    } catch (error) {
        showStatus(`❌ Auto-detection failed: ${error.message}`, 'error');
    } finally {
        autoDetectBtn.disabled = false;
        autoDetectBtn.textContent = '🔍 Auto Detect';
    }
}

/**
 * Reset to default settings
 */
async function resetSettings() {
    if (!confirm('Reset all settings to default? This will clear your Cloud Functions URL.')) {
        return;
    }
    
    resetBtn.disabled = true;
    resetBtn.textContent = '🔄 Resetting...';
    
    try {
        await configManager.reset();
        loadCurrentSettings();
        testConnections();
        showStatus('✅ Settings reset to default', 'success');
    } catch (error) {
        showStatus(`❌ Reset failed: ${error.message}`, 'error');
    } finally {
        resetBtn.disabled = false;
        resetBtn.textContent = '🔄 Reset to Default';
    }
}

/**
 * Test connections to endpoints
 */
async function testConnections() {
    testBtn.disabled = true;
    testBtn.textContent = '🔍 Testing...';
    
    // Reset status indicators
    localStatus.className = 'status-indicator status-testing';
    cloudStatus.className = 'status-indicator status-testing';
    
    connectionStatus.innerHTML = 'Testing connections...';
    
    try {
        // Test local endpoint
        const localAvailable = await configManager.testEndpoint('http://127.0.0.1:5000');
        localStatus.className = `status-indicator ${localAvailable ? 'status-online' : 'status-offline'}`;
        
        // Test cloud endpoint if configured
        const config = configManager.getConfig();
        let cloudAvailable = false;
        if (config.useCloud && config.apiUrl !== 'http://127.0.0.1:5000') {
            cloudAvailable = await configManager.testEndpoint(config.apiUrl);
        } else if (cloudUrlInput.value.trim()) {
            cloudAvailable = await configManager.testEndpoint(cloudUrlInput.value.trim());
        }
        cloudStatus.className = `status-indicator ${cloudAvailable ? 'status-online' : 'status-offline'}`;
        
        // Update connection status
        const statusMessages = [];
        if (localAvailable) statusMessages.push('✅ Local server: Online');
        else statusMessages.push('❌ Local server: Offline');
        
        if (config.useCloud || cloudUrlInput.value.trim()) {
            if (cloudAvailable) statusMessages.push('✅ Cloud Functions: Online');
            else statusMessages.push('❌ Cloud Functions: Offline');
        } else {
            statusMessages.push('⚪ Cloud Functions: Not configured');
        }
        
        connectionStatus.innerHTML = statusMessages.join('<br>');
        
        // Show current active endpoint status
        const currentEndpoint = configManager.getApiEndpoint();
        const currentAvailable = await configManager.testEndpoint(configManager.getConfig().apiUrl);
        
        if (currentAvailable) {
            showStatus(`✅ Current endpoint (${currentEndpoint}) is online`, 'success');
        } else {
            showStatus(`❌ Current endpoint (${currentEndpoint}) is offline`, 'error');
        }
        
    } catch (error) {
        showStatus(`❌ Connection test failed: ${error.message}`, 'error');
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = '🔍 Test Connection';
    }
}

/**
 * Show status message
 */
function showStatus(message, type = 'info') {
    // Create or update status div
    let statusDiv = document.getElementById('status-message');
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.id = 'status-message';
        statusDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            max-width: 300px;
        `;
        document.body.appendChild(statusDiv);
    }
    
    // Set color based on type
    const colors = {
        success: '#4CAF50',
        error: '#f44336',
        warning: '#FF9800',
        info: '#2196F3'
    };
    
    statusDiv.style.backgroundColor = colors[type] || colors.info;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
    }, 5000);
}