import { useEffect, useState } from "react";
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

/* =========================================================
   APP
   ========================================================= */

function App() {
  const [question, setQuestion] = useState(DEFAULT_QUESTION);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [documents, setDocuments] = useState([]);
  const [investigations, setInvestigations] = useState([]);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  /* =========================================================
     LOAD DOCUMENTS
     ========================================================= */

  const loadDocuments = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/documents`
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load evidence documents."
        );
      }

      const data = await response.json();

      setDocuments(
        Array.isArray(data.documents)
          ? data.documents
          : []
      );
    } catch (err) {
      console.error(
        "Document inventory error:",
        err
      );
    }
  };

  /* =========================================================
     LOAD INVESTIGATION HISTORY
     ========================================================= */

  const loadInvestigations = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/investigations`
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load investigation history."
        );
      }

      const data = await response.json();

      setInvestigations(
        Array.isArray(data.investigations)
          ? data.investigations
          : []
      );
    } catch (err) {
      console.error(
        "Investigation history error:",
        err
      );
    }
  };

  /* =========================================================
     INITIAL LOAD
     ========================================================= */

  useEffect(() => {
    loadDocuments();
    loadInvestigations();
  }, []);

  /* =========================================================
     ANALYZE POLICY
     ========================================================= */

  const analyzePolicy = async () => {
    if (!question.trim()) {
      setError(
        "Please enter a policy question to investigate."
      );
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/api/analyze`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: question.trim(),
          }),
        }
      );

      if (!response.ok) {
        let message = `API request failed with status ${response.status}.`;

        try {
          const errorData =
            await response.json();

          if (errorData?.detail) {
            message = errorData.detail;
          }
        } catch {
          // Keep default error message.
        }

        throw new Error(message);
      }

      const data = await response.json();

      setResult(
        normalizeResult(data)
      );

      await loadInvestigations();
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

  /* =========================================================
     UPLOAD DOCUMENT
     ========================================================= */

  const uploadDocument = async () => {
    if (!selectedFile) {
      return;
    }

    if (
      selectedFile.type !==
        "application/pdf" &&
      !selectedFile.name
        .toLowerCase()
        .endsWith(".pdf")
    ) {
      setUploadMessage(
        "Please select a PDF document."
      );
      return;
    }

    setUploading(true);
    setUploadMessage("");
    setError("");

    try {
      const formData =
        new FormData();

      formData.append(
        "file",
        selectedFile
      );

      const response =
        await fetch(
          `${API_URL}/api/documents/upload`,
          {
            method: "POST",
            body: formData,
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Document upload failed."
        );
      }

      const filename =
        data?.document?.filename ||
        selectedFile.name;

      const documentCount =
        data?.index?.documents ??
        data?.index?.document_count ??
        null;

      setUploadMessage(
        documentCount !== null
          ? `✓ ${filename} indexed successfully. ${documentCount} evidence documents available.`
          : `✓ ${filename} indexed successfully and added to the evidence library.`
      );

      setSelectedFile(null);

      await loadDocuments();
    } catch (err) {
      console.error(err);

      setUploadMessage(
        err?.message ||
          "Unable to upload document."
      );
    } finally {
      setUploading(false);
    }
  };

  /* =========================================================
     OPEN SAVED INVESTIGATION
     ========================================================= */

  const openInvestigation = async (
    investigationId
  ) => {
    try {
      setError("");

      const response =
        await fetch(
          `${API_URL}/api/investigations/${investigationId}`
        );

      if (!response.ok) {
        throw new Error(
          "Unable to open investigation."
        );
      }

      const data =
        await response.json();

      const normalized =
        normalizeResult(data);

      setResult({
        ...normalized,
        investigation_id:
          data?.id ||
          data?.investigation_id ||
          normalized.investigation_id ||
          investigationId,
      });

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } catch (err) {
      console.error(err);

      setError(
        err?.message ||
          "Unable to open saved investigation."
      );
    }
  };

  return (
    <div className="app-shell">
      {/* =====================================================
          TOP BAR
          ===================================================== */}

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <BrainCircuit size={23} />
          </div>

          <div>
            <div className="brand-name">
              CivicLens
            </div>

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
        {/* ===================================================
            HERO
            =================================================== */}

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
            CivicLens autonomously investigates
            municipal documents, connects policy
            changes to affected locations and
            stakeholders, verifies evidence, and
            produces an actionable impact report.
          </p>
        </section>

        {/* ===================================================
            ANALYSIS CARD
            =================================================== */}

        <section className="analysis-card">
          <div className="card-heading">
            <div>
              <h2>
                Start an investigation
              </h2>

              <p>
                Describe the municipal policy
                question you want CivicLens to
                investigate.
              </p>
            </div>

            <div className="document-count">
              <FileText size={17} />

              {documents.length} evidence documents
            </div>
          </div>

          <textarea
            value={question}
            onChange={(e) =>
              setQuestion(e.target.value)
            }
            placeholder="Ask CivicLens to investigate a policy..."
            disabled={loading}
          />

          <div className="action-row">
            <span className="hint">
              Evidence is retrieved locally before
              AI reasoning.
            </span>

            <button
              className="analyze-button"
              onClick={analyzePolicy}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2
                    className="spin"
                    size={18}
                  />
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

        {/* ===================================================
            WORKSPACE TOOLS
            =================================================== */}

        <section className="workspace-tools">
          {/* =================================================
              EVIDENCE LIBRARY
              ================================================= */}

          <div className="workspace-tool upload-tool">
            <div className="workspace-tool-heading">
              <div className="workspace-tool-icon">
                <Database size={19} />
              </div>

              <div>
                <h3>
                  Evidence Library
                </h3>

                <p>
                  Add municipal PDFs to
                  CivicLens's local evidence
                  index.
                </p>
              </div>
            </div>

            <div className="upload-row">
              <label className="file-picker">
                <FileText size={17} />

                <span>
                  {selectedFile
                    ? selectedFile.name
                    : "Choose a PDF document"}
                </span>

                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={(e) =>
                    setSelectedFile(
                      e.target.files?.[0] ||
                        null
                    )
                  }
                />
              </label>

              <button
                className="secondary-action"
                onClick={
                  uploadDocument
                }
                disabled={
                  !selectedFile ||
                  uploading
                }
              >
                {uploading ? (
                  <>
                    <Loader2
                      className="spin"
                      size={17}
                    />
                    Indexing...
                  </>
                ) : (
                  <>
                    <Database size={17} />
                    Upload & Index
                  </>
                )}
              </button>
            </div>

            {uploadMessage && (
              <div className="upload-message">
                {uploadMessage}
              </div>
            )}

            <div className="document-list">
              {documents.length === 0 ? (
                <div className="history-empty">
                  No evidence documents are currently
                  indexed.
                </div>
              ) : (
                documents.map(
                  (document) => (
                    <div
                      className="document-item"
                      key={
                        document.filename
                      }
                    >
                      <FileText size={15} />

                      <div>
                        <strong>
                          {
                            document.filename
                          }
                        </strong>

                        <span>
                          {document.pages ||
                            0}{" "}
                          page
                          {document.pages ===
                          1
                            ? ""
                            : "s"}{" "}
                          •{" "}
                          {document.chunks ||
                            0}{" "}
                          evidence chunks
                        </span>
                      </div>

                      <CheckCircle2 size={16} />
                    </div>
                  )
                )
              )}
            </div>
          </div>

          {/* =================================================
              INVESTIGATION HISTORY
              ================================================= */}

          <div className="workspace-tool history-tool">
            <div className="workspace-tool-heading">
              <div className="workspace-tool-icon">
                <Activity size={19} />
              </div>

              <div>
                <h3>
                  Investigation History
                </h3>

                <p>
                  Reopen previous
                  evidence-backed
                  investigations.
                </p>
              </div>
            </div>

            {investigations.length ===
            0 ? (
              <div className="history-empty">
                No saved investigations yet.
                Run an analysis to create
                one.
              </div>
            ) : (
              <div className="investigation-list">
                {investigations
                  .slice(0, 5)
                  .map(
                    (
                      investigation
                    ) => (
                      <div
                        className="investigation-item"
                        key={
                          investigation.id
                        }
                      >
                        <div className="investigation-info">
                          <strong>
                            {getInvestigationQuestion(
                              investigation
                            )}
                          </strong>

                          <span>
                            {getInvestigationToolCount(
                              investigation
                            )}{" "}
                            tools •{" "}
                            {getInvestigationNodeCount(
                              investigation
                            )}{" "}
                            evidence nodes
                          </span>
                        </div>

                        <button
                          className="open-investigation"
                          onClick={() =>
                            openInvestigation(
                              investigation.id
                            )
                          }
                        >
                          Open
                          <ArrowRight
                            size={15}
                          />
                        </button>
                      </div>
                    )
                  )}
              </div>
            )}
          </div>
        </section>

        {/* ===================================================
            ERROR
            =================================================== */}

        {error && (
          <div className="error-box">
            <AlertTriangle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* ===================================================
            LIVE AGENT TRACE
            =================================================== */}

        {loading && (
          <section className="agent-progress">
            <div className="progress-header">
              <div>
                <span className="eyebrow">
                  <BrainCircuit size={15} />
                  LIVE AGENT TRACE
                </span>

                <h2>
                  CivicLens is investigating...
                </h2>
              </div>

              <span className="completed-badge">
                4 tools
              </span>
            </div>

            <div className="trace-grid">
              <TraceItem
                icon={
                  <BrainCircuit size={19} />
                }
                title="Plan"
                text="Building investigation strategy"
                detail="Preparing evidence workflow"
                active
              />

              <TraceItem
                icon={
                  <Search size={19} />
                }
                title="Retrieve"
                text="Searching municipal evidence"
                detail="Local TF-IDF retrieval"
                active
              />

              <TraceItem
                icon={
                  <MapPin size={19} />
                }
                title="Locate"
                text="Finding affected areas"
                detail="Cross-referencing locations"
                active
              />

              <TraceItem
                icon={
                  <Users size={19} />
                }
                title="Impact"
                text="Analyzing stakeholder impact"
                detail="Residents, businesses & others"
                active
              />

              <TraceItem
                icon={
                  <ShieldCheck size={19} />
                }
                title="Verify"
                text="Checking evidence"
                detail="Preparing evidence-backed findings"
                active
              />
            </div>
          </section>
        )}

        {/* ===================================================
            COMPLETED AGENT TRACE
            =================================================== */}

        {result && !loading && (
          <>
            <section className="agent-progress completed">
              <div className="progress-header">
                <div>
                  <span className="eyebrow">
                    <CheckCircle2 size={15} />
                    INVESTIGATION COMPLETE
                  </span>

                  <h2>
                    Agent execution trace
                  </h2>
                </div>

                <span className="completed-badge">
                  {getOverallToolCount(
                    result
                  )}{" "}
                  tools executed
                </span>
              </div>

              <div className="trace-grid">
                <TraceItem
                  icon={
                    <BrainCircuit size={19} />
                  }
                  title="Plan"
                  text="Investigation strategy created"
                  detail={`${getPlanMetric(
                    result
                  )} investigation steps`}
                  done
                />

                <TraceItem
                  icon={
                    <Search size={19} />
                  }
                  title="Retrieve"
                  text="Municipal evidence retrieved"
                  detail={`${getToolMetric(
                    result,
                    "search_policy_documents"
                  )} evidence passages`}
                  done
                />

                <TraceItem
                  icon={
                    <MapPin size={19} />
                  }
                  title="Locate"
                  text="Affected areas investigated"
                  detail={`${getToolMetric(
                    result,
                    "find_affected_locations"
                  )} location evidence passages`}
                  done
                />

                <TraceItem
                  icon={
                    <Users size={19} />
                  }
                  title="Impact"
                  text="Stakeholder impacts analyzed"
                  detail={`${getStakeholderMetric(
                    result
                  )} stakeholder groups analyzed`}
                  done
                />

                <TraceItem
                  icon={
                    <ShieldCheck size={19} />
                  }
                  title="Verify"
                  text="Claims checked against evidence"
                  detail={`${getToolMetric(
                    result,
                    "verify_claim"
                  )} supporting passages found`}
                  done
                />
              </div>
            </section>

            {/* =================================================
                EVIDENCE GRAPH
                ================================================= */}

            <EvidenceGraph
              graph={
                result.evidence_graph
              }
            />

            {/* =================================================
                REPORT
                ================================================= */}

            <Report
              report={result.report}
            />
          </>
        )}
      </main>

      <footer>
        CivicLens • Evidence-backed municipal
        policy intelligence • Hackathon Prototype
      </footer>
    </div>
  );
}

/* =========================================================
   RESULT NORMALIZATION
   ========================================================= */

function normalizeResult(data) {
  if (!data) {
    return null;
  }

  /*
   * Current API responses contain the result directly.
   *
   * Older/saved investigation responses may contain
   * the investigation object with fields such as
   * tools, evidence_graph and report directly.
   */

  const source =
    data?.result &&
    typeof data.result === "object"
      ? data.result
      : data;

  const tools =
    source?.tools ||
    source?.tool_results ||
    data?.tools ||
    data?.tool_results ||
    [];

  const evidenceGraph =
    source?.evidence_graph ||
    data?.evidence_graph ||
    {
      nodes: [],
      edges: [],
    };

  return {
    ...source,

    investigation_id:
      data?.investigation_id ||
      data?.id ||
      source?.investigation_id,

    request:
      source?.request ||
      data?.request ||
      data?.question ||
      "",

    plan:
      source?.plan ||
      data?.plan ||
      {
        steps: [],
      },

    tools: Array.isArray(tools)
      ? tools
      : [],

    tool_results: Array.isArray(
      tools
    )
      ? tools
      : [],

    evidence_graph:
      evidenceGraph,

    report:
      source?.report ||
      data?.report ||
      "",

    metrics:
      source?.metrics ||
      data?.metrics ||
      {},
  };
}

/* =========================================================
   AGENT / RESULT HELPERS
   ========================================================= */

function getToolResults(result) {
  const tools =
    result?.tools ||
    result?.tool_results ||
    [];

  return Array.isArray(tools)
    ? tools
    : [];
}

function getToolResult(
  result,
  toolName
) {
  const tools =
    getToolResults(result);

  const tool = tools.find(
    (item) =>
      item?.tool === toolName
  );

  return tool?.result || null;
}

function getToolMetric(
  result,
  toolName
) {
  const toolResult =
    getToolResult(
      result,
      toolName
    );

  if (!toolResult) {
    return 0;
  }

  /*
   * Prefer the explicit evidence_count
   * generated by the improved backend tools.
   */

  if (
    typeof toolResult.evidence_count ===
      "number" &&
    toolResult.evidence_count >= 0
  ) {
    return toolResult.evidence_count;
  }

  if (
    toolName ===
    "search_policy_documents"
  ) {
    return (
      toolResult.results?.length ||
      toolResult.evidence?.length ||
      0
    );
  }

  if (
    toolName ===
    "find_affected_locations"
  ) {
    return (
      toolResult.location_evidence
        ?.length ||
      toolResult.results?.length ||
      toolResult.evidence?.length ||
      0
    );
  }

  if (
    toolName ===
    "verify_claim"
  ) {
    return (
      toolResult.evidence?.length ||
      toolResult.results?.length ||
      0
    );
  }

  return 0;
}

function getStakeholderMetric(
  result
) {
  const toolResult =
    getToolResult(
      result,
      "analyze_impact"
    );

  if (!toolResult) {
    return 0;
  }

  if (
    Array.isArray(
      toolResult.stakeholders
    )
  ) {
    return toolResult.stakeholders.length;
  }

  if (
    Array.isArray(
      toolResult.affected_stakeholders
    )
  ) {
    return toolResult
      .affected_stakeholders.length;
  }

  if (
    Array.isArray(
      toolResult.results
    )
  ) {
    return toolResult.results.length;
  }

  return 0;
}

function getPlanMetric(result) {
  const steps =
    result?.plan?.steps;

  if (Array.isArray(steps)) {
    return steps.length;
  }

  const actions =
    result?.plan?.actions;

  if (Array.isArray(actions)) {
    return actions.length;
  }

  if (
    Array.isArray(result?.plan)
  ) {
    return result.plan.length;
  }

  return 4;
}

function getOverallToolCount(
  result
) {
  if (
    typeof result?.metrics
      ?.tool_count === "number"
  ) {
    return result.metrics.tool_count;
  }

  return getToolResults(result)
    .length;
}

function getInvestigationQuestion(
  investigation
) {
  return (
    investigation?.request ||
    investigation?.question ||
    investigation?.result?.request ||
    investigation?.result?.question ||
    "Untitled investigation"
  );
}

function getInvestigationResult(
  investigation
) {
  if (
    investigation?.result &&
    typeof investigation.result ===
      "object"
  ) {
    return investigation.result;
  }

  if (
    investigation?.analysis &&
    typeof investigation.analysis ===
      "object"
  ) {
    return investigation.analysis;
  }

  if (
    investigation?.data &&
    typeof investigation.data ===
      "object"
  ) {
    return investigation.data;
  }

  return investigation;
}

function getInvestigationToolCount(
  investigation
) {
  const data =
    getInvestigationResult(
      investigation
    );

  if (
    typeof investigation?.tool_count ===
      "number"
  ) {
    return investigation.tool_count;
  }

  if (
    typeof data?.metrics?.tool_count ===
      "number"
  ) {
    return data.metrics.tool_count;
  }

  const tools =
    data?.tools ||
    data?.tool_results ||
    [];

  if (Array.isArray(tools)) {
    return tools.length;
  }

  return 0;
}

function getInvestigationNodeCount(
  investigation
) {
  const data =
    getInvestigationResult(
      investigation
    );

  if (
    typeof investigation?.node_count ===
      "number"
  ) {
    return investigation.node_count;
  }

  if (
    typeof data?.metrics?.node_count ===
      "number"
  ) {
    return data.metrics.node_count;
  }

  return (
    data?.evidence_graph?.nodes
      ?.length || 0
  );
}

/* =========================================================
   TRACE ITEM
   ========================================================= */

function TraceItem({
  icon,
  title,
  text,
  detail,
  active,
  done,
}) {
  return (
    <div
      className={`trace-item ${
        active ? "active" : ""
      } ${done ? "done" : ""}`}
    >
      <div className="trace-icon">
        {icon}
      </div>

      <div className="trace-content">
        <strong>{title}</strong>

        <span>{text}</span>

        {detail && (
          <small className="trace-detail">
            {detail}
          </small>
        )}
      </div>

      {done && (
        <CheckCircle2
          className="trace-check"
          size={17}
        />
      )}
    </div>
  );
}

/* =========================================================
   EVIDENCE GRAPH
   ========================================================= */

function EvidenceGraph({
  graph,
}) {
  if (
    !graph?.nodes?.length
  ) {
    return null;
  }

  const getNodes = (type) =>
    graph.nodes.filter(
      (node) =>
        node.type === type
    );

  const policyNodes =
    getNodes("policy");

  const ruleNodes =
    getNodes("rule");

  const locationNodes =
    getNodes("location");

  const stakeholderNodes =
    getNodes("stakeholder");

  const impactNodes =
    getNodes("impact");

  const evidenceNodes =
    getNodes("evidence");

  return (
    <section className="graph-section">
      <div className="graph-heading">
        <div>
          <span className="eyebrow">
            <GitBranch size={15} />
            EVIDENCE INVESTIGATION GRAPH
          </span>

          <h2>
            How CivicLens reached its findings
          </h2>

          <p>
            Every investigation follows an
            evidence chain from the policy
            change through applicable rules,
            affected places, stakeholders,
            potential impacts, and
            supporting sources.
          </p>
        </div>

        <div className="graph-stat">
          <GitBranch size={17} />

          <span>
            {graph.nodes.length} nodes •{" "}
            {graph.edges?.length ||
              0}{" "}
            links
          </span>
        </div>
      </div>

      <div className="graph-flow">
        <GraphStage
          icon={
            <Scale size={20} />
          }
          label="POLICY"
          title="Policy Change"
          nodes={policyNodes}
          type="policy"
        />

        <GraphConnector />

        <GraphStage
          icon={
            <FileText size={20} />
          }
          label="RULES"
          title="Relevant Rules"
          nodes={ruleNodes}
          type="rule"
        />

        <GraphConnector />

        <GraphStage
          icon={
            <MapPin size={20} />
          }
          label="LOCATION"
          title="Affected Areas"
          nodes={locationNodes}
          type="location"
        />

        <GraphConnector />

        <GraphStage
          icon={
            <Users size={20} />
          }
          label="PEOPLE"
          title="Stakeholders"
          nodes={
            stakeholderNodes
          }
          type="stakeholder"
        />

        <GraphConnector />

        <GraphStage
          icon={
            <Activity size={20} />
          }
          label="IMPACT"
          title="Potential Impact"
          nodes={impactNodes}
          type="impact"
        />

        <GraphConnector />

        <GraphStage
          icon={
            <Database size={20} />
          }
          label="EVIDENCE"
          title="Supporting Sources"
          nodes={evidenceNodes}
          type="evidence"
        />
      </div>

      <div className="graph-explanation">
        <div>
          <CheckCircle2 size={17} />
          <span>
            Evidence-backed relationship
          </span>
        </div>

        <div>
          <ShieldCheck size={17} />
          <span>
            Human verification remains required
          </span>
        </div>

        <div>
          <Lightbulb size={17} />
          <span>
            AI produces decision support, not legal
            decisions
          </span>
        </div>
      </div>
    </section>
  );
}

function GraphStage({
  icon,
  label,
  title,
  nodes,
  type,
}) {
  return (
    <div
      className={`graph-stage graph-stage-${type}`}
    >
      <div className="graph-stage-header">
        <div className="graph-stage-icon">
          {icon}
        </div>

        <div>
          <span>{label}</span>
          <strong>{title}</strong>
        </div>
      </div>

      <div className="graph-nodes">
        {nodes.length === 0 ? (
          <div className="graph-empty">
            No linked evidence
          </div>
        ) : (
          nodes.map(
            (node, index) => (
              <GraphNode
                key={
                  node.id ||
                  `${type}-${index}`
                }
                node={node}
                type={type}
              />
            )
          )
        )}
      </div>
    </div>
  );
}

function GraphNode({
  node,
  type,
}) {
  const description =
    node.description || "";

  return (
    <div
      className={`graph-node graph-node-${type}`}
    >
      <div className="graph-node-top">
        <span className="graph-node-label">
          {type === "rule" &&
            "RULE"}
          {type === "location" &&
            "AREA"}
          {type ===
            "stakeholder" &&
            "STAKEHOLDER"}
          {type === "impact" &&
            "IMPACT"}
          {type === "evidence" &&
            "SOURCE"}
          {type === "policy" &&
            "CHANGE"}
        </span>

        <CheckCircle2 size={14} />
      </div>

      <strong>
        {node.label ||
          "Untitled finding"}
      </strong>

      {description && (
        <p>
          {description.length >
          180
            ? `${description.slice(
                0,
                180
              )}...`
            : description}
        </p>
      )}

      {(node.document ||
        node.page) && (
        <div className="graph-source">
          <FileText size={12} />

          <span>
            {node.document ||
              "Source"}
            {node.page
              ? ` • Page ${node.page}`
              : ""}
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

function Report({
  report,
}) {
  const sections =
    parseReport(report);

  const confidence =
    sections["Confidence"];

  return (
    <section className="report-section">
      <div className="report-title-row">
        <div>
          <span className="eyebrow">
            <FileText size={15} />
            POLICY IMPACT REPORT
          </span>

          <h2>
            CivicLens Findings
          </h2>
        </div>

        <div className="confidence">
          <ShieldCheck size={18} />
          {getConfidenceLabel(
            confidence
          )}
        </div>
      </div>

      <div className="report-grid">
        <ReportCard
          icon={
            <FileText size={20} />
          }
          title="Executive Summary"
          content={
            sections[
              "Executive Summary"
            ]
          }
        />

        <ReportCard
          icon={
            <ArrowRight size={20} />
          }
          title="What Changed"
          content={
            sections[
              "What Changed"
            ]
          }
        />

        <ReportCard
          icon={
            <MapPin size={20} />
          }
          title="Affected Locations"
          content={
            sections[
              "Affected Locations"
            ]
          }
        />

        <ReportCard
          icon={
            <Users size={20} />
          }
          title="Affected Stakeholders"
          content={
            sections[
              "Affected Stakeholders"
            ]
          }
        />

        <ReportCard
          wide
          icon={
            <AlertTriangle
              size={20}
            />
          }
          title="Potential Impacts"
          content={
            sections[
              "Potential Impacts"
            ]
          }
        />

        <ReportCard
          wide
          icon={
            <ShieldCheck
              size={20}
            />
          }
          title="Confidence"
          content={
            sections[
              "Confidence"
            ]
          }
        />
      </div>

      {/* ===================================================
          TRACEABLE EVIDENCE
          =================================================== */}

      <div className="evidence-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">
              <ShieldCheck size={15} />
              TRACEABLE EVIDENCE
            </span>

            <h3>
              Sources used by the agent
            </h3>
          </div>
        </div>

        <div className="evidence-content">
          {formatEvidence(
            sections["Evidence"]
          )}
        </div>
      </div>

      {/* ===================================================
          ACTIONS / VERIFICATION
          =================================================== */}

      <div className="bottom-grid">
        <div className="recommendation-panel">
          <div className="panel-heading">
            <h3>
              Recommended Actions
            </h3>
          </div>

          <div className="panel-content">
            {formatContent(
              sections[
                "Recommended Actions"
              ]
            )}
          </div>
        </div>

        <div className="verification-panel">
          <div className="panel-heading">
            <h3>
              Verification Required
            </h3>
          </div>

          <div className="panel-content">
            {formatContent(
              sections[
                "Verification Required"
              ]
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function getConfidenceLabel(
  content
) {
  if (!content) {
    return "Evidence-backed analysis";
  }

  const normalized =
    content.toLowerCase();

  if (
    normalized.includes("high")
  ) {
    return "High evidence confidence";
  }

  if (
    normalized.includes("medium")
  ) {
    return "Moderate evidence confidence";
  }

  if (
    normalized.includes("low")
  ) {
    return "Limited evidence confidence";
  }

  return "Evidence-backed analysis";
}

function ReportCard({
  icon,
  title,
  content,
  wide,
}) {
  return (
    <div
      className={`report-card ${
        wide ? "wide" : ""
      }`}
    >
      <div className="report-card-icon">
        {icon}
      </div>

      <h3>{title}</h3>

      <div className="report-card-content">
        {formatContent(
          content
        )}
      </div>
    </div>
  );
}

/* =========================================================
   REPORT PARSING
   ========================================================= */

function parseReport(
  report
) {
  if (!report) {
    return {};
  }

  const sections = {};

  const parts =
    report.split(/^## /gm);

  parts.forEach(
    (part) => {
      const lines = part
        .trim()
        .split("\n");

      if (!lines.length) {
        return;
      }

      let title =
        lines[0].trim();

      title =
        title.replace(
          /^\d+\.\s*/,
          ""
        );

      if (
        title &&
        title !==
          "CivicLens Policy Impact Report"
      ) {
        sections[title] =
          lines
            .slice(1)
            .join("\n")
            .trim();
      }
    }
  );

  return sections;
}

/* =========================================================
   NORMAL CONTENT FORMATTER
   ========================================================= */

function formatContent(
  content = ""
) {
  if (!content) {
    return (
      <span className="muted">
        No information returned.
      </span>
    );
  }

  const lines = content
    .split("\n")
    .map(
      (line) => line.trim()
    )
    .filter(Boolean);

  return lines.map(
    (line, index) => {
      const isNumbered =
        /^\d+\.\s/.test(
          line
        );

      const clean =
        line
          .replace(
            /^\d+\.\s*/,
            ""
          )
          .replace(
            /^\s*[-*]\s*/,
            ""
          )
          .replace(
            /\*\*/g,
            ""
          )
          .replace(
            /^`|`$/g,
            ""
          );

      return (
        <div
          className={
            isNumbered
              ? "numbered-item"
              : undefined
          }
          key={index}
        >
          {clean}
        </div>
      );
    }
  );
}

/* =========================================================
   EVIDENCE FORMATTER
   ========================================================= */

function formatEvidence(
  content = ""
) {
  if (!content) {
    return (
      <span className="muted">
        No evidence returned.
      </span>
    );
  }

  const lines = content
    .split("\n")
    .map(
      (line) => line.trim()
    )
    .filter(Boolean);

  /*
   * Markdown evidence tables can vary slightly.
   * Instead of assuming the first two rows are always
   * the header and separator, explicitly detect them.
   */

  const tableRows =
    lines.filter(
      (line) =>
        line.startsWith("|") &&
        line.includes("|")
    );

  if (tableRows.length > 0) {
    const parsedRows =
      tableRows
        .map(
          (line) =>
            line
              .split("|")
              .slice(1, -1)
              .map(
                (cell) =>
                  cell
                    .trim()
                    .replace(
                      /\*\*/g,
                      ""
                    )
              )
        )
        .filter(
          (cells) =>
            cells.length >= 2 &&
            cells.some(Boolean)
        );

    const dataRows =
      parsedRows.filter(
        (cells) => {
          const joined =
            cells.join(
              " "
            );

          const isSeparator =
            cells.every(
              (cell) =>
                /^:?-{2,}:?$/.test(
                  cell
                )
            );

          const isHeader =
            /document|evidence|claim|topic|page|source/i.test(
              joined
            ) &&
            !/\bpage\s+\d+/i.test(
              joined
            );

          return (
            !isSeparator &&
            !isHeader
          );
        }
      );

    if (
      dataRows.length > 0
    ) {
      return dataRows.map(
        (
          cells,
          index
        ) => {
          /*
           * Most generated CivicLens tables use:
           * Claim / Topic | Document | Page | Evidence Summary
           *
           * If the structure differs, we still display all
           * cells rather than losing information.
           */

          const claim =
            cells[0] ||
            "Evidence finding";

          const document =
            cells[1] ||
            "";

          const page =
            cells[2] ||
            "";

          const summary =
            cells
              .slice(3)
              .join(" • ");

          return (
            <div
              className="evidence-line"
              key={index}
            >
              <CheckCircle2
                size={16}
              />

              <div className="evidence-line-content">
                <strong>
                  {claim}
                </strong>

                {(document ||
                  page) && (
                  <span>
                    {document ||
                      "Source document"}
                    {page
                      ? ` • ${page}`
                      : ""}
                  </span>
                )}

                {summary && (
                  <p>
                    {summary}
                  </p>
                )}

                {cells.length >
                  4 && (
                  <p>
                    {cells
                      .slice(4)
                      .join(
                        " • "
                      )}
                  </p>
                )}
              </div>
            </div>
          );
        }
      );
    }
  }

  /*
   * Fallback for evidence generated without a Markdown table.
   */

  return lines
    .filter(
      (line) =>
        !/^\|?\s*:?-{2,}/.test(
          line
        )
    )
    .filter(
      (line) =>
        !/^\|\s*(Claim\s*\/\s*Topic|Document|Source|Evidence)/i.test(
          line
        )
    )
    .map(
      (line, index) => {
        const clean =
          line
            .replace(
              /^[-*]\s*/,
              ""
            )
            .replace(
              /\*\*/g,
              ""
            )
            .replace(
              /^\|/,
              ""
            )
            .replace(
              /\|$/,
              ""
            );

        return (
          <div
            className="evidence-line"
            key={index}
          >
            <CheckCircle2
              size={16}
            />

            <span>
              {clean}
            </span>
          </div>
        );
      }
    );
}

export default App;