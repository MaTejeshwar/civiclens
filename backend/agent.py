import os
import json
from dotenv import load_dotenv
from google import genai

from backend.tools import (
    search_policy_documents,
    find_affected_locations,
    analyze_impact,
    verify_claim,
)


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in .env")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.7-flash"


def ask_gemini(prompt):
    models = [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
    ]

    last_error = None

    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            if response.text:
                return response.text

        except Exception as exc:
            last_error = exc

            print(
                f"Gemini model {model_name} failed. "
                f"Trying fallback..."
            )

    raise last_error


def create_plan(user_request):
    """
    Create a deterministic investigation plan.

    CivicLens uses a local orchestrator for planning so that
    Gemini is reserved for the higher-value reasoning/report step.
    """

    return {
        "objective": (
            "Investigate the municipal policy issue using retrieved "
            "evidence, affected-location analysis, stakeholder impact "
            "analysis, and claim verification."
        ),
        "steps": [
            {
                "tool": "search_policy_documents",
                "query": (
                    f"Find municipal policy rules, regulations, clauses, "
                    f"and documents relevant to: {user_request}"
                )
            },
            {
                "tool": "find_affected_locations",
                "query": (
                    f"Identify locations, zones, roads, corridors, or "
                    f"geographic areas potentially affected by: {user_request}"
                )
            },
            {
                "tool": "analyze_impact",
                "query": (
                    f"Analyze potential traffic, parking, pedestrian, "
                    f"residential, commercial, and public-transport impacts "
                    f"of: {user_request}"
                )
            },
            {
                "tool": "verify_claim",
                "query": (
                    f"Verify the important claims and factual assertions "
                    f"related to: {user_request}"
                )
            }
        ]
    }


def execute_tool(tool_name, query):
    """Execute one planned CivicLens tool."""

    if tool_name == "search_policy_documents":

        return search_policy_documents(
            query=query,
            top_k=5
        )

    if tool_name == "find_affected_locations":

        return find_affected_locations(
            policy_change=query
        )

    if tool_name == "analyze_impact":

        # Convert the planner's query into a stakeholder list.
        stakeholders = [
            "residents",
            "property owners",
            "businesses",
            "pedestrians",
            "public transport users"
        ]

        return analyze_impact(
            policy_change=query,
            stakeholders=stakeholders
        )

    if tool_name == "verify_claim":

        return verify_claim(
            claim=query
        )

    return {
        "error": f"Unknown tool: {tool_name}"
    }

def _short_text(text, limit=180):
    """Create a compact readable description for graph nodes."""
    if not text:
        return ""

    text = " ".join(str(text).split())

    if len(text) <= limit:
        return text

    return text[:limit].rstrip() + "..."


