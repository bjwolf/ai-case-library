"""AI Solution Design Agent with keyword-based similarity matching."""
import uuid
import re
from collections import Counter
from sqlalchemy.orm import Session
from app.models import Case

# In-memory session store
_sessions = {}

STOP_WORDS = {"the","a","an","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","shall","can",
    "for","and","nor","but","or","yet","so","in","on","at","to","of","with","by","from",
    "as","into","through","during","before","after","above","below","between","out",
    "off","over","under","again","further","then","once","here","there","when","where",
    "why","how","all","each","every","both","few","more","most","other","some","such",
    "no","not","only","own","same","than","too","very","just","because","about","up",
    "it","its","i","we","they","them","our","my","your","this","that","these","those","what"}


def tokenize(text):
    if not text:
        return []
    words = re.findall(r'[a-z0-9]+', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def score_case(query_tokens, case):
    """Score a case against query tokens with field weighting."""
    fields = [
        (case.problem_statement, 3),
        (case.use_case_title, 2),
        (case.solution_description, 2),
        (case.ai_technique, 2),
        (case.tools_services, 1),
        (case.output_outcome, 1),
        (case.key_prompts, 1),
    ]
    query_set = set(query_tokens)
    total = 0
    for text, weight in fields:
        tokens = set(tokenize(text))
        overlap = len(query_set & tokens)
        total += overlap * weight
    return total


def find_similar_cases(db: Session, query: str, top_k: int = 5):
    """Find top-K similar cases using keyword matching."""
    cases = db.query(Case).all()
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    scored = [(case, score_case(query_tokens, case)) for case in cases]
    scored = [(c, s) for c, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def generate_design(query: str, matched_cases):
    """Generate a solution design from matched cases."""
    if not matched_cases:
        return {
            "recommendation": "No similar cases found in the library. Try describing your problem with more detail about the AI technique, data type, or business domain.",
            "technique": None,
            "tools": None,
            "estimated_effort_hours": None,
            "expected_outcomes": None,
            "implementation_steps": [],
            "matched_cases": [],
        }

    # Aggregate insights from matched cases
    techniques = Counter()
    tools = Counter()
    dev_hours = []
    outcomes = []
    case_refs = []

    for case, score in matched_cases:
        if case.ai_technique:
            techniques[case.ai_technique] += score
        if case.tools_services:
            for tool in case.tools_services.split(","):
                tools[tool.strip()] += score
        if case.dev_time_hours:
            dev_hours.append(case.dev_time_hours)
        if case.output_outcome:
            outcomes.append(case.output_outcome)
        case_refs.append({
            "id": case.id,
            "title": case.use_case_title,
            "program": case.program_team,
            "technique": case.ai_technique,
            "similarity_score": score,
            "time_saved": case.time_saved,
            "accuracy": case.accuracy,
            "yearly_usd_saved": case.yearly_usd_saved,
        })

    top_technique = techniques.most_common(1)[0][0] if techniques else "General ML"
    top_tools = [t for t, _ in tools.most_common(5)]
    avg_hours = round(sum(dev_hours) / len(dev_hours)) if dev_hours else None

    # Generate implementation steps based on technique
    steps = generate_steps(top_technique, top_tools, query)

    recommendation = (
        f"Based on {len(matched_cases)} similar initiatives in the library, "
        f"we recommend using **{top_technique}** as the primary AI technique. "
    )
    if top_tools:
        recommendation += f"Key tools: {', '.join(top_tools[:3])}. "
    if avg_hours:
        recommendation += f"Estimated development effort: ~{avg_hours} hours. "
    if outcomes:
        recommendation += f"Similar initiatives achieved: {outcomes[0]}"

    return {
        "recommendation": recommendation,
        "technique": top_technique,
        "tools": top_tools[:5],
        "estimated_effort_hours": avg_hours,
        "expected_outcomes": outcomes[:3],
        "implementation_steps": steps,
        "matched_cases": case_refs,
    }


def generate_steps(technique, tools, query):
    """Generate implementation steps based on technique."""
    base_steps = [
        "1. Define success metrics and acceptance criteria",
        "2. Collect and prepare training/input data",
        "3. Set up development environment and tools",
    ]
    technique_steps = {
        "NLP Text Classification": [
            "4. Label training data with target categories",
            "5. Train classification model (fine-tune or use pre-trained)",
            "6. Evaluate model accuracy on held-out test set",
            "7. Build inference pipeline with API endpoint",
        ],
        "Time Series Forecasting": [
            "4. Clean and normalize historical time series data",
            "5. Feature engineering (seasonality, trends, external factors)",
            "6. Train forecasting model (Prophet, ARIMA, or ML-based)",
            "7. Validate predictions against historical actuals",
        ],
        "Generative AI (LLM)": [
            "4. Design prompt templates for target use case",
            "5. Select and configure LLM (Bedrock Claude, GPT, etc.)",
            "6. Build prompt pipeline with input validation",
            "7. Implement output quality checks and guardrails",
        ],
        "Computer Vision": [
            "4. Collect and annotate image/video training data",
            "5. Train or fine-tune vision model (detection, classification)",
            "6. Optimize model for inference speed",
            "7. Build image processing pipeline",
        ],
        "Reinforcement Learning": [
            "4. Define environment, state space, and reward function",
            "5. Implement simulation environment for training",
            "6. Train RL agent with iterative reward optimization",
            "7. Validate agent behavior in simulated scenarios",
        ],
        "Anomaly Detection": [
            "4. Establish baseline patterns from historical normal data",
            "5. Train anomaly detection model (isolation forest, autoencoder)",
            "6. Tune detection thresholds to balance precision/recall",
            "7. Build alerting pipeline for detected anomalies",
        ],
        "Recommendation Systems": [
            "4. Build user-item interaction matrix from historical data",
            "5. Train collaborative/content-based recommendation model",
            "6. Implement real-time recommendation serving",
            "7. A/B test recommendations against baseline",
        ],
    }
    mid_steps = technique_steps.get(technique, [
        "4. Select and configure appropriate ML model",
        "5. Train model on prepared data",
        "6. Evaluate model performance",
        "7. Build inference pipeline",
    ])
    end_steps = [
        f"{len(base_steps) + len(mid_steps) + 1}. Deploy to UAT environment and gather user feedback",
        f"{len(base_steps) + len(mid_steps) + 2}. Monitor performance metrics and iterate",
        f"{len(base_steps) + len(mid_steps) + 3}. Production deployment with monitoring and alerting",
    ]
    return base_steps + mid_steps + end_steps


def handle_design_query(db: Session, query: str, session_id: str = None):
    """Main entry point for design queries."""
    if not session_id:
        session_id = str(uuid.uuid4())

    matched = find_similar_cases(db, query)
    design = generate_design(query, matched)

    _sessions[session_id] = {"query": query, "design": design, "history": [query]}
    return {"session_id": session_id, "design": design}


def handle_followup(db: Session, session_id: str, question: str):
    """Handle follow-up questions within a session."""
    session = _sessions.get(session_id)
    if not session:
        return {"error": "Session not found. Start a new conversation."}

    session["history"].append(question)
    combined_query = session["query"] + " " + question
    matched = find_similar_cases(db, combined_query)
    design = generate_design(combined_query, matched)

    # Generate contextual answer
    answer = generate_followup_answer(question, design, session)
    session["design"] = design
    return {"session_id": session_id, "answer": answer, "updated_design": design}


def generate_followup_answer(question, design, session):
    """Generate a contextual answer to a follow-up question."""
    q = question.lower()
    if any(w in q for w in ["cost", "budget", "price", "expensive"]):
        hours = design.get("estimated_effort_hours") or "unknown"
        return f"Based on similar initiatives, estimated effort is ~{hours} hours. Primary tools: {', '.join(design.get('tools', [])[:3])}. Consider starting with a POC to validate before full investment."
    if any(w in q for w in ["scale", "scaling", "grow", "expand"]):
        return "To scale this solution: 1) Containerize the inference pipeline, 2) Use auto-scaling compute (e.g., SageMaker endpoints), 3) Implement caching for repeated queries, 4) Monitor latency and throughput metrics."
    if any(w in q for w in ["time", "timeline", "long", "duration", "fast"]):
        hours = design.get("estimated_effort_hours") or "unknown"
        return f"Estimated ~{hours} hours of development. Recommend a phased approach: POC in 2-4 weeks, UAT in 2 weeks, production in 1-2 weeks."
    if any(w in q for w in ["risk", "challenge", "difficult", "problem"]):
        return "Key risks: 1) Data quality — ensure clean, representative training data, 2) Model drift — plan for retraining cadence, 3) Integration complexity — start with simple API interface, 4) User adoption — involve end users early in UAT."
    if any(w in q for w in ["team", "skill", "people", "resource"]):
        return "Recommended team: 1 ML engineer, 1 data engineer, 1 domain expert (part-time). For LLM-based solutions, prompt engineering skills are key. Consider upskilling existing team via internal AI training programs."
    return f"Based on the matched cases and your question about '{question}', the recommended approach using {design.get('technique', 'ML')} remains solid. The implementation steps in the design cover this area. Would you like to explore a specific aspect in more detail?"
