import { useState } from "react";
import {
  Search,
  MapPin,
  Users,
  ShieldCheck,
  FileText,
  BrainCircuit,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Loader2,
  Sparkles,
  GitBranch,
  Scale,
  Activity,
  Database,
  Lightbulb,
} from "lucide-react";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const DEFAULT_QUESTION =
  "Analyze the proposed mixed-use corridor policy change. Determine what planning rules are relevant, which locations may be affected, which stakeholders may be impacted, and what evidence should be verified before implementation.";

function App() {
  const [question, setQuestion] = useState(DEFAULT_QUESTION);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyzePolicy = async () => {
    if (!question.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
        }),
      });

      if (!response.ok) {
        let message = `API request failed with status ${response.status}.`;

        try {
          const errorData = await response.json();

          if (errorData?.detail) {
            message = errorData.detail;
          }
        } catch {
          // Keep the default error message.
        }

        throw new Error(message);
      }

      const data = await response.json();

      setResult(data);
    } catch (err) {
      console.error(err);

      setError(
        err?.message ||
          "Unable to connect to CivicLens backend. Make sure the FastAPI server is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <BrainCircuit size={23} />
          </div>

          <div>
            <div className="brand-name">CivicLens</div>
            <div className="brand-tagline">
              Autonomous Policy Intelligence
            </div>
          </div>
        </div>

        <div className="top-status">
          <span className="status-dot" />
          Agent System Online
        </div>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="eyebrow">
            <Sparkles size={15} />
            AGENTIC MUNICIPAL INTELLIGENCE
          </div>

          <h1>
            See what a policy change
            <span> means for your city.</span>
          </h1>

          <p>
            CivicLens autonomously investigates municipal documents,
            connects policy changes to affected locations and stakeholders,
            verifies evidence, and produces an actionable impact report.
          </p>
        </section>

        <section className="analysis-card">
          <div className="card-heading">
            <div>
              <h2>Start an investigation</h2>
              <p>
                Describe the municipal policy question you want CivicLens to
                investigate.
              </p>
            </div>

            <div className="document-count">
              <FileText size={17} />
              5 evidence documents
            </div>
          </div>

          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask CivicLens to investigate a policy..."
          />

          <div className="action-row">
            <span className="hint">
              Evidence is retrieved locally before AI reasoning.
            </span>

            <button
              className="analyze-button"
              onClick={analyzePolicy}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="spin" size={18} />
                  Investigating...
                </>
              ) : (
                <>
                  <Search size={18} />
                  Analyze Policy
                  <ArrowRight size={17} />
                </>
              )}
            </button>
          </div>
        </section>

        {error && (
          <div className="error-box">
            <AlertTriangle size={20} />
            <span>{error}</span>
          </div>
        )}

        {loading && (
          <section className="agent-progress">
            <div className="progress-header">
              <div>
                <span className="eyebrow">
                  <BrainCircuit size={15} />
                  LIVE AGENT TRACE
                </span>

                <h2>CivicLens is investigating...</h2>
              </div>
            </div>

            <div className="trace-grid">
              <TraceItem
                icon={<BrainCircuit size={19} />}
                title="Plan"
                text="Creating investigation strategy"
                active
              />

              <TraceItem
                icon={<Search size={19} />}
                title="Retrieve"
                text="Searching municipal evidence"
                active
              />

              <TraceItem
                icon={<MapPin size={19} />}
                title="Locate"
                text="Mapping affected areas"
                active
              />

              <TraceItem
                icon={<Users size={19} />}
                title="Impact"
                text="Analyzing stakeholders"
                active
              />

              <TraceItem
                icon={<ShieldCheck size={19} />}
                title="Verify"
                text="Checking evidence"
                active
              />
            </div>
          </section>
        )}

        {result && !loading && (
          <>
            <section className="agent-progress completed">
              <div className="progress-header">
                <div>
                  <span className="eyebrow">
                    <CheckCircle2 size={15} />
                    INVESTIGATION COMPLETE
                  </span>

                  <h2>Agent execution trace</h2>
                </div>

                <span className="completed-badge">
                  {result.tools?.length || 0} tools executed
                </span>
              </div>

              <div className="trace-grid">
                <TraceItem
                  icon={<BrainCircuit size={19} />}
                  title="Plan"
                  text="Investigation strategy created"
                  done
                />

                <TraceItem
                  icon={<Search size={19} />}
                  title="Retrieve"
                  text="Municipal evidence retrieved"
                  done
                />

                <TraceItem
                  icon={<MapPin size={19} />}
                  title="Locate"
                  text="Affected areas investigated"
                  done
                />

                <TraceItem
                  icon={<Users size={19} />}
                  title="Impact"
                  text="Stakeholder impacts analyzed"
                  done
                />

                <TraceItem
                  icon={<ShieldCheck size={19} />}
                  title="Verify"
                  text="Claims checked against evidence"
                  done
                />
              </div>
            </section>

            <EvidenceGraph graph={result.evidence_graph} />

            <Report report={result.report} />
          </>
        )}
      </main>

      <footer>
        CivicLens • Evidence-backed municipal policy intelligence • Hackathon
        Prototype
      </footer>
    </div>
  );
}

