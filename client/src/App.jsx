import { useCallback, useEffect, useRef, useState } from "react";
import "./index.css";
import ThemeToggle from "./components/ThemeToggle";
import Sidebar from "./components/Sidebar";
import PromptCard from "./components/PromptCard";
import ModeSelector from "./components/ModeSelector";
import ExplanationPanel from "./components/ExplanationPanel";
import VisualPanel from "./components/VisualPanel";
import FollowUpChips from "./components/FollowUpChips";
import LoadingSteps from "./components/LoadingSteps";
import DeclinePanel from "./components/DeclinePanel";
import ConversationPreview from "./components/ConversationPreview";
import EmptyState from "./components/EmptyState";
import { examplePrompts } from "./data/fakeExplanation";
import { textLoadingSteps, visualLoadingSteps } from "./data/loadingSteps";
import {
  clearConversationTurns,
  deleteConversation,
  explainQuestion,
  getConversation,
  getConversations,
  saveConversationTurn,
} from "./api/explainApi";

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function App() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("text");
  const [history, setHistory] = useState([]);
  const [currentMessages, setCurrentMessages] = useState([]);
  const [currentTurns, setCurrentTurns] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [activeTurnId, setActiveTurnId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [currentResult, setCurrentResult] = useState(null);
  const [error, setError] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const abortControllerRef = useRef(null);

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("conceptcanvas-theme") || "light";
  });

  const loadingSteps = mode === "visual" ? visualLoadingSteps : textLoadingSteps;

  function createAssistantMessage(result) {
    if (!result) {
      return "";
    }

    if (result.topicType === "declined") {
      return result.message || "This question cannot be answered.";
    }

    const explanation = result.explanation || {};

    return [
      explanation.title,
      explanation.quickMeaning,
      explanation.deepExplanation,
      `Steps: ${(explanation.stepByStep || []).join(" ")}`,
      `Example: ${explanation.realWorldExample || ""}`,
    ]
      .filter(Boolean)
      .join("\n");
  }

  function buildMessagesFromTurns(turns) {
    return turns.flatMap((turn) => [
      {
        role: "user",
        content: turn.question,
      },
      {
        role: "assistant",
        content: createAssistantMessage(turn.result),
      },
    ]);
  }

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations();

      const normalizedConversations = (data.conversations || []).map(
        (conversation) => ({
          ...conversation,
          question: conversation.first_question,
          lastQuestion: conversation.last_question,
          createdAt: conversation.created_at,
          updatedAt: conversation.updated_at,
        }),
      );

      setHistory(normalizedConversations);
    } catch (loadError) {
      console.error("Failed to load conversations:", loadError);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    getConversations()
      .then((data) => {
        if (!isMounted) return;

        const normalizedConversations = (data.conversations || []).map(
          (conversation) => ({
            ...conversation,
            question: conversation.first_question,
            lastQuestion: conversation.last_question,
            createdAt: conversation.created_at,
            updatedAt: conversation.updated_at,
          }),
        );

        setHistory(normalizedConversations);
      })
      .catch((loadError) => {
        console.error("Failed to load conversations:", loadError);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    localStorage.setItem("conceptcanvas-theme", theme);
  }, [theme]);

  async function handleGenerate() {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isLoading) return;

    setCurrentResult(null);
    setError("");
    setIsLoading(true);
    setActiveStep(0);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const conversationHistory = currentMessages.slice(-6);

      const backendRequest = explainQuestion({
        question: trimmedQuestion,
        mode,
        conversationHistory,
        signal: abortController.signal,
      });

      for (let index = 0; index < loadingSteps.length; index += 1) {
        setActiveStep(index);
        await delay(700);
      }

      const result = await backendRequest;

      const savedTurn = await saveConversationTurn({
        conversationId: activeConversationId,
        question: trimmedQuestion,
        mode,
        result,
      });

      const newTurn = {
        id: savedTurn.turnId,
        question: trimmedQuestion,
        mode,
        result,
        created_at: new Date().toISOString(),
      };

      const nextTurns = [...currentTurns, newTurn];

      const userMessage = {
        role: "user",
        content: trimmedQuestion,
      };

      const assistantMessage = {
        role: "assistant",
        content: createAssistantMessage(result),
      };

      const nextMessages = [...currentMessages, userMessage, assistantMessage];

      setActiveConversationId(savedTurn.conversationId);
      setActiveTurnId(savedTurn.turnId);
      setCurrentTurns(nextTurns);
      setCurrentMessages(nextMessages);
      setCurrentResult(result);
      setQuestion("");

      await loadConversations();
    } catch (apiError) {
      if (apiError.name === "AbortError") {
        setError("Generation cancelled.");
        return;
      }

      console.error(apiError);
      setError(
        "Could not generate the explanation. Please check if FastAPI is running and try again.",
      );
    } finally {
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }

  function handleSelectTurn(turnId) {
    const selectedTurn = currentTurns.find((turn) => turn.id === turnId);

    if (!selectedTurn) {
      return;
    }

    setActiveTurnId(selectedTurn.id);
    setMode(selectedTurn.mode || "text");
    setCurrentResult(selectedTurn.result);
    setError("");
  }

  function handleThemeToggle() {
    setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"));
  }

  function handleExamplePromptClick(prompt) {
    if (isLoading) return;

    setQuestion(prompt);
    setError("");
  }

  function handleCancelGeneration() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setIsLoading(false);
    setActiveStep(0);
    setError("Generation cancelled.");
  }

  function handleFollowUpClick(prompt) {
    if (isLoading) return;

    setQuestion(prompt);
    setError("");
  }

  function handleNewChat() {
    setActiveConversationId(null);
    setActiveTurnId(null);
    setQuestion("");
    setCurrentMessages([]);
    setCurrentTurns([]);
    setCurrentResult(null);
    setError("");
  }

  async function handleClearConversation() {
    if (!activeConversationId) {
      setCurrentMessages([]);
      setCurrentTurns([]);
      setCurrentResult(null);
      setActiveTurnId(null);
      setQuestion("");
      return;
    }

    try {
      await clearConversationTurns(activeConversationId);

      setCurrentMessages([]);
      setCurrentTurns([]);
      setCurrentResult(null);
      setActiveTurnId(null);
      setQuestion("");

      await loadConversations();
    } catch (clearError) {
      console.error(clearError);
      setError("Failed to clear conversation");
    }
  }

  async function handleDeleteHistoryItem(conversationId) {
    try {
      await deleteConversation(conversationId);

      if (conversationId === activeConversationId) {
        handleNewChat();
      }

      await loadConversations();
    } catch (deleteError) {
      console.error(deleteError);
      setError("Failed to delete conversation");
    }
  }

  async function handleClearAllHistory() {
    if (isLoading) return;

    try {
      await Promise.all(history.map((item) => deleteConversation(item.id)));

      setHistory([]);
      handleNewChat();
    } catch (clearAllError) {
      console.error(clearAllError);
      setError("Failed to clear all conversations");
    }
  }

  async function handleSelectHistory(item) {
    try {
      const data = await getConversation(item.id);

      if (data.status !== "success") {
        setError("Conversation not found");
        return;
      }

      const conversation = data.conversation;
      const turns = conversation.turns || [];
      const latestTurn = turns[turns.length - 1];

      setActiveConversationId(conversation.id);
      setCurrentTurns(turns);
      setCurrentMessages(buildMessagesFromTurns(turns));
      setActiveTurnId(latestTurn?.id || null);
      setCurrentResult(latestTurn?.result || null);
      setMode(latestTurn?.mode || "text");
      setQuestion("");
      setError("");
    } catch (selectError) {
      console.error(selectError);
      setError("Failed to open conversation");
    }
  }

  const isConceptExplanation =
    currentResult?.topicType === "concept_explanation";

  const isDeclined = currentResult?.topicType === "declined";

  return (
    <div
      data-theme={theme}
      className="app-theme min-h-screen bg-[#f7f8fb] text-gray-900"
    >
      <div className="flex min-h-screen">
        <Sidebar
          history={history}
          activeConversationId={activeConversationId}
          onNewChat={handleNewChat}
          onSelectHistory={handleSelectHistory}
          onDeleteHistoryItem={handleDeleteHistoryItem}
          onClearAllHistory={handleClearAllHistory}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          disabled={isLoading}
        />

        <main className="flex-1 p-4 md:p-8">
          <div className="mb-4 flex items-center justify-between rounded-2xl bg-white p-4 shadow-sm md:hidden">
            <div>
              <h1 className="text-lg font-bold text-blue-900">
                ConceptCanvas
              </h1>
              <p className="text-xs text-gray-500">
                AI visual learning tutor
              </p>
            </div>

            <div className="flex items-center gap-2">
              <ThemeToggle theme={theme} onToggle={handleThemeToggle} />

              <button
                onClick={() => setIsSidebarOpen(true)}
                className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-2 text-sm font-semibold text-gray-700"
              >
                Menu
              </button>
            </div>
          </div>

          <div className="mx-auto max-w-6xl">
            <div className="mb-8 rounded-[2rem] border border-gray-100 bg-white p-6 shadow-sm md:p-8">
              <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
                  Ask anything. Choose how you learn.
                </p>

                <div className="hidden md:block">
                  <ThemeToggle theme={theme} onToggle={handleThemeToggle} />
                </div>
              </div>

              <h2 className="text-3xl font-bold tracking-tight text-gray-950 md:text-5xl">
                Learn any concept with text, visuals, and narration.
              </h2>

              <p className="mt-3 max-w-2xl text-gray-500">
                Ask a concept-based question and choose how you want to learn:
                a structured answer or a whiteboard-style visual explanation.
              </p>

              <div className="mt-6 grid gap-3 md:grid-cols-4">
                {examplePrompts.map((prompt) => (
                  <PromptCard
                    key={prompt}
                    prompt={prompt}
                    onClick={handleExamplePromptClick}
                    disabled={isLoading}
                  />
                ))}
              </div>

              <div className="mt-6 rounded-3xl border border-gray-200 bg-gray-50 p-4">
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="Example: Explain recursion with a simple example..."
                  className="min-h-24 w-full resize-none bg-transparent text-base outline-none placeholder:text-gray-400"
                  disabled={isLoading}
                />

                <div className="mt-4 flex flex-col gap-3 border-t border-gray-200 pt-4 md:flex-row md:items-center md:justify-between">
                  <ModeSelector
                    mode={mode}
                    onModeChange={setMode}
                    disabled={isLoading}
                  />

                  <button
                    onClick={handleGenerate}
                    disabled={isLoading || !question.trim()}
                    className={`rounded-xl px-6 py-2.5 text-sm font-semibold text-white ${isLoading || !question.trim()
                      ? "cursor-not-allowed bg-gray-400"
                      : "bg-green-700 hover:bg-green-600"
                      }`}
                  >
                    {isLoading ? "Creating..." : "Generate explanation"}
                  </button>
                </div>
              </div>
            </div>

            <ConversationPreview
              turns={currentTurns}
              activeTurnId={activeTurnId}
              onSelectTurn={handleSelectTurn}
              onClearConversation={handleClearConversation}
            />

            {isLoading && (
              <LoadingSteps
                steps={loadingSteps}
                activeStep={activeStep}
                onCancel={handleCancelGeneration}
              />
            )}

            {error && (
              <div className="mb-8 rounded-3xl border border-red-100 bg-red-50 p-5 text-sm text-red-700 shadow-sm">
                {error}
              </div>
            )}

            {!isLoading && !currentResult && <EmptyState />}

            {isDeclined && (
              <DeclinePanel
                message={currentResult.message}
                suggestions={currentResult.suggestions}
                onSuggestionClick={handleExamplePromptClick}
                disabled={isLoading}
              />
            )}

            {isConceptExplanation && mode === "visual" && (
              <div className="space-y-8">
                <div className="mx-auto max-w-6xl">
                  <VisualPanel
                    storyboard={currentResult.storyboard}
                    storyboardSource={currentResult.storyboardSource}
                    storyboardModelUsed={currentResult.storyboardModelUsed}
                  />
                </div>

                <div className="mx-auto max-w-6xl">
                  <ExplanationPanel
                    explanation={currentResult.explanation}
                    source={currentResult.source}
                    modelUsed={currentResult.modelUsed}
                  />
                </div>

                {currentResult.followUps?.length > 0 && (
                  <div className="mx-auto max-w-6xl">
                    <FollowUpChips
                      followUps={currentResult.followUps}
                      onFollowUpClick={handleFollowUpClick}
                      disabled={isLoading}
                    />
                  </div>
                )}
              </div>
            )}

            {isConceptExplanation && mode !== "visual" && (
              <div className="space-y-8">
                <div className="mx-auto max-w-6xl">
                  <ExplanationPanel
                    explanation={currentResult.explanation}
                    source={currentResult.source}
                    modelUsed={currentResult.modelUsed}
                  />
                </div>

                {currentResult.followUps?.length > 0 && (
                  <div className="mx-auto max-w-6xl">
                    <FollowUpChips
                      followUps={currentResult.followUps}
                      onFollowUpClick={handleFollowUpClick}
                      disabled={isLoading}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;