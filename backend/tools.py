from backend.rag import search_documents


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _deduplicate_results(results):
    """
    Remove duplicate document/page results while preserving
    the strongest retrieval result for each document/page pair.
    """

    best_results = {}

    for result in results or []:
        key = (
            result.get("document"),
            result.get("page")
        )

        score = float(result.get("score", 0) or 0)

        if key not in best_results:
            best_results[key] = result
        else:
            existing_score = float(
                best_results[key].get("score", 0) or 0
            )

            if score > existing_score:
                best_results[key] = result

    return sorted(
        best_results.values(),
        key=lambda item: float(item.get("score", 0) or 0),
        reverse=True
    )


def _confidence_from_scores(results):
    """
    Convert TF-IDF retrieval scores into a simple,
    explainable confidence level.

    This is retrieval confidence, not legal certainty.
    """

    if not results:
        return {
            "level": "LOW",
            "score": 0.0,
            "basis": "No relevant evidence was retrieved."
        }

    scores = [
        float(result.get("score", 0) or 0)
        for result in results
    ]

    top_score = max(scores)

    if top_score >= 0.30:
        level = "HIGH"
    elif top_score >= 0.12:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "level": level,
        "score": round(top_score, 4),
        "basis": (
            "Based on the strongest local TF-IDF evidence match. "
            "This indicates retrieval strength, not legal certainty."
        )
    }


def _prepare_results(results, limit=5):
    """
    Normalize and deduplicate retrieved evidence.
    """

    cleaned = []

    for result in _deduplicate_results(results)[:limit]:
        cleaned.append({
            "document": result.get(
                "document",
                "Unknown document"
            ),
            "page": result.get(
                "page",
                None
            ),
            "score": round(
                float(result.get("score", 0) or 0),
                4
            ),
            "text": result.get(
                "text",
                ""
            )
        })

    return cleaned


# =========================================================
# POLICY DOCUMENT SEARCH
# =========================================================

def search_policy_documents(query, top_k=5):
    """
    Search municipal documents and return evidence with
    document, page, score, and retrieval-confidence metadata.
    """

    results = search_documents(
        query=query,
        top_k=top_k
    )

    results = _prepare_results(
        results,
        limit=top_k
    )

    return {
        "query": query,
        "results": results,
        "evidence_count": len(results),
        "confidence": _confidence_from_scores(results)
    }


# =========================================================
# POLICY COMPARISON
# =========================================================

def compare_policy(old_text, new_text):
    """
    Identify important differences between an existing
    policy and a proposed policy.
    """

    old_lines = set(
        line.strip()
        for line in old_text.splitlines()
        if line.strip()
    )

    new_lines = set(
        line.strip()
        for line in new_text.splitlines()
        if line.strip()
    )

    removed = sorted(old_lines - new_lines)
    added = sorted(new_lines - old_lines)

    return {
        "added": added[:20],
        "removed": removed[:20],
        "change_count": len(added) + len(removed)
    }


# =========================================================
# AFFECTED LOCATIONS
# =========================================================

def find_affected_locations(policy_change):
    """
    Identify geographic references associated with a policy
    change using local document retrieval.
    """

    search_query = (
        f"locations zones roads corridors wards "
        f"affected by {policy_change}"
    )

    results = search_documents(
        search_query,
        top_k=5
    )

    results = _prepare_results(
        results,
        limit=5
    )

    locations = []

    for result in results:
        locations.append({
            "document": result["document"],
            "page": result["page"],
            "evidence": result["text"],
            "score": result["score"]
        })

    return {
        "policy_change": policy_change,
        "location_evidence": locations,
        "evidence_count": len(locations),
        "confidence": _confidence_from_scores(results)
    }


# =========================================================
# STAKEHOLDER / IMPACT ANALYSIS
# =========================================================

def analyze_impact(policy_change, stakeholders):
    """
    Retrieve evidence relevant to potential stakeholder
    and municipal impact analysis.
    """

    query = (
        f"{policy_change} impact on "
        f"{', '.join(stakeholders)} "
        f"traffic parking pedestrian residential "
        f"commercial public transport safety noise"
    )

    results = search_documents(
        query,
        top_k=5
    )

    results = _prepare_results(
        results,
        limit=5
    )

    return {
        "policy_change": policy_change,
        "stakeholders": stakeholders,
        "evidence": results,
        "evidence_count": len(results),
        "confidence": _confidence_from_scores(results)
    }


# =========================================================
# CLAIM VERIFICATION
# =========================================================

def verify_claim(claim):
    """
    Check whether the local document collection contains
    supporting evidence for a claim.

    Verification is deliberately conservative:
    the system reports whether supporting evidence was found,
    but does not claim legal or factual certainty.
    """

    results = search_documents(
        claim,
        top_k=5
    )

    results = _prepare_results(
        results,
        limit=5
    )

    # Keep the existing working threshold so current
    # investigations do not suddenly become unsupported.
    supporting_evidence = [
        result
        for result in results
        if result["score"] > 0.05
    ]

    weak_evidence = [
        result
        for result in results
        if 0.02 < result["score"] <= 0.05
    ]

    if supporting_evidence:
        verified = True

        if supporting_evidence[0]["score"] >= 0.30:
            verification_level = "STRONG SUPPORT"
        elif supporting_evidence[0]["score"] >= 0.12:
            verification_level = "MODERATE SUPPORT"
        else:
            verification_level = "LIMITED SUPPORT"

    elif weak_evidence:
        verified = False
        verification_level = "WEAK / INCONCLUSIVE"

    else:
        verified = False
        verification_level = "NO SUPPORTING EVIDENCE"

    return {
        "claim": claim,
        "verified": verified,
        "verification_level": verification_level,
        "evidence": supporting_evidence,
        "weak_evidence": weak_evidence,
        "evidence_count": len(supporting_evidence),
        "confidence": _confidence_from_scores(
            supporting_evidence
        )
    }


# =========================================================
# GEMINI EVIDENCE CONTEXT
# =========================================================

def generate_evidence_context(results):
    """
    Convert retrieved evidence into compact context suitable
    for the single Gemini reasoning/report call.

    This function does not call Gemini itself.
    """

    context = []

    for result in results or []:

        document = result.get(
            "document",
            "Unknown document"
        )

        page = result.get(
            "page",
            "N/A"
        )

        score = result.get(
            "score",
            0
        )

        text = result.get(
            "text",
            ""
        )

        context.append(
            f"[SOURCE: {document} | "
            f"PAGE: {page} | "
            f"SCORE: {score}]\n"
            f"{text}"
        )

    return "\n\n".join(context)