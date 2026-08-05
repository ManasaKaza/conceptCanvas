import { useCallback, useEffect, useRef, useState } from "react";
import { Menu, Send, Sparkles } from "lucide-react";
import "./index.css";
import ThemeToggle from "./components/ThemeToggle";
import Sidebar from "./components/Sidebar";
import PromptCard from "./components/PromptCard";
import ModeSelector from "./components/ModeSelector";
import LessonSettings from "./components/LessonSettings";
import ExplanationPanel from "./components/ExplanationPanel";
import CollapsibleExplanation from "./components/CollapsibleExplanation";
import VisualPanel from "./components/VisualPanel";
import FollowUpChips from "./components/FollowUpChips";
import LoadingSteps from "./components/LoadingSteps";
import DeclinePanel from "./components/DeclinePanel";
import ConversationPreview from "./components/ConversationPreview";
import EmptyState from "./components/EmptyState";
import { examplePrompts } from "./data/fakeExplanation";
import {
  clearConversationTurns,
  deleteConversation,
  explainQuestion,
  getConversation,
  getConversations,
  saveConversationTurn,
} from "./api/explainApi";

function App() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("text");
  const [audienceLevel, setAudienceLevel] = useState("beginner");
  const [explanationDepth, setExplanationDepth] = useState("standard");
  const [requestedSceneCount, setRequestedSceneCount] = useState(null);
  const [groundingMode, setGroundingMode] = useState("preferred");
  const [history, setHistory] = useState([]);
  const [currentMessages, setCurrentMessages] = useState([]);
  const [currentTurns, setCurrentTurns] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [activeTurnId, setActiveTurnId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);
  const [error, setError] = useState("");
  const [saveWarning, setSaveWarning] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const abortControllerRef = useRef(null);

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("conceptcanvas-theme") || "light";
  });

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
    setSaveWarning("");
    setIsLoading(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const conversationHistory = currentMessages.slice(-6);

      const backendRequest = explainQuestion({
        question: trimmedQuestion,
        mode,
        audienceLevel,
        explanationDepth,
        requestedSceneCount,
        requestedStructure: [],
        narrationEnabled: true,
        groundingMode,
        conversationHistory,
        signal: abortController.signal,
      });

      const result = await backendRequest;
      const temporaryTurnId = `local-${Date.now()}`;
      const newTurn = {
        id: temporaryTurnId,
        question: trimmedQuestion,
        mode,
        result,
        created_at: new Date().toISOString(),
      };

      const userMessage = { role: "user", content: trimmedQuestion };
      const assistantMessage = {
        role: "assistant",
        content: createAssistantMessage(result),
      };

      setActiveTurnId(temporaryTurnId);
      setCurrentTurns((turns) => [...turns, newTurn]);
      setCurrentMessages((messages) => [
        ...messages,
        userMessage,
        assistantMessage,
      ]);
      setCurrentResult(result);
      setQuestion("");

      try {
        const savedTurn = await saveConversationTurn({
          conversationId: activeConversationId,
          question: trimmedQuestion,
          mode,
          result,
        });

        setActiveConversationId(savedTurn.conversationId);
        setActiveTurnId(savedTurn.turnId);
        setCurrentTurns((turns) =>
          turns.map((turn) =>
            turn.id === temporaryTurnId
              ? { ...turn, id: savedTurn.turnId }
              : turn,
          ),
        );
        await loadConversations();
      } catch (saveError) {
        console.error("Lesson generated but could not be saved:", saveError);
        setSaveWarning(
          "Your lesson was generated successfully, but it could not be added to history.",
        );
      }
    } catch (apiError) {
      if (apiError.name === "AbortError") {
        setError("Generation cancelled.");
        return;
      }

      console.error(apiError);
      setError(
        apiError.message ||
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
    setAudienceLevel(selectedTurn.result?.audienceLevel || "beginner");
    setExplanationDepth(selectedTurn.result?.explanationDepth || "standard");
    setRequestedSceneCount(
      selectedTurn.result?.storyboardValidation?.requestedSceneCount ?? null,
    );
    setGroundingMode(selectedTurn.result?.groundingReport?.mode || "preferred");
    setCurrentResult(selectedTurn.result);
    setError("");
    setSaveWarning("");
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
    setSaveWarning("");
  }

  async function handleClearConversation() {
    if (!activeConversationId) {
      setCurrentMessages([]);
      setCurrentTurns([]);
      setCurrentResult(null);
      setActiveTurnId(null);
      setQuestion("");
      setSaveWarning("");
      return;
    }

    try {
      await clearConversationTurns(activeConversationId);

      setCurrentMessages([]);
      setCurrentTurns([]);
      setCurrentResult(null);
      setActiveTurnId(null);
      setQuestion("");
      setSaveWarning("");

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
      setAudienceLevel(latestTurn?.result?.audienceLevel || "beginner");
      setExplanationDepth(latestTurn?.result?.explanationDepth || "standard");
      setRequestedSceneCount(
        latestTurn?.result?.storyboardValidation?.requestedSceneCount ?? null,
      );
      setGroundingMode(latestTurn?.result?.groundingReport?.mode || "preferred");
      setQuestion("");
      setError("");
      setSaveWarning("");
    } catch (selectError) {
      console.error(selectError);
      setError("Failed to open conversation");
    }
  }

  const isConceptExplanation =
    currentResult?.topicType === "concept_explanation";

  const isDeclined = currentResult?.topicType === "declined";

  const activeLessonTitle = currentResult?.title || currentResult?.explanation?.title;

  return (
    <div data-theme={theme} className="app-theme cc-app-shell">
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

        <main className="cc-main">
          <header className="cc-topbar">
            <div className="min-w-0">
              <div className="flex items-center gap-2 md:hidden">
                <div className="cc-brand-mark" aria-hidden="true"><span /><span /><span /></div>
                <strong className="text-sm text-gray-900">ConceptCanvas</strong>
              </div>
              <p className="hidden text-xs font-medium text-gray-400 md:block">
                {activeConversationId ? "Learning thread" : "Workspace"}
              </p>
              <h1 className="mt-0.5 hidden truncate text-base font-semibold tracking-[-0.02em] text-gray-900 md:block">
                {activeLessonTitle || "New visual lesson"}
              </h1>
            </div>

            <div className="flex items-center gap-2">
              <ThemeToggle theme={theme} onToggle={handleThemeToggle} />
              <button type="button" onClick={() => setIsSidebarOpen(true)} className="cc-icon-button md:hidden" aria-label="Open menu">
                <Menu size={18} />
              </button>
            </div>
          </header>

          <div className="cc-content">
            <section className={`cc-composer ${currentResult ? "is-compact" : ""}`}>
              {!currentResult && (
                <div className="cc-composer-intro">
                  <div className="cc-intro-kicker"><Sparkles size={15} />A question becomes a lesson</div>
                  <h2>What would you like to understand?</h2>
                  <p>Ask anything. ConceptCanvas will choose the clearest teaching structure, visual format, and narration flow.</p>
                </div>
              )}

              <div className="cc-prompt-box">
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => {
                    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") handleGenerate();
                  }}
                  placeholder="Ask a question, for example: Explain how inflation affects a household budget"
                  disabled={isLoading}
                  rows={currentResult ? 2 : 4}
                />

                <div className="cc-composer-actions">
                  <ModeSelector mode={mode} onModeChange={setMode} disabled={isLoading} />
                  <div className="flex items-center gap-2">
                    <LessonSettings
                      mode={mode}
                      audienceLevel={audienceLevel}
                      onAudienceLevelChange={setAudienceLevel}
                      explanationDepth={explanationDepth}
                      onExplanationDepthChange={setExplanationDepth}
                      requestedSceneCount={requestedSceneCount}
                      onRequestedSceneCountChange={setRequestedSceneCount}
                      groundingMode={groundingMode}
                      onGroundingModeChange={setGroundingMode}
                      disabled={isLoading}
                    />
                    <button type="button" onClick={handleGenerate} disabled={isLoading || !question.trim()} className="cc-primary-button">
                      <Send size={16} />
                      {isLoading ? "Creating" : "Create lesson"}
                    </button>
                  </div>
                </div>
              </div>

              {!currentResult && (
                <div className="cc-suggestion-row">
                  <span>Try</span>
                  <div className="grid flex-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
                    {examplePrompts.map((prompt) => (
                      <PromptCard key={prompt} prompt={prompt} onClick={handleExamplePromptClick} disabled={isLoading} />
                    ))}
                  </div>
                </div>
              )}
            </section>

            <ConversationPreview
              turns={currentTurns}
              activeTurnId={activeTurnId}
              onSelectTurn={handleSelectTurn}
              onClearConversation={handleClearConversation}
            />

            {isLoading && <LoadingSteps onCancel={handleCancelGeneration} />}

            {error && <div className="cc-alert is-error">{error}</div>}
            {saveWarning && <div className="cc-alert is-warning">{saveWarning}</div>}

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
              <div className="space-y-6">
                <VisualPanel
                  storyboard={currentResult.storyboard}
                  storyboardSource={currentResult.storyboardSource}
                  storyboardModelUsed={currentResult.storyboardModelUsed}
                  storyboardValidation={currentResult.storyboardValidation}
                  qualityReport={currentResult.qualityReport}
                  groundingReport={currentResult.groundingReport}
                />

                <CollapsibleExplanation
                  explanation={currentResult.explanation}
                  source={currentResult.source}
                  modelUsed={currentResult.modelUsed}
                  groundingReport={currentResult.groundingReport}
                />

                {currentResult.followUps?.length > 0 && (
                  <FollowUpChips followUps={currentResult.followUps} onFollowUpClick={handleFollowUpClick} disabled={isLoading} />
                )}
              </div>
            )}

            {isConceptExplanation && mode !== "visual" && (
              <div className="space-y-6">
                <ExplanationPanel
                  explanation={currentResult.explanation}
                  source={currentResult.source}
                  modelUsed={currentResult.modelUsed}
                  groundingReport={currentResult.groundingReport}
                />
                {currentResult.followUps?.length > 0 && (
                  <FollowUpChips followUps={currentResult.followUps} onFollowUpClick={handleFollowUpClick} disabled={isLoading} />
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
