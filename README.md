# ConceptCanvas

ConceptCanvas is an AI-powered visual learning tutor that turns concept-based questions into structured text explanations, visual storyboard scenes, narration, subtitles, and follow-up learning threads.

Instead of only giving a long text answer, ConceptCanvas helps learners understand concepts step by step through text, visuals, and audio.

---

## Problem

Many learners struggle to understand concepts clearly because existing learning content is often:

* too long
* too text-heavy
* scattered across videos, articles, notes, and AI chats
* not focused on the learner’s exact question
* difficult to revise quickly before interviews or assessments

ConceptCanvas solves this by generating focused explanations and visual learning flows on demand.

---

## Features

* Ask any concept-based question
* Choose between Text Only and Text + Visual modes
* Generate structured explanations with:

  * simple meaning
  * deep explanation
  * step-by-step breakdown
  * analogy
  * real-world example
  * common confusions
  * interview angle
  * key takeaways
* Generate visual storyboard scenes
* Watch animated visual lessons
* Voice narration support
* Live subtitles
* Playback controls: play, pause, replay, next, previous, stop
* Dark and light theme support
* Follow-up questions
* Threaded learning conversations
* SQLite-based conversation history

---

## Tech Stack

### Frontend

* React
* Vite
* JavaScript
* Tailwind CSS
* Lucide React icons
* Browser Speech Synthesis API

### Backend

* FastAPI
* Python
* Pydantic
* SQLite
* Groq LLM API

### AI

* Groq LLM for explanation generation
* Groq LLM for visual storyboard generation
* Rule-based fallback storyboard generation
* Storyboard validation and normalization

---

## Architecture

```text
Learner
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
Question Classifier
  ↓
Explanation Service
  ↓
Groq LLM
  ↓
Storyboard Service
  ↓
Validation and Fallback Logic
  ↓
SQLite Conversation Store
  ↓
Text Explanation + Visual Lesson Player
```

## Why ConceptCanvas

ConceptCanvas is designed for learners who want quick, focused, and visual explanations instead of switching between long videos, dense notes, and scattered online resources.

It combines structured AI explanations with visual storytelling, narration, subtitles, and threaded follow-up learning.