def build_evidence_graph(user_request, tool_results):
    """
    Build a human-readable evidence graph locally.

    No Gemini/API call is used here.
    """

    nodes = []
    edges = []

    def add_node(node):
        nodes.append(node)

    def add_edge(source, target, label):
        edges.append({
            "source": source,
            "target": target,
            "label": label
        })

    # =========================================================
    # POLICY
    # =========================================================

    add_node({
        "id": "policy",
        "type": "policy",
        "label": "Mixed-Use Corridor Amendment",
        "description": _short_text(user_request, 190)
    })

    # =========================================================
    # RULES
    # =========================================================

    policy_results = []

    for item in tool_results:
        if item["tool"] == "search_policy_documents":
            policy_results = item["result"].get("results", [])
            break

    rule_nodes = []

    rule_keywords = [
        ("Residential (Mixed)", ["residential", "mixed"]),
        ("Mutation Corridor", ["mutation corridor"]),
        ("Commercial Use", ["commercial"]),
        ("Development Controls", ["development control"]),
        ("Road-Width Requirements", ["road width", "road-width"]),
    ]

    selected_rules = []

    for result in policy_results:
        text = result.get("text", "")
        lower_text = text.lower()

        for label, keywords in rule_keywords:
            if all(keyword in lower_text for keyword in keywords):
                selected_rules.append((label, result))
                break

    # If keyword matching found nothing, retain top evidence.
    if not selected_rules:
        for result in policy_results[:3]:
            selected_rules.append((
                "Relevant Planning Rule",
                result
            ))

    # Remove duplicate rule labels.
    seen_rules = set()

    for index, (label, result) in enumerate(selected_rules[:3]):

        if label in seen_rules:
            continue

        seen_rules.add(label)

        node_id = f"rule_{len(rule_nodes)}"

        add_node({
            "id": node_id,
            "type": "rule",
            "label": label,
            "description": _short_text(
                result.get("text", ""),
                175
            ),
            "document": result.get("document"),
            "page": result.get("page"),
            "score": result.get("score")
        })

        rule_nodes.append(node_id)

        add_edge(
            "policy",
            node_id,
            "checked against"
        )

    # =========================================================
    # LOCATIONS
    # =========================================================

    location_evidence = []

    for item in tool_results:
        if item["tool"] == "find_affected_locations":
            location_evidence = item["result"].get(
                "location_evidence",
                []
            )
            break

    location_nodes = []

    location_candidates = [
        (
            "Outer Ring Road Corridor",
            ["outer ring road"]
        ),
        (
            "Junction A → Junction B",
            ["junction a", "junction b"]
        ),
        (
            "100m Residential Buffer",
            ["100 metres", "100 meters", "100m"]
        ),
        (
            "Adjacent Residential Streets",
            ["residential streets"]
        ),
    ]

    combined_location_text = " ".join(
        item.get("evidence", "")
        for item in location_evidence
    ).lower()

    for label, keywords in location_candidates:

        if all(keyword in combined_location_text for keyword in keywords):

            node_id = f"location_{len(location_nodes)}"

            matching_evidence = next(
                (
                    item
                    for item in location_evidence
                    if all(
                        keyword in item.get(
                            "evidence",
                            ""
                        ).lower()
                        for keyword in keywords
                    )
                ),
                location_evidence[0]
                if location_evidence
                else {}
            )

            add_node({
                "id": node_id,
                "type": "location",
                "label": label,
                "description": _short_text(
                    matching_evidence.get(
                        "evidence",
                        "Potentially affected geographic area."
                    ),
                    175
                ),
                "document": matching_evidence.get("document"),
                "page": matching_evidence.get("page")
            })

            location_nodes.append(node_id)

            if rule_nodes:
                add_edge(
                    rule_nodes[0],
                    node_id,
                    "applies to"
                )
            else:
                add_edge(
                    "policy",
                    node_id,
                    "affects"
                )

    # Fallback if the documents don't contain our expected terms.
    if not location_nodes and location_evidence:

        for index, item in enumerate(location_evidence[:2]):

            node_id = f"location_{index}"

            add_node({
                "id": node_id,
                "type": "location",
                "label": f"Affected Area {index + 1}",
                "description": _short_text(
                    item.get("evidence", ""),
                    175
                ),
                "document": item.get("document"),
                "page": item.get("page")
            })

            location_nodes.append(node_id)

            add_edge(
                "policy",
                node_id,
                "affects"
            )

    # =========================================================
    # STAKEHOLDERS
    # =========================================================

    stakeholders = []

    for item in tool_results:
        if item["tool"] == "analyze_impact":
            stakeholders = item["result"].get(
                "stakeholders",
                []
            )
            break

    stakeholder_nodes = []

    for index, stakeholder in enumerate(stakeholders):

        node_id = f"stakeholder_{index}"

        label = stakeholder.title()

        add_node({
            "id": node_id,
            "type": "stakeholder",
            "label": label,
            "description": (
                f"Potentially affected {stakeholder.lower()}."
            )
        })

        stakeholder_nodes.append(node_id)

        if location_nodes:
            add_edge(
                location_nodes[0],
                node_id,
                "may affect"
            )
        else:
            add_edge(
                "policy",
                node_id,
                "may affect"
            )

    # =========================================================
    # IMPACTS
    # =========================================================

    impact_results = []

    for item in tool_results:
        if item["tool"] == "analyze_impact":
            impact_results = item["result"].get(
                "evidence",
                []
            )
            break

    combined_impact_text = " ".join(
        item.get("text", "")
        for item in impact_results
    ).lower()

    impact_candidates = [
        (
            "Traffic & Parking Risk",
            [
                "traffic",
                "parking"
            ],
            "Potential increase in vehicle trips and parking pressure."
        ),
        (
            "Pedestrian Safety Risk",
            [
                "pedestrian"
            ],
            "Potential increase in pedestrian conflict points."
        ),
        (
            "Residential Character & Noise",
            [
                "residential"
            ],
            "Commercial activity may affect nearby residential areas."
        ),
        (
            "Economic Opportunity",
            [
                "economic",
                "commercial"
            ],
            "Potential economic benefits for local businesses."
        ),
    ]

    impact_nodes = []

    for label, keywords, description in impact_candidates:

        if all(keyword in combined_impact_text for keyword in keywords):

            node_id = f"impact_{len(impact_nodes)}"

            add_node({
                "id": node_id,
                "type": "impact",
                "label": label,
                "description": description
            })

            impact_nodes.append(node_id)

            for stakeholder_id in stakeholder_nodes[:4]:

                add_edge(
                    stakeholder_id,
                    node_id,
                    "may experience"
                )

    # Fallback impact node.
    if not impact_nodes and impact_results:

        node_id = "impact_0"

        add_node({
            "id": node_id,
            "type": "impact",
            "label": "Potential Impact",
            "description": (
                f"Impact analysis supported by "
                f"{len(impact_results)} evidence items."
            )
        })

        impact_nodes.append(node_id)

        for stakeholder_id in stakeholder_nodes[:4]:

            add_edge(
                stakeholder_id,
                node_id,
                "may experience"
            )

    # =========================================================
    # EVIDENCE
    # =========================================================

    evidence_items = []

    for item in tool_results:

        result = item.get("result", {})

        if item["tool"] == "search_policy_documents":

            evidence_items.extend(
                result.get("results", [])
            )

        elif item["tool"] == "analyze_impact":

            evidence_items.extend(
                result.get("evidence", [])
            )

        elif item["tool"] == "verify_claim":

            evidence_items.extend(
                result.get("evidence", [])
            )

    # Deduplicate document/page combinations.
    unique_evidence = []
    seen_evidence = set()

    for evidence in evidence_items:

        key = (
            evidence.get("document"),
            evidence.get("page")
        )

        if key in seen_evidence:
            continue

        seen_evidence.add(key)
        unique_evidence.append(evidence)

    evidence_nodes = []

    for index, evidence in enumerate(unique_evidence[:5]):

        node_id = f"evidence_{index}"

        document = evidence.get(
            "document",
            "Source Document"
        )

        add_node({
            "id": node_id,
            "type": "evidence",
            "label": document,
            "description": _short_text(
                evidence.get("text", ""),
                175
            ),
            "document": document,
            "page": evidence.get("page"),
            "score": evidence.get("score")
        })

        evidence_nodes.append(node_id)

        if impact_nodes:
            add_edge(
                impact_nodes[0],
                node_id,
                "supported by"
            )
        else:
            add_edge(
                "policy",
                node_id,
                "supported by"
            )

    return {
        "nodes": nodes,
        "edges": edges
    }

