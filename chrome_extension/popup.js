
// Configuration will be loaded dynamically
let API_ENDPOINT = 'http://127.0.0.1:5000/log'; // Default fallback

// DOM Elements
const loadingDiv = document.getElementById('loading');
const errorMessageDiv = document.getElementById('error-message');
const successMessageDiv = document.getElementById('success-message');
const logForm = document.getElementById('log-form');
const submitBtn = document.getElementById('submit-btn');

let problemData = {}; // To store data received from content script
let selectedTopics = []; // To store selected topics

// Global functions for updating topic display
function updateSelectedTopicsDisplay() {
    const selectedTopicsContainer = document.getElementById('selected-topics');
    selectedTopicsContainer.innerHTML = '';
    selectedTopics.forEach(topic => {
        const selectedTag = document.createElement('div');
        selectedTag.className = 'selected-tag';
        selectedTag.innerHTML = `
            <span>${topic}</span>
            <button type="button" class="remove-tag" data-value="${topic}">×</button>
        `;
        selectedTopicsContainer.appendChild(selectedTag);
    });

    // Add event listeners to remove buttons
    document.querySelectorAll('.remove-tag').forEach(btn => {
        btn.addEventListener('click', () => {
            const value = btn.dataset.value;
            selectedTopics = selectedTopics.filter(topic => topic !== value);
            document.querySelector(`[data-value="${value}"]`).classList.remove('selected');
            updateSelectedTopicsDisplay();
            updateHiddenInput();
        });
    });
}

function updateHiddenInput() {
    const hiddenInput = document.getElementById('topic');
    if (hiddenInput) {
        hiddenInput.value = selectedTopics.join(', ');
    }
}

/**
 * Initialize topic selection functionality
 */
function initializeTopicSelection() {
    const topicTags = document.querySelectorAll('.topic-tag');

    topicTags.forEach(tag => {
        tag.addEventListener('click', () => {
            const value = tag.dataset.value;
            
            if (selectedTopics.includes(value)) {
                // Remove topic
                selectedTopics = selectedTopics.filter(topic => topic !== value);
                tag.classList.remove('selected');
            } else {
                // Add topic
                selectedTopics.push(value);
                tag.classList.add('selected');
            }
            
            updateSelectedTopicsDisplay();
            updateHiddenInput();
        });
    });
}

/**
 * Main function that runs when the popup is opened.
 */
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize simple configuration
    try {
        await window.SIMPLE_CONFIG.init();
        updateApiEndpoint();
        
        console.log('LeetCode Journey - Using API:', API_ENDPOINT);
        
        initializeTopicSelection();
        
        // Only auto-detect if no configuration exists
        const currentConfig = window.SIMPLE_CONFIG.getConfig();
        if (!currentConfig.useCloud && currentConfig.apiUrl === 'http://127.0.0.1:5000') {
            console.log('No saved config found, attempting auto-detection');
            const detection = await window.SIMPLE_CONFIG.autoDetect();
            if (detection !== 'none') {
                updateApiEndpoint();
                console.log(`Auto-detected ${detection} endpoint:`, API_ENDPOINT);
            }
        } else {
            console.log('Using saved configuration:', currentConfig);
        }
    } catch (error) {
        console.error('Configuration failed:', error);
        // Use default
        API_ENDPOINT = 'http://127.0.0.1:5000/log';
    }
    
    // Listen for configuration updates
    setupConfigListener();
    
    // Query for the active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const activeTab = tabs[0];
        // Check if we are on a LeetCode problem page
        if (activeTab.url && activeTab.url.includes("leetcode.com/problems")) {
            // Send a message to the content script to get problem details
            chrome.tabs.sendMessage(activeTab.id, { type: "GET_PROBLEM_DETAILS" }, (response) => {
                // DEBUG: Log whatever response we get from the content script.
                console.log("Response from content script:", response);

                if (chrome.runtime.lastError) {
                    // Handle cases where the content script hasn't been injected yet
                    showError(`Could not connect to the page: ${chrome.runtime.lastError.message}. Please refresh the LeetCode tab and try again.`);
                    return;
                }

                if (response && !response.error) {
                    handleDataReceived(response);
                } else {
                    showError(response ? response.error : "No response from content script.");
                }
            });
        } else {
            showError("This extension only works on LeetCode problem pages.");
        }
    });
});

