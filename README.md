# ConceptCanvas

I built ConceptCanvas to explore a better way of learning complex topics.

Most AI tools return a long text answer. ConceptCanvas turns a question into a structured explanation, a scene-by-scene visual lesson, synchronized narration, and playback controls so the learner can follow one idea at a time.

## What I developed

- A topic-independent lesson generation pipeline
- Structured explanations for different learner levels and depths
- Exact scene-count handling and canonical scene numbering
- A typed visual grammar for nodes, edges, groups, annotations, and narration targets
- Reusable renderers for flows, hierarchies, stacks, timelines, cycles, comparisons, concept maps, formulas, and state transitions
- Narration synchronized with the currently highlighted visual elements
- Validation and repair for malformed AI-generated lessons
- Honest AI, hybrid, and deterministic fallback states
- Claim-level grounding and lesson quality checks
- Conversation history for local development
- A responsive visual-learning workspace
- CI, staging configuration, and deployment setup

The visual-planning layer is based on the structure of a concept, not a fixed list of topics. For example, a networking question may use a sequence diagram, recursion may use a call stack, a historical topic may use a timeline, and a biological process may use a cycle or flow.

## How it works

```text
Question
  ↓
Lesson requirements
  ↓
Structured explanation
  ↓
Visual planning
  ↓
Typed scenes and narration
  ↓
Validation and repair
  ↓
Interactive lesson player
```

The backend treats the model response as a candidate lesson. It validates scene count, numbering, visual references, narration alignment, and quality before the lesson reaches the frontend.

## Tech stack

### Frontend

- React
- Vite
- Tailwind CSS
- SVG-based typed visual renderers
- Browser speech synthesis

### Backend

- FastAPI
- Pydantic
- Groq or Gemini
- SQLite for local development
- Provider-independent grounding and quality evaluation

### Deployment and testing

- GitHub Actions
- Render
- Vercel
- Python unit tests
- Frontend visual-model tests
- Cross-domain quality benchmark

## Project structure

```text
ConceptCanvas
├── client
│   ├── src
│   ├── tests
│   └── vercel.json
├── server
│   ├── app
│   ├── tests
│   ├── scripts
│   ├── benchmarks
│   ├── evaluation
│   └── grounding
├── .github
│   └── workflows
└── render.yaml
```
