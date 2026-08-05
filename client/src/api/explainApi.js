const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function throwResponseError(response, fallbackMessage) {
    let message = fallbackMessage;

    try {
        const payload = await response.json();
        if (typeof payload?.detail === "string") {
            message = payload.detail;
        } else if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
            message = payload.detail
                .map((item) => item?.msg)
                .filter(Boolean)
                .join(" ");
        } else if (typeof payload?.message === "string") {
            message = payload.message;
        }
    } catch {
        // Keep the user-friendly fallback when the response is not JSON.
    }

    throw new Error(message);
}

export async function explainQuestion({
    question,
    mode,
    audienceLevel,
    explanationDepth,
    requestedSceneCount,
    requestedStructure = [],
    narrationEnabled = true,
    groundingMode = "preferred",
    conversationHistory,
    signal,
}) {
    const response = await fetch(`${API_BASE_URL}/api/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal,
        body: JSON.stringify({
            schemaVersion: "1.1",
            question,
            mode,
            audienceLevel,
            explanationDepth,
            requestedSceneCount,
            requestedStructure,
            narrationEnabled,
            groundingMode,
            conversationHistory,
        }),
    });

    if (!response.ok) {
        await throwResponseError(response, "Failed to generate explanation");
    }

    return response.json();
}

export async function getConversations() {
    const response = await fetch(`${API_BASE_URL}/api/conversations`);
    if (!response.ok) {
        await throwResponseError(response, "Failed to load conversations");
    }
    return response.json();
}

export async function getConversation(conversationId) {
    const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`);
    if (!response.ok) {
        await throwResponseError(response, "Failed to load conversation");
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversationId, question, mode, result }),
    });

    if (!response.ok) {
        await throwResponseError(response, "Failed to save conversation turn");
    }
    return response.json();
}

export async function deleteConversation(conversationId) {
    const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
        method: "DELETE",
    });
    if (!response.ok) {
        await throwResponseError(response, "Failed to delete conversation");
    }
    return response.json();
}

export async function clearConversationTurns(conversationId) {
    const response = await fetch(
        `${API_BASE_URL}/api/conversations/${conversationId}/turns`,
        { method: "DELETE" },
    );
    if (!response.ok) {
        await throwResponseError(response, "Failed to clear conversation");
    }
    return response.json();
}