/**
 * Handles the data received from the content script.
 * @param {object} data - The problem details scraped from the page.
 */
function handleDataReceived(data) {
    problemData = data; // Store for later submission
    loadingDiv.classList.add('hidden');

    // Populate the form fields
    document.getElementById('problem_number').value = data.problem_number;
    document.getElementById('name').value = data.name;
    
    // Set difficulty dropdown to match scraped data
    const difficultySelect = document.getElementById('difficulty');
    if (data.difficulty && ['Easy', 'Medium', 'Hard'].includes(data.difficulty)) {
        difficultySelect.value = data.difficulty;
    }
    
    // Auto-select topics from scraped data
    if (data.topic) {
        const scrapedTopics = data.topic.split(', ').map(topic => topic.trim());
        const availableTopics = Array.from(document.querySelectorAll('.topic-tag')).map(tag => tag.dataset.value);
        
        scrapedTopics.forEach(topic => {
            if (availableTopics.includes(topic) && !selectedTopics.includes(topic)) {
                selectedTopics.push(topic);
                const topicElement = document.querySelector(`[data-value="${topic}"]`);
                if (topicElement) {
                    topicElement.classList.add('selected');
                }
            }
        });
        
        // Update display and hidden input
        updateSelectedTopicsDisplay();
        updateHiddenInput();
    }

    logForm.classList.remove('hidden');
}

/**
 * Handles the form submission.
 * @param {Event} e - The form submission event.
 */
logForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // Prevent default form submission

    // Disable button to prevent multiple submissions
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';

    // Collect data from the form
    const formData = {
        problem_number: problemData.problem_number,
        name: problemData.name,
        url: problemData.url,
        difficulty: document.getElementById('difficulty').value,
        topic: document.getElementById('topic').value,
        notes: document.getElementById('notes').value,
    };

    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        const result = await response.json();

        if (response.ok) {
            showSuccess();
        } else {
            showError(`Error from server: ${result.message}`);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save to Google Sheet';
        }
    } catch (error) {
        const isLocal = API_ENDPOINT.includes('127.0.0.1') || API_ENDPOINT.includes('localhost');
        const errorMsg = isLocal 
            ? `Failed to connect to the local server. Is it running? Error: ${error.message}`
            : `Failed to connect to the API server. Error: ${error.message}`;
        showError(errorMsg);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save to Google Sheet';
    }
});

/**
 * Displays an error message in the popup.
 * @param {string} message - The error message to display.
 */
function showError(message) {
    loadingDiv.classList.add('hidden');
    errorMessageDiv.textContent = message;
    errorMessageDiv.classList.remove('hidden');
}

/**
 * Hides the form and shows a success message.
 */
function showSuccess() {
    logForm.classList.add('hidden');
    successMessageDiv.classList.remove('hidden');
    // Close the popup after a short delay
    setTimeout(() => {
        window.close();
    }, 2000);
}

/**
 * Update API endpoint from config
 */
function updateApiEndpoint() {
    API_ENDPOINT = window.SIMPLE_CONFIG.getApiEndpoint();
}

/**
 * Setup listener for config changes
 */
function setupConfigListener() {
    if (typeof chrome !== 'undefined' && chrome.runtime) {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            if (message.type === 'CONFIG_UPDATED') {
                console.log('Configuration updated, refreshing API endpoint');
                updateApiEndpoint();
                console.log('New API endpoint:', API_ENDPOINT);
            }
        });
    }
}
