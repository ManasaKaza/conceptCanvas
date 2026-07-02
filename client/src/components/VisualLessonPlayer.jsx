import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
    Gauge,
    Pause,
    Play,
    RotateCcw,
    SkipBack,
    SkipForward,
    Square,
    Volume2,
    VolumeX,
} from "lucide-react";
import { formatElementName } from "../utils/sceneUtils";

const ACTION_DURATIONS = {
    slow: 2300,
    normal: 1600,
    fast: 1000,
};

function isSpeechSupported() {
    return typeof window !== "undefined" && "speechSynthesis" in window;
}

function stopSpeech() {
    if (isSpeechSupported()) {
        window.speechSynthesis.cancel();
    }
}

function pauseSpeech() {
    if (isSpeechSupported()) {
        window.speechSynthesis.pause();
    }
}

function resumeSpeech() {
    if (isSpeechSupported()) {
        window.speechSynthesis.resume();
    }
}

function speakText(text, onEnd) {
    if (!isSpeechSupported() || !text?.trim()) {
        onEnd?.();
        return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;

    utterance.onend = () => {
        onEnd?.();
    };

    utterance.onerror = () => {
        onEnd?.();
    };

    window.speechSynthesis.speak(utterance);
}

function collectSceneElements(scene) {
    const visualElements = Array.isArray(scene?.visualElements)
        ? scene.visualElements
        : [];

    const actionElements = Array.isArray(scene?.actions)
        ? scene.actions.flatMap((action) => [
            action.target,
            action.fromElement,
            action.toElement,
        ])
        : [];

    return [...new Set([...visualElements, ...actionElements].filter(Boolean))];
}

function getActions(scene) {
    if (Array.isArray(scene?.actions) && scene.actions.length > 0) {
        return scene.actions;
    }

    const elements = collectSceneElements(scene);

    return elements.map((element) => ({
        type: "show",
        target: element,
        label: `Showing ${formatElementName(element)}`,
    }));
}

function getActionLabel(action) {
    if (!action) return "Preparing visual explanation...";

    if (action.label) return action.label;

    if (action.type === "show" && action.target) {
        return `Showing ${formatElementName(action.target)}`;
    }

    if (action.type === "connect" && action.fromElement && action.toElement) {
        return `${formatElementName(action.fromElement)} connects to ${formatElementName(
            action.toElement,
        )}`;
    }

    if (action.type === "highlight" && action.target) {
        return `Focus on ${formatElementName(action.target)}`;
    }

    if (action.type === "move" && action.fromElement && action.toElement) {
        return `${formatElementName(action.fromElement)} moves to ${formatElementName(
            action.toElement,
        )}`;
    }

    return "Understanding this step...";
}

function getActionSpeech(_scene, action) {
    return getActionLabel(action);
}

function getPosition(index, total) {
    const layouts = {
        1: [{ x: 50, y: 45 }],
        2: [
            { x: 30, y: 45 },
            { x: 70, y: 45 },
        ],
        3: [
            { x: 22, y: 45 },
            { x: 50, y: 28 },
            { x: 78, y: 45 },
        ],
        4: [
            { x: 18, y: 35 },
            { x: 42, y: 62 },
            { x: 66, y: 35 },
            { x: 84, y: 62 },
        ],
        5: [
            { x: 12, y: 45 },
            { x: 32, y: 28 },
            { x: 52, y: 45 },
            { x: 72, y: 28 },
            { x: 88, y: 45 },
        ],
    };

    const fallback = [
        { x: 12, y: 45 },
        { x: 28, y: 28 },
        { x: 44, y: 60 },
        { x: 60, y: 28 },
        { x: 76, y: 60 },
        { x: 90, y: 42 },
    ];

    const selectedLayout = layouts[total] || fallback;

    return selectedLayout[index] || fallback[index % fallback.length];
}

function getVisibleElements(actions, activeActionIndex) {
    const visibleElements = new Set();

    actions.slice(0, activeActionIndex + 1).forEach((action) => {
        if (action.type === "show" && action.target) {
            visibleElements.add(action.target);
        }

        if (action.type === "highlight" && action.target) {
            visibleElements.add(action.target);
        }

        if (
            (action.type === "connect" || action.type === "move") &&
            action.fromElement
        ) {
            visibleElements.add(action.fromElement);
        }

        if (
            (action.type === "connect" || action.type === "move") &&
            action.toElement
        ) {
            visibleElements.add(action.toElement);
        }
    });

    return visibleElements;
}

function getActiveTarget(action) {
    return action?.target || action?.toElement || action?.fromElement || null;
}

function ArrowLayer({ actions, activeActionIndex, positions }) {
    const completedActions = actions.slice(0, activeActionIndex + 1);

    return (
        <svg className="pointer-events-none absolute inset-0 h-full w-full">
            <defs>
                <marker
                    id="arrow-head"
                    markerWidth="8"
                    markerHeight="8"
                    refX="7"
                    refY="3"
                    orient="auto"
                >
                    <path d="M0,0 L0,6 L7,3 z" fill="#4f46e5" />
                </marker>
            </defs>

            {completedActions.map((action, index) => {
                if (action.type !== "connect" && action.type !== "move") {
                    return null;
                }

                const fromPosition = positions[action.fromElement];
                const toPosition = positions[action.toElement];

                if (!fromPosition || !toPosition) {
                    return null;
                }

                const isActive = index === activeActionIndex;

                return (
                    <line
                        key={`${action.fromElement}-${action.toElement}-${index}`}
                        x1={`${fromPosition.x}%`}
                        y1={`${fromPosition.y}%`}
                        x2={`${toPosition.x}%`}
                        y2={`${toPosition.y}%`}
                        stroke={isActive ? "#4f46e5" : "#93c5fd"}
                        strokeWidth={isActive ? "4" : "3"}
                        strokeDasharray={action.type === "move" ? "8 6" : "0"}
                        markerEnd="url(#arrow-head)"
                        className="transition-all duration-500"
                    />
                );
            })}
        </svg>
    );
}

function VisualCanvas({ scene, activeActionIndex }) {
    const elements = collectSceneElements(scene);
    const actions = getActions(scene);
    const activeAction = actions[activeActionIndex];
    const visibleElements = getVisibleElements(actions, activeActionIndex);
    const activeTarget = getActiveTarget(activeAction);

    const positions = elements.reduce((acc, element, index) => {
        acc[element] = getPosition(index, elements.length);
        return acc;
    }, {});

    return (
        <div className="relative min-h-[420px] overflow-hidden rounded-[2rem] border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-blue-50">
            <ArrowLayer
                actions={actions}
                activeActionIndex={activeActionIndex}
                positions={positions}
            />

            {elements.map((element) => {
                const position = positions[element];
                const isVisible = visibleElements.has(element);
                const isActive = activeTarget === element;

                return (
                    <div
                        key={element}
                        className={`absolute min-w-32 max-w-48 -translate-x-1/2 -translate-y-1/2 rounded-2xl border bg-white px-4 py-3 text-center text-sm font-bold shadow-sm transition-all duration-700 ${isVisible ? "scale-100 opacity-100" : "scale-90 opacity-0"
                            } ${isActive
                                ? "border-indigo-400 text-indigo-950 ring-8 ring-indigo-100"
                                : "border-gray-100 text-gray-700"
                            }`}
                        style={{
                            left: `${position.x}%`,
                            top: `${position.y}%`,
                        }}
                    >
                        {formatElementName(element)}
                    </div>
                );
            })}

            <div className="absolute bottom-4 left-1/2 w-[92%] -translate-x-1/2 rounded-2xl border border-white/10 bg-slate-950/90 px-5 py-4 text-center shadow-xl backdrop-blur">
                <p className="text-xs font-bold uppercase tracking-wide text-indigo-300">
                    Live subtitle
                </p>

                <p className="mt-1 text-base font-semibold leading-7 text-white">
                    {getActionLabel(activeAction)}
                </p>

                <p className="mt-1 text-xs text-slate-300">
                    Step {activeActionIndex + 1} of {actions.length}
                </p>
            </div>
        </div>
    );
}

function PlayerButton({ onClick, children, variant = "secondary", title }) {
    const variantClasses =
        variant === "primary"
            ? "bg-indigo-700 text-white hover:bg-indigo-600"
            : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50";

    return (
        <button
            onClick={onClick}
            title={title}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${variantClasses}`}
        >
            {children}
        </button>
    );
}

function VisualLessonPlayer({ scenes }) {
    const safeScenes = useMemo(() => {
        return Array.isArray(scenes) ? scenes : [];
    }, [scenes]);

    const [sceneIndex, setSceneIndex] = useState(0);
    const [activeActionIndex, setActiveActionIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [hasCompleted, setHasCompleted] = useState(false);
    const [playbackSpeed, setPlaybackSpeed] = useState("normal");
    const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);

    const spokenActionRef = useRef(null);

    const currentScene = safeScenes[sceneIndex];
    const currentActions = getActions(currentScene);
    const currentAction = currentActions[activeActionIndex];

    const moveToNextStep = useCallback(() => {
        if (activeActionIndex < currentActions.length - 1) {
            setActiveActionIndex((prev) => prev + 1);
            return;
        }

        if (sceneIndex < safeScenes.length - 1) {
            stopSpeech();
            spokenActionRef.current = null;
            setSceneIndex((prev) => prev + 1);
            setActiveActionIndex(0);
            return;
        }

        stopSpeech();
        spokenActionRef.current = null;
        setIsPlaying(false);
        setHasCompleted(true);
    }, [
        activeActionIndex,
        currentActions.length,
        sceneIndex,
        safeScenes.length,
    ]);

    const totalSteps = safeScenes.reduce(
        (count, scene) => count + getActions(scene).length,
        0,
    );

    const completedStepsBeforeScene = safeScenes
        .slice(0, sceneIndex)
        .reduce((count, scene) => count + getActions(scene).length, 0);

    const completedSteps = completedStepsBeforeScene + activeActionIndex + 1;

    const progressPercentage =
        totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

    useEffect(() => {
        return () => {
            stopSpeech();
        };
    }, []);

    useEffect(() => {
        if (!isPlaying || !currentScene) {
            return undefined;
        }

        if (isVoiceEnabled && isSpeechSupported()) {
            return undefined;
        }

        const timerId = setTimeout(() => {
            moveToNextStep();
        }, ACTION_DURATIONS[playbackSpeed]);

        return () => clearTimeout(timerId);
    }, [
        isPlaying,
        currentScene,
        playbackSpeed,
        isVoiceEnabled,
        moveToNextStep,
    ]);

    useEffect(() => {
        if (!isPlaying || !currentScene || !currentAction || !isVoiceEnabled) {
            return undefined;
        }

        if (!isSpeechSupported()) {
            return undefined;
        }

        const actionKey = `${sceneIndex}-${activeActionIndex}`;

        if (spokenActionRef.current === actionKey) {
            return undefined;
        }

        spokenActionRef.current = actionKey;

        const speechText = getActionSpeech(currentScene, currentAction);

        speakText(speechText, () => {
            moveToNextStep();
        });

        return undefined;
    }, [
        isPlaying,
        currentScene,
        currentAction,
        sceneIndex,
        activeActionIndex,
        isVoiceEnabled,
        moveToNextStep,
    ]);

    function handlePlay() {
        if (safeScenes.length === 0) return;

        if (hasCompleted) {
            stopSpeech();
            spokenActionRef.current = null;
            setSceneIndex(0);
            setActiveActionIndex(0);
            setHasCompleted(false);
        } else {
            resumeSpeech();
        }

        setIsPlaying(true);
    }

    function handlePause() {
        pauseSpeech();
        setIsPlaying(false);
    }

    function handleReplay() {
        stopSpeech();
        spokenActionRef.current = null;
        setSceneIndex(0);
        setActiveActionIndex(0);
        setHasCompleted(false);
        setIsPlaying(true);
    }

    function handleStop() {
        stopSpeech();
        spokenActionRef.current = null;
        setIsPlaying(false);
        setHasCompleted(false);
        setSceneIndex(0);
        setActiveActionIndex(0);
    }

    function handlePrevious() {
        stopSpeech();
        spokenActionRef.current = null;
        setIsPlaying(false);
        setHasCompleted(false);

        if (activeActionIndex > 0) {
            setActiveActionIndex((prev) => prev - 1);
            return;
        }

        if (sceneIndex > 0) {
            const previousSceneIndex = sceneIndex - 1;
            const previousActions = getActions(safeScenes[previousSceneIndex]);

            setSceneIndex(previousSceneIndex);
            setActiveActionIndex(previousActions.length - 1);
        }
    }

    function handleNext() {
        stopSpeech();
        spokenActionRef.current = null;
        setIsPlaying(false);
        setHasCompleted(false);

        if (activeActionIndex < currentActions.length - 1) {
            setActiveActionIndex((prev) => prev + 1);
            return;
        }

        if (sceneIndex < safeScenes.length - 1) {
            setSceneIndex((prev) => prev + 1);
            setActiveActionIndex(0);
            return;
        }

        setHasCompleted(true);
    }

    if (safeScenes.length === 0) {
        return (
            <div className="rounded-3xl bg-white p-5 text-sm text-gray-500 shadow-sm">
                No visual lesson available yet.
            </div>
        );
    }

    return (
        <div className="rounded-[2rem] border border-gray-100 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-indigo-700">
                        Visual Lesson
                    </p>

                    <h3 className="mt-1 text-xl font-bold text-gray-950">
                        {currentScene.title}
                    </h3>

                    <p className="mt-1 text-sm leading-6 text-gray-500">
                        Scene overview: {currentScene.narration}
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    <button
                        onClick={() => {
                            setIsVoiceEnabled((current) => {
                                if (current) {
                                    stopSpeech();
                                }

                                return !current;
                            });
                        }}
                        title={isVoiceEnabled ? "Turn voice off" : "Turn voice on"}
                        className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${isVoiceEnabled
                            ? "bg-green-50 text-green-800"
                            : "bg-gray-100 text-gray-600"
                            }`}
                    >
                        {isVoiceEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
                        {isVoiceEnabled ? "Voice on" : "Voice off"}
                    </button>

                    <div className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-700">
                        <Gauge size={14} />

                        <select
                            value={playbackSpeed}
                            onChange={(event) => setPlaybackSpeed(event.target.value)}
                            className="bg-transparent outline-none"
                        >
                            <option value="slow">Slow</option>
                            <option value="normal">Normal</option>
                            <option value="fast">Fast</option>
                        </select>
                    </div>

                    <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-800">
                        Scene {sceneIndex + 1} of {safeScenes.length}
                    </span>
                </div>
            </div>

            <div className="mb-4">
                <div className="mb-1 flex justify-between text-xs text-gray-500">
                    <span>Animated lesson progress</span>
                    <span>{progressPercentage}%</span>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                    <div
                        className="h-full rounded-full bg-indigo-700 transition-all duration-500"
                        style={{ width: `${progressPercentage}%` }}
                    />
                </div>
            </div>

            <VisualCanvas
                scene={currentScene}
                activeActionIndex={activeActionIndex}
            />

            <div className="mt-5 flex flex-wrap items-center justify-center gap-2 border-t border-gray-100 pt-4">
                <PlayerButton onClick={handlePrevious} title="Previous step">
                    <SkipBack size={16} />
                    Previous
                </PlayerButton>

                {isPlaying ? (
                    <PlayerButton onClick={handlePause} variant="primary" title="Pause lesson">
                        <Pause size={16} />
                        Pause
                    </PlayerButton>
                ) : (
                    <PlayerButton onClick={handlePlay} variant="primary" title="Play lesson">
                        <Play size={16} />
                        {hasCompleted ? "Play again" : "Play lesson"}
                    </PlayerButton>
                )}

                <PlayerButton onClick={handleNext} title="Next step">
                    <SkipForward size={16} />
                    Next
                </PlayerButton>

                <PlayerButton onClick={handleReplay} title="Replay lesson">
                    <RotateCcw size={16} />
                    Replay
                </PlayerButton>

                <PlayerButton onClick={handleStop} title="Stop lesson">
                    <Square size={16} />
                    Stop
                </PlayerButton>
            </div>
        </div>
    );
}

export default VisualLessonPlayer;