function TraceItem({ icon, title, text, active, done }) {
  return (
    <div
      className={`trace-item ${active ? "active" : ""} ${
        done ? "done" : ""
      }`}
    >
      <div className="trace-icon">{icon}</div>

      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>

      {done && <CheckCircle2 className="trace-check" size={17} />}
    </div>
  );
}

/* =========================================================
   EVIDENCE GRAPH
   ========================================================= */

function EvidenceGraph({ graph }) {
  if (!graph?.nodes?.length) {
    return null;
  }

  const getNodes = (type) =>
    graph.nodes.filter((node) => node.type === type);

  const policyNodes = getNodes("policy");
  const ruleNodes = getNodes("rule");
  const locationNodes = getNodes("location");
  const stakeholderNodes = getNodes("stakeholder");
  const impactNodes = getNodes("impact");
  const evidenceNodes = getNodes("evidence");

  return (
    <section className="graph-section">
      <div className="graph-heading">
        <div>
          <span className="eyebrow">
            <GitBranch size={15} />
            EVIDENCE INVESTIGATION GRAPH
          </span>

          <h2>How CivicLens reached its findings</h2>

          <p>
            Every investigation follows an evidence chain from the policy
            change through applicable rules, affected places, stakeholders,
            potential impacts, and supporting sources.
          </p>
        </div>

        <div className="graph-stat">
          <GitBranch size={17} />
          <span>
            {graph.nodes.length} nodes • {graph.edges?.length || 0} links
          </span>
        </div>
      </div>

      <div className="graph-flow">
        <GraphStage
          icon={<Scale size={20} />}
          label="POLICY"
          title="Policy Change"
          nodes={policyNodes}
          type="policy"
        />

        <GraphConnector />

        <GraphStage
          icon={<FileText size={20} />}
          label="RULES"
          title="Relevant Rules"
          nodes={ruleNodes}
          type="rule"
        />

        <GraphConnector />

        <GraphStage
          icon={<MapPin size={20} />}
          label="LOCATION"
          title="Affected Areas"
          nodes={locationNodes}
          type="location"
        />

        <GraphConnector />

        <GraphStage
          icon={<Users size={20} />}
          label="PEOPLE"
          title="Stakeholders"
          nodes={stakeholderNodes}
          type="stakeholder"
        />

        <GraphConnector />

        <GraphStage
          icon={<Activity size={20} />}
          label="IMPACT"
          title="Potential Impact"
          nodes={impactNodes}
          type="impact"
        />

        <GraphConnector />

        <GraphStage
          icon={<Database size={20} />}
          label="EVIDENCE"
          title="Supporting Sources"
          nodes={evidenceNodes}
          type="evidence"
        />
      </div>

      <div className="graph-explanation">
        <div>
          <CheckCircle2 size={17} />
          <span>Evidence-backed relationship</span>
        </div>

        <div>
          <ShieldCheck size={17} />
          <span>Human verification remains required</span>
        </div>

        <div>
          <Lightbulb size={17} />
          <span>AI produces decision support, not legal decisions</span>
        </div>
      </div>
    </section>
  );
}

function GraphStage({ icon, label, title, nodes, type }) {
  return (
    <div className={`graph-stage graph-stage-${type}`}>
      <div className="graph-stage-header">
        <div className="graph-stage-icon">{icon}</div>

        <div>
          <span>{label}</span>
          <strong>{title}</strong>
        </div>
      </div>

      <div className="graph-nodes">
        {nodes.length === 0 ? (
          <div className="graph-empty">No linked evidence</div>
        ) : (
          nodes.map((node) => (
            <GraphNode key={node.id} node={node} type={type} />
          ))
        )}
      </div>
    </div>
  );
}

