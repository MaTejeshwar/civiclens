from backend.rag import search_documents


def search_policy_documents(query, top_k=5):
    """
    Search municipal documents and return
    evidence with document and page references.
    """

    results = search_documents(
        query=query,
        top_k=top_k
    )

    return {
        "query": query,
        "results": results
    }


def compare_policy(old_text, new_text):
    """
    Identify the important differences between
    an existing policy and a proposed policy.
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


def find_affected_locations(policy_change):
    """
    Identify geographic references associated with
    a policy change using document retrieval.
    """

    search_query = (
        f"locations zones roads corridors wards "
        f"affected by {policy_change}"
    )

    results = search_documents(
        search_query,
        top_k=5
    )

    locations = []

    for result in results:

        text = result["text"]

        locations.append({
            "document": result["document"],
            "page": result["page"],
            "evidence": text
        })

    return {
        "policy_change": policy_change,
        "location_evidence": locations
    }


def analyze_impact(policy_change, stakeholders):
    """
    Retrieve evidence relevant to potential stakeholder impacts.
    """

    query = (
        f"{policy_change} impact on "
        f"{', '.join(stakeholders)} "
        f"traffic parking pedestrian residential commercial"
    )

    results = search_documents(
        query,
        top_k=5
    )

    return {
        "policy_change": policy_change,
        "stakeholders": stakeholders,
        "evidence": results
    }


def verify_claim(claim):
    """
    Check whether the document collection contains
    supporting evidence for a claim.
    """

    results = search_documents(
        claim,
        top_k=5
    )

    supporting_evidence = [
        result
        for result in results
        if result["score"] > 0.05
    ]

    return {
        "claim": claim,
        "verified": len(supporting_evidence) > 0,
        "evidence": supporting_evidence
    }


def generate_evidence_context(results):
    """
    Convert retrieved evidence into a compact context
    suitable for sending to Gemini.
    """

    context = []

    for result in results:

        context.append(
            f"[SOURCE: {result['document']} | "
            f"PAGE: {result['page']} | "
            f"SCORE: {result['score']}]\n"
            f"{result['text']}"
        )

    return "\n\n".join(context)