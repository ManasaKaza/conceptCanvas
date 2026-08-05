import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Gauge, Pause, Play, RotateCcw, SkipBack, SkipForward, Square, Volume2, VolumeX } from "lucide-react";
import { getSceneTimeline } from "../utils/sceneUtils";
import LegacyVisualCanvas from "./visual/LegacyVisualCanvas";
import TypedVisualCanvas from "./visual/TypedVisualCanvas";
import { isTypedVisual } from "./visual/visualModel";
import { buildSourceIndex } from "../utils/grounding";

const SPEECH_RATES = { slow: 0.78, normal: 0.95, fast: 1.15 };
const DURATION_FACTORS = { slow: 1.28, normal: 1, fast: 0.72 };

function isSpeechSupported() {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}
function stopSpeech() { if (isSpeechSupported()) window.speechSynthesis.cancel(); }
function pauseSpeech() { if (isSpeechSupported()) window.speechSynthesis.pause(); }
function resumeSpeech() { if (isSpeechSupported()) window.speechSynthesis.resume(); }
function speakText(text, onEnd, rate = 0.95) {
  if (!isSpeechSupported() || !text?.trim()) { onEnd?.(); return; }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = rate;
  utterance.pitch = 1;
  utterance.onend = () => onEnd?.();
  utterance.onerror = () => onEnd?.();
  window.speechSynthesis.speak(utterance);
}
function getTimedDuration(segment, speed) {
  const base = Number(segment?.estimatedDurationMs) || 3500;
  return Math.max(1000, Math.min(14000, base * DURATION_FACTORS[speed]));
}

function PlayerIconButton({ onClick, children, title, disabled = false, primary = false }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      disabled={disabled}
      className={`cc-player-button ${primary ? "is-primary" : ""}`}
    >
      {children}
    </button>
  );
}

