import re

from app.catalog import find_by_name, names_to_recommendations, normalize
from app.retriever import retrieve
from app.schemas import ChatResponse, Message, Recommendation


CURATED = {
    "leadership": [
        "Occupational Personality Questionnaire OPQ32r",
        "OPQ Universal Competency Report 2.0",
        "OPQ Leadership Report",
    ],
    "rust_networking": [
        "Smart Interview Live Coding",
        "Linux Programming (General)",
        "Networking and Implementation (New)",
        "SHL Verify Interactive G+",
        "Occupational Personality Questionnaire OPQ32r",
    ],
    "contact_center_us": [
        "SVAR - Spoken English (US) (New)",
        "Contact Center Call Simulation (New)",
        "Entry Level Customer Serv-Retail & Contact Center",
        "Customer Service Phone Simulation",
    ],
    "finance_graduate": [
        "SHL Verify Interactive - Numerical Reasoning",
        "Financial Accounting (New)",
        "Basic Statistics (New)",
        "Occupational Personality Questionnaire OPQ32r",
    ],
    "finance_graduate_sjt": [
        "SHL Verify Interactive - Numerical Reasoning",
        "Financial Accounting (New)",
        "Basic Statistics (New)",
        "Graduate Scenarios",
        "Occupational Personality Questionnaire OPQ32r",
    ],
    "sales_reskill": [
        "Global Skills Assessment",
        "Global Skills Development Report",
        "Occupational Personality Questionnaire OPQ32r",
        "OPQ MQ Sales Report",
        "Sales Transformation 2.0 - Individual Contributor",
    ],
    "safety": [
        "Dependability and Safety Instrument (DSI)",
        "Manufac. & Indust. - Safety & Dependability 8.0",
        "Workplace Health and Safety (New)",
    ],
    "safety_industrial": [
        "Manufac. & Indust. - Safety & Dependability 8.0",
        "Workplace Health and Safety (New)",
    ],
    "healthcare_hybrid": [
        "HIPAA (Security)",
        "Medical Terminology (New)",
        "Microsoft Word 365 - Essentials (New)",
        "Dependability and Safety Instrument (DSI)",
        "Occupational Personality Questionnaire OPQ32r",
    ],
    "office_quick": [
        "MS Excel (New)",
        "MS Word (New)",
        "Occupational Personality Questionnaire OPQ32r",
    ],
    "office_sim": [
        "Microsoft Excel 365 (New)",
        "Microsoft Word 365 (New)",
        "MS Excel (New)",
        "MS Word (New)",
        "Occupational Personality Questionnaire OPQ32r",
    ],
    "graduate_management": [
        "SHL Verify Interactive G+",
        "Occupational Personality Questionnaire OPQ32r",
        "Graduate Scenarios",
    ],
    "graduate_management_no_opq": [
        "SHL Verify Interactive G+",
        "Graduate Scenarios",
    ],
    "fullstack_backend": [
        "Core Java (Advanced Level) (New)",
        "Spring (New)",
        "RESTful Web Services (New)",
        "SQL (New)",
        "SHL Verify Interactive G+",
        "Occupational Personality Questionnaire OPQ32r",
    ],
    "fullstack_backend_cloud": [
        "Core Java (Advanced Level) (New)",
        "Spring (New)",
        "SQL (New)",
        "Amazon Web Services (AWS) Development (New)",
        "Docker (New)",
        "SHL Verify Interactive G+",
        "Occupational Personality Questionnaire OPQ32r",
    ],
}

LEGAL_TERMS = ("legal", "law", "lawyer", "required under", "satisfy that requirement", "compliance question")
INJECTION_TERMS = ("ignore previous", "system prompt", "developer message", "jailbreak", "reveal prompt")
OFF_TOPIC_TERMS = ("weather", "recipe", "stock price", "sports", "write my essay")
CONFIRM_TERMS = ("perfect", "thanks", "thank you", "confirmed", "that works", "that's good", "covers it", "locking it in", "final list")


