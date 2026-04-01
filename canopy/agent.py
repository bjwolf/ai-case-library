"""AI Solution Design Agent — keyword-based fallback when no LLM available."""
import uuid, re
from collections import Counter

STOP_WORDS = {"the","a","an","is","are","was","were","be","been","have","has","had","do","does","did",
    "will","would","could","should","for","and","nor","but","or","yet","so","in","on","at","to","of",
    "with","by","from","as","into","through","not","only","this","that","what","how","all","each"}

_sessions = {}

def tokenize(text):
    if not text: return []
    return [w for w in re.findall(r'[a-z0-9]+', text.lower()) if w not in STOP_WORDS and len(w) > 2]

def score_case(tokens, case):
    qset = set(tokens)
    total = 0
    for field, weight in [("problem_statement",3),("use_case_title",2),("solution_description",2),("ai_technique",2),("tools_services",1)]:
        total += len(qset & set(tokenize(case.get(field,"")))) * weight
    return total

def handle_design(query, cases):
    tokens = tokenize(query)
    scored = [(c, score_case(tokens, c)) for c in cases]
    scored = [(c, s) for c, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    matched = scored[:5]
    if not matched:
        return {"session_id": str(uuid.uuid4()), "design": {
            "recommendation": "No similar cases found. Try more detail about AI technique or business domain.",
            "technique": None, "tools": [], "estimated_effort_hours": None,
            "implementation_steps": [], "matched_cases": []}}
    techniques = Counter()
    tools = Counter()
    hours = []
    refs = []
    for c, s in matched:
        if c.get("ai_technique"): techniques[c["ai_technique"]] += s
        if c.get("tools_services"):
            for t in c["tools_services"].split(","): tools[t.strip()] += s
        if c.get("dev_time_hours"): hours.append(c["dev_time_hours"])
        refs.append({"title": c.get("use_case_title"), "technique": c.get("ai_technique"),
                      "yearly_usd_saved": c.get("yearly_usd_saved"), "similarity": s})
    tech = techniques.most_common(1)[0][0] if techniques else "General ML"
    top_tools = [t for t, _ in tools.most_common(5)]
    avg_h = round(sum(hours)/len(hours)) if hours else None
    rec = f"Based on {len(matched)} similar initiatives, recommend **{tech}**."
    if top_tools: rec += f" Tools: {', '.join(top_tools[:3])}."
    if avg_h: rec += f" Estimated ~{avg_h} hours."
    steps = ["Define success metrics","Collect and prepare data","Set up environment",
             f"Implement {tech} pipeline","Train/configure model","Evaluate performance",
             "Build API/interface","Deploy to UAT","Gather feedback","Production deployment"]
    sid = str(uuid.uuid4())
    _sessions[sid] = {"query": query}
    return {"session_id": sid, "design": {"recommendation": rec, "technique": tech,
        "tools": top_tools, "estimated_effort_hours": avg_h,
        "implementation_steps": steps, "matched_cases": refs}}

def handle_followup_local(sid, question, cases):
    q = question.lower()
    if any(w in q for w in ["cost","budget","price"]): answer = "Consider starting with a POC to validate before full investment."
    elif any(w in q for w in ["scale","grow"]): answer = "Containerize the pipeline, use auto-scaling compute, implement caching."
    elif any(w in q for w in ["time","long","fast"]): answer = "Recommend phased approach: POC 2-4 weeks, UAT 2 weeks, production 1-2 weeks."
    elif any(w in q for w in ["risk","challenge"]): answer = "Key risks: data quality, model drift, integration complexity, user adoption."
    elif any(w in q for w in ["team","skill","people"]): answer = "Recommended: 1 ML engineer, 1 data engineer, 1 domain expert (part-time)."
    else: answer = f"The recommended approach remains solid. Could you be more specific about what aspect you'd like to explore?"
    return {"session_id": sid, "answer": answer}