function GraphNode({ node, type }) {
  const description = node.description || "";

  return (
    <div className={`graph-node graph-node-${type}`}>
      <div className="graph-node-top">
        <span className="graph-node-label">
          {type === "rule" && "RULE"}
          {type === "location" && "AREA"}
          {type === "stakeholder" && "STAKEHOLDER"}
          {type === "impact" && "IMPACT"}
          {type === "evidence" && "SOURCE"}
          {type === "policy" && "CHANGE"}
        </span>

        <CheckCircle2 size={14} />
      </div>

      <strong>{node.label || "Untitled finding"}</strong>

      {description && (
        <p>
          {description.length > 180
            ? `${description.slice(0, 180)}...`
            : description}
        </p>
      )}

      {(node.document || node.page) && (
        <div className="graph-source">
          <FileText size={12} />

          <span>
            {node.document || "Source"}
            {node.page ? ` • Page ${node.page}` : ""}
          </span>
        </div>
      )}
    </div>
  );
}

function GraphConnector() {
  return (
    <div className="graph-connector">
      <ArrowRight size={18} />
    </div>
  );
}

/* =========================================================
   REPORT
   ========================================================= */

function Report({ report }) {
  const sections = parseReport(report);

  return (
    <section className="report-section">
      <div className="report-title-row">
        <div>
          <span className="eyebrow">
            <FileText size={15} />
            POLICY IMPACT REPORT
          </span>

          <h2>CivicLens Findings</h2>
        </div>

        <div className="confidence">
          <ShieldCheck size={18} />
          Evidence-backed analysis
        </div>
      </div>

      <div className="report-grid">
        <ReportCard
          icon={<FileText size={20} />}
          title="Executive Summary"
          content={sections["Executive Summary"]}
        />

        <ReportCard
          icon={<ArrowRight size={20} />}
          title="What Changed"
          content={sections["What Changed"]}
        />

        <ReportCard
          icon={<MapPin size={20} />}
          title="Affected Locations"
          content={sections["Affected Locations"]}
        />

        <ReportCard
          icon={<Users size={20} />}
          title="Affected Stakeholders"
          content={sections["Affected Stakeholders"]}
        />

        <ReportCard
          wide
          icon={<AlertTriangle size={20} />}
          title="Potential Impacts"
          content={sections["Potential Impacts"]}
        />

        <ReportCard
          wide
          icon={<ShieldCheck size={20} />}
          title="Confidence"
          content={sections["Confidence"]}
        />
      </div>

      <div className="evidence-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">
              <ShieldCheck size={15} />
              TRACEABLE EVIDENCE
            </span>

            <h3>Sources used by the agent</h3>
          </div>
        </div>

        <div className="evidence-content">
          {formatEvidence(sections["Evidence"])}
        </div>
      </div>

      <div className="bottom-grid">
        <div className="recommendation-panel">
          <div className="panel-heading">
            <h3>Recommended Actions</h3>
          </div>

          <div className="panel-content">
            {formatContent(sections["Recommended Actions"])}
          </div>
        </div>

        <div className="verification-panel">
          <div className="panel-heading">
            <h3>Verification Required</h3>
          </div>

          <div className="panel-content">
            {formatContent(sections["Verification Required"])}
          </div>
        </div>
      </div>
    </section>
  );
}

function ReportCard({ icon, title, content, wide }) {
  return (
    <div className={`report-card ${wide ? "wide" : ""}`}>
      <div className="report-card-icon">{icon}</div>

      <h3>{title}</h3>

      <div className="report-card-content">
        {formatContent(content)}
      </div>
    </div>
  );
}

/* =========================================================
   REPORT PARSING / FORMATTING
   ========================================================= */

function parseReport(report) {
  if (!report) return {};

  const sections = {};

  const parts = report.split(/^## /gm);

  parts.forEach((part) => {
    const lines = part.trim().split("\n");

    if (!lines.length) return;

    let title = lines[0].trim();

    title = title.replace(/^\d+\.\s*/, "");

    if (title && title !== "CivicLens Policy Impact Report") {
      sections[title] = lines.slice(1).join("\n").trim();
    }
  });

  return sections;
}

function formatContent(content = "") {
  if (!content) {
    return <span className="muted">No information returned.</span>;
  }

  const lines = content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return lines.map((line, index) => {
    const clean = line.replace(/^\d+\.\s*/, "");

    const formatted = clean
      .replace(/\*\*/g, "")
      .replace(/^[-*]\s*/, "");

    return (
      <div
        className={
          /^\d+\.\s/.test(clean) ? "numbered-item" : undefined
        }
        key={index}
      >
        {formatted}
      </div>
    );
  });
}

function formatEvidence(content = "") {
  if (!content) {
    return <span className="muted">No evidence returned.</span>;
  }

  const lines = content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return lines.map((line, index) => {
    const clean = line
      .replace(/^[-*]\s*/, "")
      .replace(/\*\*/g, "");

    return (
      <div className="evidence-line" key={index}>
        <CheckCircle2 size={16} />
        <span>{clean}</span>
      </div>
    );
  });
}

export default App;