# CivicLens

### Evidence-backed AI investigation for municipal policy

> **CivicLens turns fragmented municipal documents into an evidence-backed map of what changed, who is affected, why they are affected, and what action should happen next.**

CivicLens is an agentic civic-policy intelligence prototype built for the **Civic Policy & Municipal Transparency** problem space.

It takes a natural-language policy question and turns it into a structured investigation across municipal documents. Instead of producing a standalone AI-generated summary, CivicLens connects **policy changes → planning rules → locations → stakeholders → impacts → evidence → verification** and presents the result as an explainable investigation.

---

## Problem

Municipal policy information is often fragmented across:

- Zoning regulations
- Approval orders
- Council resolutions
- Policy proposals
- Planning reports
- Other municipal documents

Understanding the impact of a policy change therefore requires more than searching for a keyword.

A useful investigation needs to answer:

1. What changed?
2. Which planning rules are relevant?
3. Which locations may be affected?
4. Which stakeholders may be impacted?
5. What are the potential impacts?
6. What evidence supports those conclusions?
7. Which claims still need verification?
8. What action or follow-up should happen next?

CivicLens is designed to automate this investigation workflow.

---

## Solution

CivicLens combines local document retrieval, specialized investigation tools, evidence verification, and AI reasoning into one workflow.

```text
                    POLICY QUESTION
                           │
                           ▼
                    ┌─────────────┐
                    │ Agent Plan  │
                    └──────┬──────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        Policy Search   Locations     Impact
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    Claim Verification
                           │
                           ▼
                    Evidence Package
                           │
                           ▼
                    Evidence Graph
                           │
                           ▼
                  AI Reasoning / Report
```

The core investigation chain is:

```text
CHANGE
  ↓
LAW / RULE
  ↓
LOCATION
  ↓
STAKEHOLDER
  ↓
IMPACT
  ↓
EVIDENCE
  ↓
ACTION
```

---

# How CivicLens Works

## 1. Ask a policy question

The user provides a natural-language question describing the policy or planning issue they want investigated.

Example:

> Analyze the proposed mixed-use corridor policy change. Determine what planning rules are relevant, which locations may be affected, which stakeholders may be impacted, and what evidence should be verified before implementation.

---

## 2. Create an investigation plan

CivicLens decomposes the investigation into specialized steps instead of asking a single AI call to answer everything.

The current workflow uses:

```text
Plan
  ↓
Retrieve
  ↓
Locate
  ↓
Impact
  ↓
Verify
```

---

## 3. Search policy documents

The `search_policy_documents` tool searches the local municipal document corpus for relevant regulations, orders, proposals and reports.

It returns source-level evidence including:

- Document
- Page
- Relevant passage
- Retrieval score
- Evidence confidence

---

## 4. Find affected locations

The `find_affected_locations` tool identifies locations, zones or areas connected to the retrieved evidence.

This helps answer:

> **Where does this policy matter?**

---

## 5. Analyze impact

The `analyze_impact` tool connects the policy and affected locations to potential stakeholder impacts.

Potential stakeholder categories include:

- Residents
- Businesses
- Developers
- Planners
- Local authorities
- Other affected community groups

This helps answer:

> **Who is affected, and how?**

---

## 6. Verify claims

The `verify_claim` tool checks important claims against retrieved evidence.

CivicLens distinguishes stronger evidence from weaker evidence and identifies claims that require additional verification.

This is important because policy analysis should not treat an AI-generated statement as automatically authoritative.

---

## 7. Build the evidence graph

CivicLens builds a structured evidence graph connecting the investigation components.

```text
Policy Change
      │
      ├──────────► Planning Rule
      │                  │
      │                  └────► Evidence
      │
      ├──────────► Location
      │                  │
      │                  └────► Evidence
      │
      └──────────► Stakeholder
                         │
                         └────► Impact
                                  │
                                  └────► Evidence
```

The graph provides an explainable path from a policy change to the evidence supporting the resulting analysis.

---

# Retrieval Architecture

