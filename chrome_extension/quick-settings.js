// Quick Settings JavaScript for LeetCode Journey Chrome Extension

let config;
let selectedMode = 'local';

document.addEventListener('DOMContentLoaded', async () => {
    config = window.SIMPLE_CONFIG;
    await config.init();
    
    loadCurrentConfig();
    setupEventListeners();
});

function loadCurrentConfig() {
    const currentConfig = config.getConfig();
    document.getElementById('current-endpoint').textContent = currentConfig.endpoint;
    
    if (currentConfig.useCloud) {
        selectCloudOption();
        document.getElementById('cloud-url').value = currentConfig.apiUrl;
    } else {
        selectLocalOption();
    }
}

function setupEventListeners() {
    document.getElementById('local-option').addEventListener('click', selectLocalOption);
    document.getElementById('cloud-option').addEventListener('click', selectCloudOption);
    document.getElementById('save-btn').addEventListener('click', saveConfig);
    document.getElementById('test-btn').addEventListener('click', testConnection);
}

function selectLocalOption() {
    selectedMode = 'local';
    updateSelection();
}

function selectCloudOption() {
    selectedMode = 'cloud';
    updateSelection();
}

function updateSelection() {
    const localOption = document.getElementById('local-option');
    const cloudOption = document.getElementById('cloud-option');
    const cloudUrl = document.getElementById('cloud-url');
    
    localOption.classList.remove('selected');
    cloudOption.classList.remove('selected');
    
    if (selectedMode === 'local') {
        localOption.classList.add('selected');
        cloudUrl.style.display = 'none';
    } else {
        cloudOption.classList.add('selected');
        cloudUrl.style.display = 'block';
    }
}

async function saveConfig() {
    const saveBtn = document.getElementById('save-btn');
    saveBtn.textContent = '💾 Saving...';
    saveBtn.disabled = true;
    
    try {
        if (selectedMode === 'local') {
            await config.saveConfig('http://127.0.0.1:5000', false);
            console.log('Saved local config');
        } else {
            const cloudUrl = document.getElementById('cloud-url').value.trim();
            if (!cloudUrl) {
                throw new Error('Cloud Function URL is required');
            }
            await config.saveConfig(cloudUrl, true);
            console.log('Saved cloud config:', cloudUrl);
        }
        
        // Force reload config to verify it was saved
        await config.init();
        loadCurrentConfig();
        
        // Verify save by logging current config
        const currentConfig = config.getConfig();
        console.log('Config after save:', currentConfig);
        
        showStatus('✅ Configuration saved!', 'success');
    } catch (error) {
        console.error('Save config error:', error);
        showStatus('❌ ' + error.message, 'error');
    } finally {
        saveBtn.textContent = '💾 Save';
        saveBtn.disabled = false;
    }
}

async function testConnection() {
    const testBtn = document.getElementById('test-btn');
    testBtn.textContent = '🔍 Testing...';
    testBtn.disabled = true;
    
    showStatus('🔍 Testing connection...', 'info');
    
    try {
        // Get URL to test based on current selection
        let urlToTest;
        if (selectedMode === 'local') {
            urlToTest = 'http://127.0.0.1:5000';
        } else {
            urlToTest = document.getElementById('cloud-url').value.trim();
            if (!urlToTest) {
                showStatus('❌ Please enter Cloud Function URL first', 'error');
                return;
            }
        }
        
        const isOnline = await config.testEndpoint(urlToTest);
        
        if (isOnline) {
            showStatus('✅ Connection successful!', 'success');
        } else {
            showStatus('❌ Connection failed', 'error');
        }
    } catch (error) {
        showStatus('❌ Test failed: ' + error.message, 'error');
    } finally {
        testBtn.textContent = '🔍 Test';
        testBtn.disabled = false;
    }
}

function showStatus(message, type) {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = `status ${type}`;
    status.style.display = 'block';
    
    setTimeout(() => {
        status.style.display = 'none';
    }, 3000);
}