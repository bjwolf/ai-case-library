"""Ranking engine with weighted scoring and rule-based AI analysis."""
from sqlalchemy.orm import Session
from app.models import Case
from app.analytics import get_summary


def normalize(value, max_val):
    """Normalize a value to 0-100 scale."""
    if not value or not max_val or max_val == 0:
        return 0
    return min(100, (value / max_val) * 100)


def compute_scores(cases, impact_w=40, scalability_w=25, effort_w=20, innovation_w=15):
    """Compute composite scores for all cases."""
    if not cases:
        return []

    # Find max values for normalization
    max_time = max((c.time_saved or 0) for c in cases) or 1
    max_cost = max((c.cost_reduction or 0) for c in cases) or 1
    max_acc = max((c.accuracy or 0) for c in cases) or 1
    max_usd = max((c.yearly_usd_saved or 0) for c in cases) or 1
    max_roi = max(((c.yearly_usd_saved or 0) / max(c.dev_time_hours or 1, 1)) for c in cases) or 1

    total_w = impact_w + scalability_w + effort_w + innovation_w
    results = []

    for c in cases:
        # Impact: avg of normalized metrics
        impact = (
            normalize(c.time_saved, max_time) +
            normalize(c.cost_reduction, max_cost) +
            normalize(c.accuracy, max_acc) +
            normalize(c.yearly_usd_saved, max_usd)
        ) / 4

        # Scalability: user-rated 1-10 scaled to 0-100
        scalability = (c.scalability_score or 5) * 10

        # Effort efficiency: ROI per dev hour
        roi = (c.yearly_usd_saved or 0) / max(c.dev_time_hours or 1, 1)
        effort = normalize(roi, max_roi)

        # Innovation: user-rated 1-10 scaled to 0-100
        innovation = (c.innovation_score or 5) * 10

        composite = (
            impact * (impact_w / total_w) +
            scalability * (scalability_w / total_w) +
            effort * (effort_w / total_w) +
            innovation * (innovation_w / total_w)
        )

        results.append({
            "id": c.id,
            "use_case_title": c.use_case_title,
            "owner_login": c.owner_login,
            "program_team": c.program_team,
            "ai_technique": c.ai_technique,
            "status": c.status,
            "composite_score": round(composite, 1),
            "impact_score": round(impact, 1),
            "scalability_score_calc": round(scalability, 1),
            "effort_score": round(effort, 1),
            "innovation_score_calc": round(innovation, 1),
            # Raw metrics for display
            "time_saved": c.time_saved,
            "cost_reduction": c.cost_reduction,
            "accuracy": c.accuracy,
            "yearly_usd_saved": c.yearly_usd_saved,
            "yearly_hc_saved": c.yearly_hc_saved,
            "dev_time_hours": c.dev_time_hours,
            "scalability_score": c.scalability_score,
            "innovation_score": c.innovation_score,
        })

    results.sort(key=lambda x: x["composite_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results


def get_rankings(db: Session, impact_w=40, scalability_w=25, effort_w=20, innovation_w=15):
    cases = db.query(Case).all()
    return compute_scores(cases, impact_w, scalability_w, effort_w, innovation_w)


def generate_ai_analysis(case_data, summary, all_rankings):
    """Rule-based AI analysis. Replace with Bedrock call when credentials available."""
    strengths = []
    weaknesses = []
    suggestions = []
    risks = []

    avg_time = summary.get("avg_time_saved", 0)
    avg_cost = summary.get("avg_cost_reduction", 0)
    avg_acc = summary.get("avg_accuracy", 0)
    rank = case_data.get("rank", 0)
    total = len(all_rankings)

    # Strengths
    if (case_data.get("time_saved") or 0) > avg_time:
        strengths.append(f"Time savings ({case_data['time_saved']}%) exceeds library average ({avg_time}%)")
    if (case_data.get("cost_reduction") or 0) > avg_cost:
        strengths.append(f"Cost reduction ({case_data['cost_reduction']}%) above average ({avg_cost}%)")
    if (case_data.get("accuracy") or 0) > avg_acc:
        strengths.append(f"Accuracy ({case_data['accuracy']}%) above average ({avg_acc}%)")
    if (case_data.get("yearly_usd_saved") or 0) > 500000:
        strengths.append(f"High financial impact: ${case_data['yearly_usd_saved']:,.0f} yearly savings")
    if (case_data.get("scalability_score") or 0) >= 8:
        strengths.append("High scalability potential — reusable across teams")
    if (case_data.get("innovation_score") or 0) >= 8:
        strengths.append("Highly innovative approach")
    if rank <= 3:
        strengths.append(f"Top performer — ranked #{rank} out of {total} initiatives")
    if not strengths:
        strengths.append("Solid initiative with room for growth")

    # Weaknesses
    if (case_data.get("time_saved") or 0) < avg_time and case_data.get("time_saved") is not None:
        weaknesses.append(f"Time savings ({case_data['time_saved']}%) below library average ({avg_time}%)")
    if (case_data.get("accuracy") or 0) < avg_acc and case_data.get("accuracy") is not None:
        weaknesses.append(f"Accuracy ({case_data['accuracy']}%) below average ({avg_acc}%)")
    if (case_data.get("dev_time_hours") or 0) > 150:
        weaknesses.append(f"High development effort ({case_data['dev_time_hours']}h) — consider phased delivery")
    if (case_data.get("scalability_score") or 0) < 5:
        weaknesses.append("Low scalability — limited reuse potential across teams")
    if not weaknesses:
        weaknesses.append("No significant weaknesses identified")

    # Suggestions
    if (case_data.get("accuracy") or 0) < 90:
        suggestions.append("Consider additional training data or model tuning to improve accuracy above 90%")
    if (case_data.get("yearly_usd_saved") or 0) < 200000:
        suggestions.append("Explore expanding scope to additional use cases to increase financial impact")
    if (case_data.get("scalability_score") or 0) < 7:
        suggestions.append("Document the solution as a reusable template for other teams")
    if case_data.get("status") == "Developing":
        suggestions.append("Prioritize moving to UAT to validate with real users")
    if case_data.get("status") == "UAT":
        suggestions.append("Gather user feedback and prepare production deployment plan")
    roi = (case_data.get("yearly_usd_saved") or 0) / max(case_data.get("dev_time_hours") or 1, 1)
    if roi < 1000:
        suggestions.append("ROI per dev hour is low — consider reducing scope or automating more of the pipeline")
    if not suggestions:
        suggestions.append("Continue current trajectory — strong performance across all metrics")

    # Risks
    if case_data.get("accuracy") is None:
        risks.append("No accuracy metric reported — difficult to assess quality")
    if (case_data.get("dev_time_hours") or 0) > 200:
        risks.append("Extended development timeline increases risk of scope creep")
    if (case_data.get("yearly_hc_saved") or 0) > 5:
        risks.append("High HC displacement — ensure change management plan is in place")
    if case_data.get("status") == "Developing" and (case_data.get("dev_time_hours") or 0) > 100:
        risks.append("Still in development with significant hours invested — monitor for delivery risk")
    if not risks:
        risks.append("Low risk profile — well-positioned for success")

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "risks": risks,
        "summary": f"Ranked #{rank} of {total}. Composite score: {case_data.get('composite_score', 0)}/100.",
    }