CivicLens currently uses a fully local TF-IDF retrieval pipeline.

```text
PDF Documents
      ↓
PyMuPDF Extraction
      ↓
Text Normalization
      ↓
Paragraph / Sentence-aware Chunking
      ↓
TF-IDF Index
      ↓
Local Evidence Retrieval
      ↓
Agent Investigation Tools
      ↓
Evidence Package
```

### Why local TF-IDF?

The prototype deliberately avoids unnecessary external vector-database or embedding dependencies.

Local TF-IDF retrieval provides:

- Deterministic retrieval
- Fast local searches
- No embedding API dependency
- Lower API usage
- Simple deployment requirements
- Transparent retrieval behaviour

Gemini is used for the final reasoning/report generation after the evidence package has been assembled.

---

# Agent Architecture

CivicLens currently contains four primary investigation tools:

| Tool | Purpose |
|---|---|
| `search_policy_documents` | Retrieve relevant policy and planning evidence |
| `find_affected_locations` | Identify potentially affected locations |
| `analyze_impact` | Analyze stakeholders and potential impacts |
| `verify_claim` | Check important claims against evidence |

The workflow is orchestrated by the CivicLens agent and exposed through the FastAPI backend.

---

# Evidence-First Design

A central design principle of CivicLens is:

> **The evidence should support the reasoning — not the other way around.**

A conventional AI assistant may produce a policy summary directly from a model.

CivicLens instead follows:

```text
Documents
   ↓
Evidence
   ↓
Investigation
   ↓
Verification
   ↓
AI Reasoning
   ↓
Report
```

This makes the output easier to inspect and challenge.

The goal is not to claim that the AI is always correct.

The goal is to make it clear **why a conclusion was reached and what evidence should be checked before acting on it.**

---

# Features

### 🔎 Evidence Library

Upload additional PDF documents into the municipal document corpus.

Uploaded documents are:

1. Validated as PDFs
2. Added to the document corpus
3. Indexed locally
4. Made available to future investigations

### 🤖 Agent Investigation Trace

The UI displays the investigation workflow so users can see the major reasoning stages rather than only receiving a final answer.

### 📚 Source Evidence

Retrieved evidence is presented with source document and page information.

### 🕸️ Evidence Graph

Visualizes relationships between:

- Policy changes
- Rules
- Locations
- Stakeholders
- Impacts
- Evidence

### 📊 Evidence Confidence

Investigation results expose retrieval/evidence confidence to help distinguish stronger findings from weaker evidence.

### 🗂️ Investigation History

Completed investigations can be stored locally and reopened later.

This allows users to revisit:

- The original question
- Investigation steps
- Evidence
- Graph relationships
- Final report

Runtime investigation data is intentionally excluded from version control.

### 📝 Structured Report

The final result is presented as an evidence-backed policy investigation rather than an unstructured chatbot response.

---

# Technology Stack

## Frontend

- React
- Vite
- JavaScript
- Lucide React
- Custom CSS

## Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

## Document Processing

- PyMuPDF

## Retrieval

- scikit-learn
- TF-IDF
- NumPy

## AI Reasoning

- Google Gemini API

## Persistence

- Local JSON-based investigation storage

---

# Project Structure

```text
civiclens/
│
├── backend/
│   ├── agent.py
│   ├── tools.py
│   ├── rag.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   └── package-lock.json
│
├── data/
│   └── documents/
│       ├── 01_zonal_regulations.pdf
│       ├── 02_approval_orders_2015.pdf
│       ├── 03_policy_change.pdf
│       ├── 04_council_resolution.pdf
│       └── 05_planning_impact_report.pdf
│
├── .gitignore
└── README.md
```

---

# Demo Document Corpus

The prototype includes five demonstration documents:

1. `01_zonal_regulations.pdf`
2. `02_approval_orders_2015.pdf`
3. `03_policy_change.pdf`
4. `04_council_resolution.pdf`
5. `05_planning_impact_report.pdf`

### Demo data note

