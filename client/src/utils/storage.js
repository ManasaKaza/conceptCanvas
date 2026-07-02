const HISTORY_KEY = "conceptcanvas_history";

export function loadHistory() {
    try {
        const storedHistory = localStorage.getItem(HISTORY_KEY);

        if (!storedHistory) {
            return [];
        }

        return JSON.parse(storedHistory);
    } catch (error) {
        console.error("Failed to load history:", error);
        return [];
    }
}

export function saveHistory(history) {
    try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (error) {
        console.error("Failed to save history:", error);
    }
}