
// This script runs in the context of the LeetCode problem page.

/**
 * Listens for a message from the popup script, then scrapes the page for problem data.
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "GET_PROBLEM_DETAILS") {
        try {
            const details = scrapeProblemDetails();
            sendResponse(details);
        } catch (error) {
            sendResponse({ error: `Failed to scrape page: ${error.message}` });
        }
    }
    // Keep the message channel open for the asynchronous response.
    return true;
});

/**
 * Scrapes the LeetCode problem page DOM to find the required information.
 * Note: These selectors are based on LeetCode's current HTML structure and may break if they change it.
 */
function scrapeProblemDetails() {
    // --- Final, more robust selectors based on user-provided HTML ---

    // Extract problem title element
    const titleElement = document.querySelector('a.no-underline[href*="/problems/"]');
    const title = titleElement ? titleElement.textContent.trim() : 'Not found';

    // Split title into number and name
    const parts = title.match(/^(\d+)\.\s*(.*)$/);
    const problem_number = parts ? parts[1] : 'N/A';
    const name = parts ? parts[2] : title;

    // Extract difficulty
    const difficultyElement = document.querySelector('div[class*="text-difficulty-"]');
    const difficulty = difficultyElement ? difficultyElement.textContent.trim() : 'Not found';

    // Extract Topics/Tags
    const topicElements = document.querySelectorAll('a[href*="/tag/"]');
    const topic = Array.from(topicElements).map(el => el.textContent.trim()).join(', ');

    // Get current URL
    const url = window.location.href;

    return {
        problem_number,
        name,
        difficulty,
        topic,
        url
    };
}
