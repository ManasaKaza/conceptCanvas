import { useEffect, useMemo, useRef, useState } from "react";
import { getSubtitleText } from "../utils/sceneUtils";

function isSpeechSupported() {
    return typeof window !== "undefined" && "speechSynthesis" in window;
}

function choosePreferredVoice(voices) {
    return (
        voices.find((voice) => voice.name.includes("Google US English")) ||
        voices.find((voice) => voice.lang?.startsWith("en-US")) ||
        voices.find((voice) => voice.lang?.startsWith("en")) ||
        null
    );
}

function getInitialPreferredVoice() {
    if (!isSpeechSupported()) {
        return null;
    }

    return choosePreferredVoice(window.speechSynthesis.getVoices());
}

function VoiceNarration({ scenes, onSceneChange, onNarrationEnd }) {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [hasCompleted, setHasCompleted] = useState(false);
    const [preferredVoice, setPreferredVoice] = useState(() =>
        getInitialPreferredVoice(),
    );
    const [currentSceneIndex, setCurrentSceneIndex] = useState(null);
    const [activeSubtitleIndex, setActiveSubtitleIndex] = useState(0);
    const [statusMessage, setStatusMessage] = useState("");

    const stoppedRef = useRef(false);
    const subtitleTimerRef = useRef(null);
    const isSupported = isSpeechSupported();

    const safeScenes = useMemo(() => {
        return Array.isArray(scenes) ? scenes : [];
    }, [scenes]);

    useEffect(() => {
        if (!isSupported) {
            return undefined;
        }

        function handleVoicesChanged() {
            const voices = window.speechSynthesis.getVoices();
            setPreferredVoice(choosePreferredVoice(voices));
        }

        window.speechSynthesis.onvoiceschanged = handleVoicesChanged;

        return () => {
            clearSubtitleTimer();
            window.speechSynthesis.cancel();
            window.speechSynthesis.onvoiceschanged = null;
        };
    }, [isSupported]);

    function clearSubtitleTimer() {
        if (subtitleTimerRef.current) {
            clearInterval(subtitleTimerRef.current);
            subtitleTimerRef.current = null;
        }
    }

    function startSubtitleHighlight(scene) {
        clearSubtitleTimer();

        const subtitleLines = Array.isArray(scene?.subtitleLines)
            ? scene.subtitleLines
            : [];

        if (subtitleLines.length === 0) {
            setActiveSubtitleIndex(0);
            return;
        }

        setActiveSubtitleIndex(0);

        if (subtitleLines.length === 1) {
            return;
        }

        let currentIndex = 0;

        subtitleTimerRef.current = setInterval(() => {
            currentIndex += 1;

            if (currentIndex >= subtitleLines.length) {
                clearSubtitleTimer();
                return;
            }

            setActiveSubtitleIndex(currentIndex);
        }, 1800);
    }

    function speakScene(index) {
        if (!isSupported || stoppedRef.current) return;

        const scene = safeScenes[index];

        if (!scene) {
            clearSubtitleTimer();
            setActiveSubtitleIndex(0);
            setIsSpeaking(false);
            setIsPaused(false);
            setHasCompleted(true);
            setCurrentSceneIndex(null);
            setStatusMessage("Narration completed. You can replay it from the start.");
            onSceneChange?.(null);
            onNarrationEnd?.();
            return;
        }

        setCurrentSceneIndex(index);
        setActiveSubtitleIndex(0);
        onSceneChange?.(index);
        setStatusMessage(`Narrating scene ${index + 1} of ${safeScenes.length}`);
        startSubtitleHighlight(scene);

        const utterance = new SpeechSynthesisUtterance(
            scene.narration || scene.title,
        );

        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        utterance.rate = 0.95;
        utterance.pitch = 1;

        utterance.onend = () => {
            if (!stoppedRef.current) {
                speakScene(index + 1);
            }
        };

        utterance.onerror = () => {
            clearSubtitleTimer();
            setActiveSubtitleIndex(0);
            setIsSpeaking(false);
            setIsPaused(false);
            setCurrentSceneIndex(null);
            setStatusMessage("Narration failed. You can still read the subtitles.");
            onSceneChange?.(null);
            onNarrationEnd?.();
        };

        window.speechSynthesis.speak(utterance);
    }

    function handlePlay() {
        if (!isSupported) {
            setStatusMessage("Voice narration is not supported in this browser.");
            return;
        }

        if (safeScenes.length === 0) {
            setStatusMessage("No scenes available for narration.");
            return;
        }

        clearSubtitleTimer();
        window.speechSynthesis.cancel();
        stoppedRef.current = false;
        setIsSpeaking(true);
        setIsPaused(false);
        setHasCompleted(false);
        setCurrentSceneIndex(null);
        setActiveSubtitleIndex(0);
        setStatusMessage("Starting narration...");
        speakScene(0);
    }

    function handleReplay() {
        if (!isSupported) {
            setStatusMessage("Voice narration is not supported in this browser.");
            return;
        }

        if (safeScenes.length === 0) {
            setStatusMessage("No scenes available for narration.");
            return;
        }

        clearSubtitleTimer();
        window.speechSynthesis.cancel();
        stoppedRef.current = false;
        setIsSpeaking(true);
        setIsPaused(false);
        setHasCompleted(false);
        setCurrentSceneIndex(null);
        setActiveSubtitleIndex(0);
        setStatusMessage("Replaying from the start...");
        speakScene(0);
    }

    function handlePause() {
        if (!isSupported || !isSpeaking || isPaused) return;

        window.speechSynthesis.pause();
        clearSubtitleTimer();
        setIsPaused(true);
        setStatusMessage("Narration paused.");
    }

    function handleResume() {
        if (!isSupported || !isSpeaking || !isPaused) return;

        window.speechSynthesis.resume();
        setIsPaused(false);

        if (currentSceneIndex !== null) {
            startSubtitleHighlight(safeScenes[currentSceneIndex]);
            setStatusMessage(
                `Narrating scene ${currentSceneIndex + 1} of ${safeScenes.length}`,
            );
        } else {
            setStatusMessage("Narration resumed.");
        }
    }

    function handleStop() {
        if (!isSupported) return;

        stoppedRef.current = true;
        clearSubtitleTimer();
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
        setIsPaused(false);
        setHasCompleted(false);
        setActiveSubtitleIndex(0);
        setCurrentSceneIndex(null);
        setStatusMessage("Narration stopped.");
        onSceneChange?.(null);
        onNarrationEnd?.();
    }

    const currentScene =
        currentSceneIndex !== null ? safeScenes[currentSceneIndex] : null;

    const progressPercentage =
        currentSceneIndex !== null && safeScenes.length > 0
            ? Math.round(((currentSceneIndex + 1) / safeScenes.length) * 100)
            : 0;

    return (
        <div className="mb-5 rounded-2xl border border-indigo-100 bg-indigo-50/50 p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
                        Voice Narration
                    </p>

                    <p className="mt-1 text-sm text-gray-600">
                        Play the storyboard narration scene by scene.
                    </p>

                    <p className="mt-1 text-xs text-gray-500">
                        {preferredVoice
                            ? `Voice: ${preferredVoice.name}`
                            : "Voice: browser default"}
                    </p>
                </div>

                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={handlePlay}
                        disabled={isSpeaking && !isPaused}
                        className={`rounded-xl px-4 py-2 text-sm font-semibold text-white ${isSpeaking && !isPaused
                                ? "cursor-not-allowed bg-gray-400"
                                : "bg-indigo-700 hover:bg-indigo-600"
                            }`}
                    >
                        {isSpeaking ? "Playing..." : "Play"}
                    </button>

                    <button
                        onClick={handleReplay}
                        disabled={!hasCompleted && !isSpeaking}
                        className={`rounded-xl px-4 py-2 text-sm font-semibold ${!hasCompleted && !isSpeaking
                                ? "cursor-not-allowed bg-gray-100 text-gray-400"
                                : "border border-indigo-200 bg-white text-indigo-700 hover:bg-indigo-50"
                            }`}
                    >
                        Replay
                    </button>

                    <button
                        onClick={handlePause}
                        disabled={!isSpeaking || isPaused}
                        className={`rounded-xl px-4 py-2 text-sm font-semibold ${!isSpeaking || isPaused
                                ? "cursor-not-allowed bg-gray-100 text-gray-400"
                                : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                            }`}
                    >
                        Pause
                    </button>

                    <button
                        onClick={handleResume}
                        disabled={!isSpeaking || !isPaused}
                        className={`rounded-xl px-4 py-2 text-sm font-semibold ${!isSpeaking || !isPaused
                                ? "cursor-not-allowed bg-gray-100 text-gray-400"
                                : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                            }`}
                    >
                        Resume
                    </button>

                    <button
                        onClick={handleStop}
                        disabled={!isSpeaking}
                        className={`rounded-xl px-4 py-2 text-sm font-semibold ${!isSpeaking
                                ? "cursor-not-allowed bg-gray-100 text-gray-400"
                                : "border border-red-200 bg-white text-red-700 hover:bg-red-50"
                            }`}
                    >
                        Stop
                    </button>
                </div>
            </div>

            {!isSupported && (
                <div className="mt-4 rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                    Voice narration is not supported in this browser. You can still read
                    the subtitles.
                </div>
            )}

            {statusMessage && (
                <div className="mt-4">
                    <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-medium text-indigo-800">
                            {statusMessage}
                        </p>

                        {currentSceneIndex !== null && (
                            <span className="text-xs font-semibold text-indigo-700">
                                Scene {currentSceneIndex + 1} of {safeScenes.length}
                            </span>
                        )}
                    </div>

                    {currentSceneIndex !== null && (
                        <div className="mt-3">
                            <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
                                <span>Progress</span>
                                <span>{progressPercentage}%</span>
                            </div>

                            <div className="h-2 overflow-hidden rounded-full bg-indigo-100">
                                <div
                                    className="h-full rounded-full bg-indigo-700 transition-all duration-500"
                                    style={{ width: `${progressPercentage}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>
            )}

            {currentScene && (
                <div className="mt-4 rounded-xl bg-white p-4 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Current subtitles
                    </p>

                    <div className="mt-3 space-y-2">
                        {(Array.isArray(currentScene.subtitleLines)
                            ? currentScene.subtitleLines
                            : [getSubtitleText(currentScene)]
                        ).map((line, index) => (
                            <p
                                key={`${line}-${index}`}
                                className={`rounded-xl px-3 py-2 text-sm leading-6 transition-all ${index === activeSubtitleIndex
                                        ? "bg-indigo-100 font-semibold text-indigo-900"
                                        : "bg-gray-50 text-gray-500"
                                    }`}
                            >
                                {line}
                            </p>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default VoiceNarration;