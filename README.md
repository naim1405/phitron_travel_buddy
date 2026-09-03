# ✈️ Travel Buddy — LangChain Chatbot

A travel-assistant chatbot built with **LangChain** and **Streamlit**, powered by Google Gemini. It classifies the intent of each user message, routes it to the right specialist pipeline using **`RunnableBranch`**, answers full trip-planning requests by running three specialists concurrently with **`RunnableParallel`**, and validates intent classification with **Pydantic structured output** (`PydanticOutputParser` + `BaseModel`).

![Python](https://img.shields.io/badge/Python-3.14+-blue?logo=python&logoColor=white) ![LangChain](https://img.shields.io/badge/LangChain-latest-green?logo=langchain&logoColor=white) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white) ![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-4285F4)

---

## 📖 Project Overview

Instead of sending every question through one generic prompt, Travel Buddy first *classifies* the user's intent, then routes the question to the matching specialist pipeline:

- **Complete trip planning** → Spots + Food + Budget specialists run *in parallel*, and a merge chain synthesizes their outputs into one coherent answer
- **Places / Food / Budget** question → only the matching specialist chain runs
- **Anything else** → general fallback: travel-adjacent help (packing, visas, tips) or a polite decline of off-topic questions

The entire flow — classification → branching → parallel execution → synthesis — is composed from LangChain Runnables and delivered through a Streamlit chat interface.

### Features

- Intent classification validated against a Pydantic schema
- Intent-based routing via `RunnableBranch` (4 branches + default fallback)
- Concurrent specialist answers via `RunnableParallel` + a synthesis (merge) chain
- Every pipeline driven by reusable `PromptTemplate`s — nothing inline in `invoke()`
- Streamlit chat UI with session-persisted history and a sidebar of past messages
- API key loaded from `.env` — never hardcoded

---

## 🧠 How It Works

```
                        User Question (Streamlit chat input)
                                       │
                                       ▼
                  ┌──────────────────────────────────────┐
                  │  Classifier Chain                    │
                  │  PromptTemplate + format_instructions│
                  │  → ChatGoogleGenerativeAI            │
                  │  → PydanticOutputParser (Query)      │
                  └──────────────────────────────────────┘
                                       │  validated Query {query, type, history}
                                       ▼
                              RunnableBranch
                ┌────────────┬────────────┬────────────┬────────────┐
                │ type=ALL   │ type=FOOD  │ type=SPOTS │ type=BUDGET│  (default)
                ▼            ▼            ▼            ▼            ▼
          RunnableParallel  Food         Spots       Budget      General
          ┌────┬────┬────┐  Chain        Chain       Chain       Chain (fallback)
          │    │    │    │
       Spots Food Budget (3 specialist chains invoked simultaneously)
          │    │    │
          └────┴────┘
               ▼
        Merge/Synthesis Chain (one coherent final answer)
               │
               ▼
              Streamlit Chat UI
```

1. The user sends a message in the Streamlit chat box.
2. The **classifier chain** asks the LLM to classify the intent and return JSON matching the `Query` Pydantic schema; `PydanticOutputParser` validates it.
3. A `UserInput` (query + detected `QueryType` + chat history) is passed to the **`RunnableBranch`**.
4. The first matching condition fires:
   - `ALL` → the **`RunnableParallel`** chain runs the Spots, Food, and Budget specialists simultaneously, then the **merge chain** synthesizes them into one natural answer.
   - `SPOTS` / `FOOD` / `BUDGET` → only that specialist chain runs.
   - otherwise → the **general fallback**.
5. The final answer is appended to chat history and rendered in the UI.

---

## 🔀 RunnableBranch Implementation

Defined in [`chatbot.py`](chatbot.py) as `conditional_chain`. It selects a prompt pipeline based on the classified intent:

| # | Condition | Branch | Purpose |
|---|---|---|---|
| 1 | `type == QueryType.ALL` | `all_chain` (parallel + merge) | Full trip planning — needs all specialists |
| 2 | `type == QueryType.FOOD` | `food_chain` | Restaurants, local cuisine, dining |
| 3 | `type == QueryType.SPOTS` | `spot_chain` | Attractions, activities, sightseeing |
| 4 | `type == QueryType.BUDGET` | `budget_chain` | Trip costs, expense estimates, savings |
| — | *(default)* | `general_chain` | Travel misc (packing, visas) + polite decline of off-topic questions |

Each condition is a `(predicate, chain)` pair — the first predicate that returns `True` executes, and the final unnamed runnable is the **default branch**. The branch input is a `UserInput` object (not a raw string), so the specialist chains are wrapped in `RunnableLambda`s that adapt it into the `{"query", "history"}` dict each prompt expects.

---

## ⚡ RunnableParallel Implementation

Also in [`chatbot.py`](chatbot.py), as `all_tasks_parallel_chain`. When a request is classified as `ALL` (complete trip planning), the answer must cover places, food, and budget — so the chain fans out to all three specialists **concurrently** instead of running three LLM calls sequentially (see the fan-out in the diagram above).

- The parallel step also **passes `query` and `history` through unchanged**, because the merge prompt needs the *original* user request and conversation context.
- The **merge chain** (`all_recommendation_prompt_template`) doesn't just concatenate — it removes duplicates, resolves inconsistencies, and writes as a single knowledgeable travel assistant.
- Overall this is a *map-reduce* pipeline: **fan out → specialise → reduce into one answer**.

---

## 📦 Pydantic Structured Output Implementation

Defined in [`models.py`](models.py), wired up in [`chatbot.py`](chatbot.py).

- **`QueryType`** — a `str, Enum` constraining classification to exactly one of: `all`, `spots`, `food`, `budget`, `general`.
- **`Query(BaseModel)`** — the classifier's response schema:

| Field | Type | Meaning |
|---|---|---|
| `query` | `str` | The user's original message (copied verbatim — enforced by the prompt) |
| `type` | `QueryType` | Detected intent used for routing |
| `history` | `list[HumanMessage \| AIMessage]` | Conversation history (defaults to empty) |

- A **`PydanticOutputParser(pydantic_object=Query)`** is attached to the classifier chain: its `get_format_instructions()` are injected into the prompt via `partial_variables`, and the parser validates that the LLM output conforms to the schema before anything is routed downstream.
- Because `type` is an enum, invalid classifications fail validation instead of silently breaking the `RunnableBranch` conditions — the structured output is what makes the routing reliable.

---

## 📝 PromptTemplate Usage

All prompts live in [`prompts.py`](prompts.py) as reusable templates — nothing is written inline inside `invoke()`:

| Template | Used by | Dynamic variables |
|---|---|---|
| `task_classifier_prompt_template` | Classifier chain | `query`, `format_instructions` |
| `spot_recommendation_prompt_template` | Spots specialist | `query`, `history` |
| `food_recommendation_prompt_template` | Food specialist | `query`, `history` |
| `budget_recommendation_prompt_template` | Budget specialist | `query`, `history` |
| `all_recommendation_prompt_template` | Merge/synthesis chain | `query`, `history`, `spots`, `food`, `budget` |
| `general_prompt_template` | General fallback | `query`, `history` |

---

## 🗂️ Project Structure

```
phitron_travel_buddy/
│
├── app.py               # Streamlit UI (chat, history, sidebar)
├── chatbot.py           # Classifier, RunnableBranch, RunnableParallel, merge chain
├── models.py            # Pydantic schemas (Query, QueryType) & UserInput
├── prompts.py           # All PromptTemplates
├── pyproject.toml       # Project metadata & dependencies (uv)
├── uv.lock              # Locked dependency versions
├── .env.example         # Environment variable template (no real keys)
├── .gitignore
└── README.md
```

---

## ⚙️ Project Setup

**Prerequisite:** a Google AI Studio API key ([get one here](https://aistudio.google.com/app/apikey)). The project requires Python **≥ 3.14** as pinned in `pyproject.toml`.

### Using uv (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/naim1405/phitron_travel_buddy.git
cd phitron_travel_buddy

# 2. Install dependencies (uv creates the venv and fetches the required Python automatically)
uv sync

# 3. Configure your API key
cp .env.example .env          # Windows: copy .env.example .env
# then edit .env:
# GOOGLE_API_KEY=your_api_key_here

# 4. Run the app
uv run streamlit run app.py
```

### Using pip

pip reads the dependencies directly from `pyproject.toml` — but unlike uv, it will not download Python for you, so make sure Python ≥ 3.14 is already installed.

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

git clone https://github.com/naim1405/phitron_travel_buddy.git
cd phitron_travel_buddy
pip install -e .

cp .env.example .env          # add your GOOGLE_API_KEY

streamlit run app.py
```

> 🔒 `.env` is git-ignored — never commit real API keys.

---

## 💬 Example Queries

| Try asking | Routed as |
|---|---|
| "I'm going to Cox's Bazar for 3 days. What should I do, eat, and how much will it cost?" | `ALL` → parallel specialists + merge |
| "Best places to visit in Sylhet for a weekend trip?" | `SPOTS` |
| "Where can I find the best street food in Old Dhaka?" | `FOOD` |
| "How much would a 5-day trip to Sajek Valley cost for two people?" | `BUDGET` |
| "What should I pack for a trip to Japan?" | `GENERAL` |