function VisualLessonPlayer({ scenes, groundingReport }) {
  const safeScenes = useMemo(() => Array.isArray(scenes) ? scenes : [], [scenes]);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [activeSegmentIndex, setActiveSegmentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasCompleted, setHasCompleted] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState("normal");
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const spokenSegmentRef = useRef(null);

  const currentScene = safeScenes[sceneIndex];
  const currentTimeline = useMemo(() => getSceneTimeline(currentScene), [currentScene]);
  const currentSegment = currentTimeline[activeSegmentIndex];
  const sourceIndex = useMemo(() => buildSourceIndex(groundingReport), [groundingReport]);
  const currentSources = (currentSegment?.sourceIds || []).map((sourceId) => sourceIndex.get(sourceId)).filter(Boolean);

  const moveToNextMoment = useCallback(() => {
    if (activeSegmentIndex < currentTimeline.length - 1) {
      setActiveSegmentIndex((value) => value + 1);
    } else if (sceneIndex < safeScenes.length - 1) {
      stopSpeech();
      spokenSegmentRef.current = null;
      setSceneIndex((value) => value + 1);
      setActiveSegmentIndex(0);
    } else {
      stopSpeech();
      spokenSegmentRef.current = null;
      setIsPlaying(false);
      setHasCompleted(true);
    }
  }, [activeSegmentIndex, currentTimeline.length, sceneIndex, safeScenes.length]);

  const totalMoments = useMemo(() => safeScenes.reduce((total, scene) => total + getSceneTimeline(scene).length, 0), [safeScenes]);
  const momentsBeforeScene = safeScenes.slice(0, sceneIndex).reduce((total, scene) => total + getSceneTimeline(scene).length, 0);
  const progressPercentage = totalMoments ? Math.round(((momentsBeforeScene + activeSegmentIndex + 1) / totalMoments) * 100) : 0;

  useEffect(() => () => stopSpeech(), []);
  useEffect(() => {
    if (!isPlaying || !currentScene || !currentSegment || (isVoiceEnabled && isSpeechSupported())) return undefined;
    const timer = window.setTimeout(moveToNextMoment, getTimedDuration(currentSegment, playbackSpeed));
    return () => window.clearTimeout(timer);
  }, [isPlaying, currentScene, currentSegment, playbackSpeed, isVoiceEnabled, moveToNextMoment]);
  useEffect(() => {
    if (!isPlaying || !currentScene || !currentSegment || !isVoiceEnabled || !isSpeechSupported()) return undefined;
    const key = `${sceneIndex}-${activeSegmentIndex}`;
    if (spokenSegmentRef.current === key) return undefined;
    spokenSegmentRef.current = key;
    speakText(currentSegment.spokenText, moveToNextMoment, SPEECH_RATES[playbackSpeed]);
    return undefined;
  }, [isPlaying, currentScene, currentSegment, sceneIndex, activeSegmentIndex, isVoiceEnabled, playbackSpeed, moveToNextMoment]);

  function pauseAndResetSpeech() { stopSpeech(); spokenSegmentRef.current = null; setIsPlaying(false); }
  function handlePlay() {
    if (!safeScenes.length) return;
    if (hasCompleted) {
      stopSpeech();
      spokenSegmentRef.current = null;
      setSceneIndex(0);
      setActiveSegmentIndex(0);
      setHasCompleted(false);
    } else resumeSpeech();
    setIsPlaying(true);
  }
  function handlePause() { pauseSpeech(); setIsPlaying(false); }
  function handleReplay() { stopSpeech(); spokenSegmentRef.current = null; setSceneIndex(0); setActiveSegmentIndex(0); setHasCompleted(false); setIsPlaying(true); }
  function handleStop() { stopSpeech(); spokenSegmentRef.current = null; setIsPlaying(false); setHasCompleted(false); setSceneIndex(0); setActiveSegmentIndex(0); }
  function handlePrevious() {
    pauseAndResetSpeech(); setHasCompleted(false);
    if (activeSegmentIndex > 0) setActiveSegmentIndex((value) => value - 1);
    else if (sceneIndex > 0) {
      const previous = sceneIndex - 1;
      setSceneIndex(previous);
      setActiveSegmentIndex(Math.max(0, getSceneTimeline(safeScenes[previous]).length - 1));
    }
  }
  function handleNext() {
    pauseAndResetSpeech(); setHasCompleted(false);
    if (activeSegmentIndex < currentTimeline.length - 1) setActiveSegmentIndex((value) => value + 1);
    else if (sceneIndex < safeScenes.length - 1) { setSceneIndex((value) => value + 1); setActiveSegmentIndex(0); }
    else setHasCompleted(true);
  }
  function selectScene(index) { pauseAndResetSpeech(); setHasCompleted(false); setSceneIndex(index); setActiveSegmentIndex(0); }

  if (!safeScenes.length) return <div className="cc-empty-canvas">No visual lesson is available.</div>;

  const typedScene = isTypedVisual(currentScene);
  const isAtStart = sceneIndex === 0 && activeSegmentIndex === 0;
  const isAtEnd = sceneIndex === safeScenes.length - 1 && activeSegmentIndex === currentTimeline.length - 1;

  return (
    <div className="cc-lesson-player">
      <nav className="cc-scene-rail" aria-label="Lesson scenes">
        <p className="cc-eyebrow">Scenes</p>
        <div className="mt-3 space-y-1.5">
          {safeScenes.map((scene, index) => (
            <button
              type="button"
              key={scene.id || index}
              onClick={() => selectScene(index)}
              aria-current={index === sceneIndex ? "step" : undefined}
              className={`cc-scene-button ${index === sceneIndex ? "is-active" : ""}`}
            >
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{scene.title}</strong>
            </button>
          ))}
        </div>
      </nav>

      <div className="cc-stage">
        <header className="cc-stage-header">
          <div className="min-w-0">
            <p className="cc-eyebrow">Scene {sceneIndex + 1} of {safeScenes.length}</p>
            <h3>{currentScene.title}</h3>
            <p>{typedScene ? currentScene.visual.diagramType.replaceAll("_", " ") : "Legacy visual"}</p>
          </div>

          <div className="cc-stage-options">
            <button
              type="button"
              onClick={() => setIsVoiceEnabled((value) => { stopSpeech(); spokenSegmentRef.current = null; return !value; })}
              className="cc-icon-button"
              aria-label={isVoiceEnabled ? "Turn narration off" : "Turn narration on"}
            >
              {isVoiceEnabled ? <Volume2 size={17} /> : <VolumeX size={17} />}
            </button>
            <label className="cc-speed-control">
              <Gauge size={15} />
              <span className="sr-only">Playback speed</span>
              <select value={playbackSpeed} onChange={(event) => { stopSpeech(); spokenSegmentRef.current = null; setPlaybackSpeed(event.target.value); }}>
                <option value="slow">0.8×</option>
                <option value="normal">1×</option>
                <option value="fast">1.2×</option>
              </select>
            </label>
          </div>
        </header>

        <div className="cc-progress-track" aria-label={`Lesson ${progressPercentage}% complete`}>
          <span style={{ width: `${progressPercentage}%` }} />
        </div>

        <div className="cc-visual-canvas">
          {typedScene ? (
            <TypedVisualCanvas scene={currentScene} timeline={currentTimeline} activeSegmentIndex={activeSegmentIndex} />
          ) : (
            <LegacyVisualCanvas scene={currentScene} activeMomentIndex={activeSegmentIndex} subtitle={currentSegment?.subtitleText || currentScene.narration} />
          )}
        </div>

        <div className="cc-narration-strip" aria-live="polite">
          <div className="cc-narration-index">{String(activeSegmentIndex + 1).padStart(2, "0")}</div>
          <div className="min-w-0 flex-1">
            <p>{currentSegment?.spokenText || currentScene.narration}</p>
            {currentSegment?.subtitleText && currentSegment.subtitleText !== currentSegment.spokenText && (
              <small>{currentSegment.subtitleText}</small>
            )}
            {currentSources.length > 0 && (
              <div className="cc-moment-sources">
                {currentSources.map((source) => (
                  <a key={source.sourceId} href={source.url} target="_blank" rel="noreferrer" title={`${source.title} · ${source.publisher}`}>
                    [{source.number}] {source.publisher}
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>

        <footer className="cc-player-controls">
          <div className="flex items-center gap-1">
            <PlayerIconButton onClick={handlePrevious} title="Previous moment" disabled={isAtStart}><SkipBack size={17} /></PlayerIconButton>
            {isPlaying ? (
              <PlayerIconButton onClick={handlePause} title="Pause lesson" primary><Pause size={18} />Pause</PlayerIconButton>
            ) : (
              <PlayerIconButton onClick={handlePlay} title="Play lesson" primary><Play size={18} />{hasCompleted ? "Play again" : "Play"}</PlayerIconButton>
            )}
            <PlayerIconButton onClick={handleNext} title="Next moment" disabled={isAtEnd && hasCompleted}><SkipForward size={17} /></PlayerIconButton>
          </div>
          <div className="flex items-center gap-1">
            <PlayerIconButton onClick={handleReplay} title="Replay lesson"><RotateCcw size={16} /></PlayerIconButton>
            <PlayerIconButton onClick={handleStop} title="Stop lesson"><Square size={15} /></PlayerIconButton>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default VisualLessonPlayer;
