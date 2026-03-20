# Fabricated: AI Logic Engine (Backend)

This is the FastAPI backend and AI orchestration layer for **Fabricated**, a procedural true-crime mystery game. 

This API utilizes a custom 3-step generation pipeline with strict Pydantic schema validation to force a Large Language Model (Llama 3 70B via Groq) to design logically sound, hallucination-free murder mysteries on the fly.

The frontend is a separate Next.js React application that consumes this API to render a digital evidence board.

## The Problem Solved
LLMs are notoriously bad at generating playable logic puzzles in a single shot. They hallucinate clues, contradict their own timelines, and accidentally hand the player "silver bullet" instant wins.

This backend solves that through architectural constraints:
1. **The Core Truth:** The AI generates the foundational plot, the killer, and the specific alibi flaw first.
2. **The Cast:** The "Truth" is injected into the next prompt to generate an array of innocent suspects with airtight alibis, plus the killer.
3. **The Evidence:** The entire state is injected into a final prompt, forcing the AI to build circumstantial clues around the established timeline without breaking the logic.
4. **The Sanitizer:** Before the data ever reaches the frontend client, a Python utility strips the absolute truth, ensuring players cannot inspect the network tab to cheat.

## Tech Stack
* **Python 3**
* **FastAPI & Uvicorn:** High performance async web framework.
* **Pydantic V2:** Strict data validation and schema generation.
* **Groq API:** Utilizing `llama-3.3-70b-versatile` for lightning fast structured JSON outputs.
* **Supabase (PostgreSQL):** Persistent case storage and state management.
* **SlowAPI:** IP-based rate limiting to prevent API abuse in production.

## Current Endpoints
* `GET /` : Health check.
* `POST /api/cases/generate` : Takes `theme` and `difficulty`. Executes the 3-step pipeline, saves to Supabase, and returns the sanitized JSON case file. (Rate limited: 5/hour).
* `GET /api/cases/{case_id}` : Fetches a saved case from Supabase, strips spoilers via the sanitizer utility, and returns the safe JSON.
* `POST /api/cases/{case_id}/accuse` : Takes the player's theory and selected clues. Injects the absolute hidden truth and the player's evidence into a dynamic "AI Judge" prompt to evaluate their deduction logic. Returns a verdict and the actual solution. (Rate limited: 10/hour).

## Local Development Setup

1. Clone the repository and create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Environment Variables:
Create a `.env` file in the root directory and add your keys:
```text
GROQ_API_KEY=your_groq_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
```

4. Run the server:
```bash
uvicorn main:app --reload
```

## Future Scope
* **AI Interrogation Endpoints:** Chatting directly with suspects, bounded by the generated truth schema to prevent jailbreaking.