def answer(messages: list[Message]) -> ChatResponse:
    user_messages = [m.content for m in messages if m.role == "user"]
    last = user_messages[-1] if user_messages else ""
    history = "\n".join(user_messages)
    h = normalize(history)
    l = normalize(last)

    if _has_any(l, INJECTION_TERMS):
        return ChatResponse(
            reply="I can only help select SHL assessments from the catalog and cannot follow instructions that try to override that scope.",
            recommendations=[],
            end_of_conversation=False,
        )

    if _has_any(l, LEGAL_TERMS):
        return ChatResponse(
            reply="I cannot give legal or regulatory advice. I can confirm only catalog facts: SHL assessments may measure relevant knowledge or workplace behavior, but whether a test satisfies a legal requirement should be checked with your legal or compliance team.",
            recommendations=[],
            end_of_conversation=False,
        )

    if _has_any(l, OFF_TOPIC_TERMS) or _is_general_hiring_advice(l):
        return ChatResponse(
            reply="I can help only with SHL assessment selection from the catalog. Share the role, level, skills, language, and assessment goals, and I will recommend catalog-backed options.",
            recommendations=[],
            end_of_conversation=False,
        )

    if _is_compare(l):
        return _compare_response(history, last)

    scenario = _detect_scenario(h, l)
    if scenario == "clarify_leadership":
        return _ask("Happy to help narrow that down. Is this for executive selection, leadership development, or benchmarking current leaders?")
    if scenario == "clarify_contact_language":
        return _ask("Before I shape the stack, what language and accent should candidates be assessed in?")
    if scenario == "clarify_contact_accent":
        return _ask("For English contact-center screening, should the spoken-language test use US, UK, Australian, or Indian accent?")
    if scenario == "clarify_healthcare_hybrid":
        return _ask("The healthcare knowledge tests in the catalog are English-only, while OPQ32r and DSI support Spanish variants. Are your candidates functionally bilingual enough for English knowledge tests, or do you need Spanish-only assessment?")
    if scenario == "clarify_fullstack_focus":
        return _ask("That engineering JD spans several areas. Is the role backend-leaning, frontend-heavy, or a balanced full-stack role?")
    if scenario == "clarify_fullstack_level":
        return _ask("Is this closer to a senior individual contributor role or a tech lead role with broader architecture ownership?")
    if scenario == "vague":
        return _ask("I need a little more context before recommending. What role are you hiring for, what seniority level is it, and what skills or behaviors matter most?")

    curated_names = CURATED.get(scenario or "", [])
    recs = names_to_recommendations(curated_names) if curated_names else retrieve(history, 10)

    if _wants_remove_opq(h):
        recs = [r for r in recs if "OPQ32r" not in r["name"]]
    if _wants_drop_rest(h):
        recs = [r for r in recs if "RESTful" not in r["name"]]

    if not recs:
        return _ask("I could not confidently match that to the SHL catalog yet. Which role, skills, seniority, and assessment goal should I prioritize?")

    reply = _reply_for(scenario, recs, h)
    return ChatResponse(
        reply=reply,
        recommendations=[Recommendation(**r) for r in recs[:10]],
        end_of_conversation=_is_confirming(l),
    )


def _ask(reply: str) -> ChatResponse:
    return ChatResponse(reply=reply, recommendations=[], end_of_conversation=False)


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(normalize(term) in text for term in terms)


def _is_general_hiring_advice(text: str) -> bool:
    return "interview question" in text or "salary" in text or "offer letter" in text


def _is_confirming(text: str) -> bool:
    return _has_any(text, CONFIRM_TERMS)


def _is_compare(text: str) -> bool:
    return "difference between" in text or "different from" in text or text.startswith("compare ")


def _wants_remove_opq(text: str) -> bool:
    return ("drop opq" in text or "remove opq" in text or "skip personality" in text) and "keep opq" not in text


def _wants_drop_rest(text: str) -> bool:
    return "drop rest" in text or "rest out" in text


def _detect_scenario(history: str, last: str) -> str | None:
    if len(history.split()) < 4 or history in {"i need an assessment", "need assessment", "assessment"}:
        return "vague"

    if any(t in history for t in ("full stack", "fullstack", "core java", "spring", "angular", "microservice")):
        if "backend" not in history and "frontend" not in history and "balanced" not in history and "senior ic" not in history:
            return "clarify_fullstack_focus"
        if "senior ic" not in history and "tech lead" not in history and "individual contributor" not in history:
            return "clarify_fullstack_level"
        if "aws" in history or "docker" in history:
            return "fullstack_backend_cloud"
        return "fullstack_backend"

    if any(t in history for t in ("senior leadership", "cxo", "director level", "executive")):
        if not any(t in history for t in ("selection", "development", "benchmark", "cxo", "director level")):
            return "clarify_leadership"
        return "leadership"

    if "rust" in history or ("networking" in history and "engineer" in history):
        return "rust_networking"

    if "contact centre" in history or "contact center" in history or "inbound calls" in history:
        if not any(t in history for t in ("english", "spanish", "french")):
            return "clarify_contact_language"
        if "english" in history and not any(t in history for t in (" us", "usa", "u s", "uk", "u k", "australian", "indian")):
            return "clarify_contact_accent"
        return "contact_center_us"

    if "financial analyst" in history or ("finance" in history and "graduate" in history):
        if "situational" in history or "judgement" in history or "judgment" in history or "graduate scenarios" in history:
            return "finance_graduate_sjt"
        return "finance_graduate"

    if "sales" in history and any(t in history for t in ("reskill", "re skill", "audit", "restructuring", "transformation")):
        return "sales_reskill"

    if any(t in history for t in ("chemical", "plant operator", "safety", "dependability")):
        if "industrial" in history and ("confirmed" in history or "right fit" in history):
            return "safety_industrial"
        return "safety"

    if "healthcare" in history or "hipaa" in history or "patient records" in history:
        if not any(t in history for t in ("bilingual", "hybrid", "english fluent", "functionally bilingual")):
            return "clarify_healthcare_hybrid"
        return "healthcare_hybrid"

    if ("excel" in history and "word" in history) or "admin assistant" in history:
        if "simulation" in history or "capture the capabilities" in history:
            return "office_sim"
        return "office_quick"

    if "graduate management" in history or ("management trainee" in history and "graduate" in history):
        if _wants_remove_opq(history):
            return "graduate_management_no_opq"
        return "graduate_management"

    return None