The corpus intentionally combines source material based on real BDA documents with synthetic demonstration documents created to model a municipal policy-change scenario.

The synthetic documents are **not presented as official government records**.

---

# Installation

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- A Google Gemini API key

## 1. Clone the repository

```bash
git clone https://github.com/MaTejeshwar/civiclens.git
cd civiclens
```

## 2. Set up the backend

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

## 3. Configure the Gemini API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

Do not commit the `.env` file.

## 4. Build the local document index

From the project root:

```bash
python -m backend.rag
```

This extracts the PDF corpus and creates the local TF-IDF index.

## 5. Start the backend

```bash
python -m uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## 6. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

# Running an Investigation

1. Start the backend.
2. Start the frontend.
3. Open CivicLens in the browser.
4. Enter a municipal policy question.
5. Start the analysis.
6. Observe the agent investigation trace.
7. Inspect retrieved evidence.
8. Review affected locations and stakeholders.
9. Inspect claim verification.
10. Explore the evidence graph.
11. Read the final evidence-backed report.

---

# Example Investigation

### Question

```text
Analyze the proposed mixed-use corridor policy change.
Determine what planning rules are relevant, which locations
may be affected, which stakeholders may be impacted, and what
evidence should be verified before implementation.
```

### Expected investigation flow

```text
Policy Question
      ↓
Agent Plan
      ↓
Policy Retrieval
      ↓
Affected Locations
      ↓
Impact Analysis
      ↓
Claim Verification
      ↓
Evidence Graph
      ↓
Final Report
```

---

# API Overview

The backend exposes endpoints for:

| Endpoint | Purpose |
|---|---|
| `GET /` | API information |
| `GET /health` | Health check |
| `GET /api/documents` | Document/index information |
| `POST /api/documents/upload` | Upload a PDF document |
| `GET /api/investigations` | List saved investigations |
| `GET /api/investigations/{id}` | Reopen a saved investigation |
| `POST /api/analyze` | Run a policy investigation |

---

# Responsible Use

CivicLens is a research and hackathon prototype.

It should not be treated as:

- Legal advice
- A replacement for professional planning review
- A replacement for government decision-making
- Proof that a policy interpretation is legally correct

Important policy claims should be reviewed against authoritative source documents and, where necessary, by qualified planning or legal professionals before real-world implementation.

---

# Current Limitations

The current prototype intentionally prioritizes a working evidence-driven workflow over production-scale infrastructure.

Current limitations include:

- Local TF-IDF retrieval rather than semantic/hybrid retrieval
- Small demonstration document corpus
- Synthetic documents in the demo scenario
- Local JSON persistence
- No authentication or multi-user access
- No live municipal data ingestion
- No production GIS integration
- AI-generated analysis still requires human review

---

# Future Scope

Potential future improvements include:

- Hybrid semantic + keyword retrieval
- Larger municipal document collections
- GIS/map-based impact visualization
- Automated monitoring for new policy documents
- Multilingual citizen-facing reports
- Automated public-comment drafting
- Human review and approval workflows
- Source freshness and provenance tracking
- Cross-city policy comparison
- Structured citizen response campaigns

---

# Why CivicLens?

CivicLens focuses on a key weakness of AI-assisted policy analysis:

> **An answer without an evidence chain is difficult to trust.**

CivicLens therefore makes the investigation itself visible.

```text
CHANGE
  ↓
LAW / RULE
  ↓
LOCATION
  ↓
STAKEHOLDER
  ↓
IMPACT
  ↓
EVIDENCE
  ↓
ACTION
```

### CivicLens turns municipal policy analysis from document searching into evidence-driven investigation.

---

## Hackathon Context

Built for the **Bit N Build – Around the World 2026 Hackathon** under the **Civic Policy & Municipal Transparency** problem space.

The prototype demonstrates how agentic AI can ingest municipal policy documents, retrieve relevant evidence, reason across multiple entities, verify claims, and produce localized policy-impact intelligence.

---

## License

This project is intended as a hackathon prototype.
