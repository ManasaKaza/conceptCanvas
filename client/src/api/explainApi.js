const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function explainQuestion({
    question,
    mode,
    conversationHistory,
    signal,
}) {
    const response = await fetch(`${API_BASE_URL}/api/explain`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        signal,
        body: JSON.stringify({
            question,
            mode,
            conversationHistory,
        }),
    });

    if (!response.ok) {
        throw new Error("Failed to generate explanation");
    }

    return response.json();
}

export async function getConversations() {
    const response = await fetch(`${API_BASE_URL}/api/conversations`);

    if (!response.ok) {
        throw new Error("Failed to load conversations");
    }

    return response.json();
}

export async function getConversation(conversationId) {
    const response = await fetch(
        `${API_BASE_URL}/api/conversations/${conversationId}`,
    );

    if (!response.ok) {
        throw new Error("Failed to load conversation");
    }

    return response.json();
}

export async function saveConversationTurn({
    conversationId,
    question,
    mode,
    result,
}) {
    const response = await fetch(`${API_BASE_URL}/api/conversations/turns`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            conversationId,
            question,
            mode,
            result,
        }),
    });

    if (!response.ok) {
        throw new Error("Failed to save conversation turn");
    }

    return response.json();
}

export async function deleteConversation(conversationId) {
    const response = await fetch(
        `${API_BASE_URL}/api/conversations/${conversationId}`,
        {
            method: "DELETE",
        },
    );

    if (!response.ok) {
        throw new Error("Failed to delete conversation");
    }

    return response.json();
}

export async function clearConversationTurns(conversationId) {
    const response = await fetch(
        `${API_BASE_URL}/api/conversations/${conversationId}/turns`,
        {
            method: "DELETE",
        },
    );

    if (!response.ok) {
        throw new Error("Failed to clear conversation");
    }

    return response.json();
}