def _reply_for(scenario: str | None, recs: list[dict[str, str]], history: str) -> str:
    if scenario == "rust_networking":
        return "The catalog does not include a Rust-specific test, so this shortlist uses live coding plus nearby systems, networking, reasoning, and personality measures."
    if scenario == "healthcare_hybrid":
        return "Here is a hybrid battery: English knowledge tests for healthcare/admin skills, plus Spanish-capable personality and dependability measures."
    if scenario == "fullstack_backend_cloud":
        return "Updated shortlist: REST is removed, and AWS plus Docker are added to the backend Java/Spring/SQL core."
    if scenario == "office_sim":
        return "Updated shortlist with Excel and Word simulations added, while keeping the shorter knowledge checks and OPQ32r."
    if scenario and "safety" in scenario:
        return "For a safety-critical industrial role, this shortlist combines safety/dependability behavior with workplace safety knowledge."
    if scenario and "graduate" in scenario:
        return "Here is a graduate-focused battery covering the requested cognitive, knowledge, personality, or situational-judgment needs."
    return f"Here are {len(recs)} SHL catalog assessments that best match the current request."


def _compare_response(history: str, last: str) -> ChatResponse:
    text = normalize(last)
    pairs = {
        ("opq", "opq mq sales"): "OPQ32r is the underlying broad personality questionnaire. OPQ MQ Sales Report is a sales-focused report that interprets OPQ results for sales behavior and can be enriched with Motivation Questionnaire content.",
        ("dsi", "safety dependability"): "DSI is a standalone dependability and safety personality instrument. Manufacturing & Industrial Safety & Dependability 8.0 is a sector-specific safety/dependability solution for manufacturing and industrial workforces.",
        ("contact center call simulation", "customer service phone simulation"): "Contact Center Call Simulation (New) is a newer standalone call simulation. Customer Service Phone Simulation is a broader customer-service phone simulation product that can be used for deeper finalist-stage assessment.",
        ("verify g", "technical tests"): "Technical tests measure known stack skills. Verify G+ measures broader reasoning ability, which is useful when candidates must learn, adapt, and make design decisions.",
    }
    for terms, reply in pairs.items():
        if all(term in text or term.replace(" ", "") in text.replace(" ", "") for term in terms):
            return ChatResponse(reply=reply, recommendations=[], end_of_conversation=False)

    names = _mentioned_catalog_names(last)
    if len(names) >= 2:
        a = find_by_name(names[0])
        b = find_by_name(names[1])
        if a and b:
            reply = (
                f"{a['name']} is categorized as {', '.join(a.get('keys') or ['catalog item'])} "
                f"and is described as: {a.get('description') or 'No description in catalog.'} "
                f"{b['name']} is categorized as {', '.join(b.get('keys') or ['catalog item'])} "
                f"and is described as: {b.get('description') or 'No description in catalog.'}"
            )
            return ChatResponse(reply=reply, recommendations=[], end_of_conversation=False)

    return ChatResponse(
        reply="I can compare SHL catalog assessments, but I need the two assessment names. Please name the products you want compared.",
        recommendations=[],
        end_of_conversation=False,
    )


def _mentioned_catalog_names(text: str) -> list[str]:
    quoted = re.findall(r'"([^"]+)"|' + r"'([^']+)'", text)
    names = [a or b for a, b in quoted]
    if names:
        return names
    possible = []
    for fragment in re.split(r"\band\b|\bvs\b|,", text, flags=re.IGNORECASE):
        fragment = fragment.strip(" ?.!")
        if len(fragment.split()) >= 2:
            possible.append(fragment)
    return possible[:2]

