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

    graph_nodes = []
    graph_edges = []

    # Policy node
    graph_nodes.append({
        "id": "policy",
        "type": "policy",
        "label": "Policy Change",
        "description": user_request
    })

    # ---------------------------------------------------------
    # Rules / document evidence
    # ---------------------------------------------------------

    policy_results = []

    for item in tool_results:
        if item["tool"] == "search_policy_documents":
            policy_results = item["result"].get("results", [])
            break

    rule_nodes = []

    for index, result in enumerate(policy_results[:3]):
        node_id = f"rule_{index}"

        graph_nodes.append({
            "id": node_id,
            "type": "rule",
            "label": result.get("document", "Municipal Document"),
            "description": (
                f"Page {result.get('page', 'N/A')}: "
                f"{result.get('text', '')[:220]}"
            ),
            "document": result.get("document"),
            "page": result.get("page"),
            "score": result.get("score")
        })

        rule_nodes.append(node_id)

        graph_edges.append({
            "source": "policy",
            "target": node_id,
            "label": "supported by"
        })

    # ---------------------------------------------------------
    # Affected locations
    # ---------------------------------------------------------

    location_evidence = []

    for item in tool_results:
        if item["tool"] == "find_affected_locations":
            location_evidence = item["result"].get(
                "location_evidence",
                []
            )
            break

    location_nodes = []

    for index, location in enumerate(location_evidence[:3]):
        node_id = f"location_{index}"

        graph_nodes.append({
            "id": node_id,
            "type": "location",
            "label": f"Affected Area {index + 1}",
            "description": location.get(
                "evidence",
                ""
            )[:250],
            "document": location.get("document"),
            "page": location.get("page")
        })

        location_nodes.append(node_id)

        if rule_nodes:
            graph_edges.append({
                "source": rule_nodes[0],
                "target": node_id,
                "label": "applies to"
            })
        else:
            graph_edges.append({
                "source": "policy",
                "target": node_id,
                "label": "affects"
            })

    # ---------------------------------------------------------
    # Stakeholders
    # ---------------------------------------------------------

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

        graph_nodes.append({
            "id": node_id,
            "type": "stakeholder",
            "label": stakeholder.title(),
            "description": "Potentially affected stakeholder"
        })

        stakeholder_nodes.append(node_id)

        if location_nodes:
            graph_edges.append({
                "source": location_nodes[0],
                "target": node_id,
                "label": "affects"
            })
        else:
            graph_edges.append({
                "source": "policy",
                "target": node_id,
                "label": "affects"
            })

    # ---------------------------------------------------------
    # Impact analysis
    # ---------------------------------------------------------

    impact_results = []

    for item in tool_results:
        if item["tool"] == "analyze_impact":
            impact_results = item["result"].get(
                "evidence",
                []
            )
            break

    if impact_results:
        impact_node_id = "impact"

        graph_nodes.append({
            "id": impact_node_id,
            "type": "impact",
            "label": "Potential Impact",
            "description": (
                "Impact analysis supported by "
                f"{len(impact_results)} retrieved evidence items."
            )
        })

        for stakeholder_id in stakeholder_nodes[:3]:
            graph_edges.append({
                "source": stakeholder_id,
                "target": impact_node_id,
                "label": "may experience"
            })

    # ---------------------------------------------------------
    # Evidence node
    # ---------------------------------------------------------

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

    # Remove duplicate document/page combinations
    unique_evidence = []
    seen = set()

    for evidence in evidence_items:
        key = (
            evidence.get("document"),
            evidence.get("page")
        )

        if key not in seen:
            seen.add(key)
            unique_evidence.append(evidence)

    evidence_node_ids = []

    for index, evidence in enumerate(unique_evidence[:5]):
        node_id = f"evidence_{index}"

        graph_nodes.append({
            "id": node_id,
            "type": "evidence",
            "label": evidence.get(
                "document",
                "Source Document"
            ),
            "description": (
                f"Page {evidence.get('page', 'N/A')}: "
                f"{evidence.get('text', '')[:220]}"
            ),
            "document": evidence.get("document"),
            "page": evidence.get("page"),
            "score": evidence.get("score")
        })

        evidence_node_ids.append(node_id)

        if "impact" in [node["id"] for node in graph_nodes]:
            graph_edges.append({
                "source": "impact",
                "target": node_id,
                "label": "supported by"
            })
        else:
            graph_edges.append({
                "source": "policy",
                "target": node_id,
                "label": "evidence"
            })

    evidence_graph = {
        "nodes": graph_nodes,
        "edges": graph_edges
    }

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