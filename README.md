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

## Run locally

### Backend

```powershell
cd server

Copy-Item .env.example .env

py -3.13 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"

.\.venv\Scripts\python.exe -m uvicorn app.main:app `
  --reload `
  --host 127.0.0.1 `
  --port 8000
```

The API will run at `http://127.0.0.1:8000`.

### Frontend

```powershell
cd client

Copy-Item .env.example .env

npm ci
npm run lint
npm run test:visual
npm run build
npm run dev
```

The frontend will run at `http://localhost:5173`.

## Environment

The repository contains example environment files only.

Create local files from:

```text
server/.env.example
client/.env.example
```

API keys and local environment files must not be committed.

ConceptCanvas can run with deterministic generation for local checks. To use an AI provider, configure a Groq or Gemini key in `server/.env`.

## Verification

The current release includes:

- Backend contract, planner, repair, grounding, evaluation, and deployment-safety tests
- Frontend visual-model and narration-timeline tests
- A cross-domain benchmark covering computing, mathematics, science, social science, humanities, business, and everyday learning
- GitHub Actions checks for tests, linting, benchmarking, and production build

## Deployment

The frontend is configured for Vercel and the backend is configured for Render.

The deployed frontend uses:

```text
VITE_API_BASE_URL=<Render backend URL>
```

The backend uses an environment-controlled list of allowed frontend origins.

## Current status

ConceptCanvas is ready for local use and a protected staging or portfolio deployment.

Before a full public multi-user release, the product still needs authentication, user-owned lesson history, PostgreSQL, production-grade rate limiting, usage quotas, and broader source retrieval.

## Live demo

The live link will be added here after deployment.

## Developer

Developed by Manasa Kaza.