def run_agent(user_request):
    """
    Run the complete CivicLens investigation.

    Returns:
        plan
        tool results
        evidence graph
        final evidence-backed report
    """

    # ---------------------------------------------------------
    # 1. PLAN
    # ---------------------------------------------------------

    plan = create_plan(user_request)

    tool_results = []

    # ---------------------------------------------------------
    # 2. EXECUTE PLAN
    # ---------------------------------------------------------

    for step in plan.get("steps", []):

        tool_name = step.get("tool")
        query = step.get("query", user_request)

        result = execute_tool(
            tool_name,
            query
        )

        tool_results.append({
            "tool": tool_name,
            "query": query,
            "result": result
        })

    # ---------------------------------------------------------
    # 3. BUILD EVIDENCE PACKAGE
    # ---------------------------------------------------------

    evidence_package = json.dumps(
        tool_results,
        ensure_ascii=False,
        indent=2
    )

    # Keep the prompt bounded for the free API.
    evidence_package = evidence_package[:30000]

    # ---------------------------------------------------------
    # 4. REASON + GENERATE REPORT
    # ---------------------------------------------------------

    report_prompt = f"""
You are CivicLens, an evidence-backed municipal policy
impact intelligence agent.

User request:
{user_request}

Investigation plan:
{json.dumps(plan, ensure_ascii=False, indent=2)}

Tool results:
{evidence_package}

Produce a concise Policy Impact Report.

Use ONLY evidence contained in the tool results.

Do NOT invent:
- laws
- locations
- statistics
- government decisions
- approvals
- legal conclusions

Clearly distinguish:
- verified evidence
- potential impact
- unresolved questions

Return the report using exactly these sections:

# CivicLens Policy Impact Report

## 1. Executive Summary
Briefly explain the policy issue.

## 2. What Changed
Identify the relevant policy change or issue.

## 3. Affected Locations
List locations/zones supported by retrieved evidence.

## 4. Affected Stakeholders
Identify residents, businesses, pedestrians, property owners,
transport users, authorities, or other relevant groups.

## 5. Potential Impacts
Explain likely positive and negative effects.
Use cautious language such as "may", "could", or
"potentially" where appropriate.

## 6. Evidence
For every important claim, provide:
- Document
- Page
- Evidence summary

## 7. Confidence
Give HIGH, MEDIUM, or LOW confidence and explain why.

## 8. Recommended Actions
Give practical next steps for human decision-makers.

## 9. Verification Required
List facts that CivicLens could not conclusively verify.
"""

    final_report = ask_gemini(report_prompt)

    # ---------------------------------------------------------
    # 5. BUILD EVIDENCE GRAPH LOCALLY
    # ---------------------------------------------------------
    # This uses existing tool results.
    # No additional Gemini/API call is required.

    evidence_graph = build_evidence_graph(
        user_request,
        tool_results
    )

    # ---------------------------------------------------------
    # 6. RETURN COMPLETE INVESTIGATION
    # ---------------------------------------------------------

    return {
        "request": user_request,
        "plan": plan,
        "tool_results": tool_results,
        "evidence_graph": evidence_graph,
        "report": final_report
    }