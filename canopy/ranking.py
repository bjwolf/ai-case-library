"""Ranking engine and AI analysis."""

def compute_rankings(cases, impact_w=40, scalability_w=25, effort_w=20, innovation_w=15):
    if not cases: return []
    def safe(c, f): v = c.get(f); return float(v) if v is not None else 0
    max_time = max((safe(c,"time_saved") for c in cases), default=1) or 1
    max_cost = max((safe(c,"cost_reduction") for c in cases), default=1) or 1
    max_acc = max((safe(c,"accuracy") for c in cases), default=1) or 1
    max_usd = max((safe(c,"yearly_usd_saved") for c in cases), default=1) or 1
    max_roi = max(((safe(c,"yearly_usd_saved")/max(safe(c,"dev_time_hours"),1)) for c in cases), default=1) or 1
    total_w = impact_w + scalability_w + effort_w + innovation_w
    results = []
    for c in cases:
        norm = lambda v, m: min(100, (v/m)*100) if m else 0
        impact = (norm(safe(c,"time_saved"),max_time)+norm(safe(c,"cost_reduction"),max_cost)+norm(safe(c,"accuracy"),max_acc)+norm(safe(c,"yearly_usd_saved"),max_usd))/4
        scalability = safe(c,"scalability_score")*10 or 50
        roi = safe(c,"yearly_usd_saved")/max(safe(c,"dev_time_hours"),1)
        effort = norm(roi, max_roi)
        innovation = safe(c,"innovation_score")*10 or 50
        composite = impact*(impact_w/total_w)+scalability*(scalability_w/total_w)+effort*(effort_w/total_w)+innovation*(innovation_w/total_w)
        results.append({**c, "composite_score":round(composite,1), "impact_score":round(impact,1),
            "scalability_score_calc":round(scalability,1), "effort_score":round(effort,1), "innovation_score_calc":round(innovation,1)})
    results.sort(key=lambda x: x["composite_score"], reverse=True)
    for i, r in enumerate(results): r["rank"] = i+1
    return results

def generate_analysis(case_data, summary, all_rankings):
    strengths, weaknesses, suggestions, risks = [], [], [], []
    avg_t, avg_c, avg_a = summary.get("avg_time_saved",0), summary.get("avg_cost_reduction",0), summary.get("avg_accuracy",0)
    rank, total = case_data.get("rank",0), len(all_rankings)
    if (case_data.get("time_saved") or 0) > avg_t: strengths.append(f"Time savings ({case_data['time_saved']}%) exceeds average ({avg_t}%)")
    if (case_data.get("cost_reduction") or 0) > avg_c: strengths.append(f"Cost reduction ({case_data['cost_reduction']}%) above average ({avg_c}%)")
    if (case_data.get("accuracy") or 0) > avg_a: strengths.append(f"Accuracy ({case_data['accuracy']}%) above average ({avg_a}%)")
    if (case_data.get("yearly_usd_saved") or 0) > 500000: strengths.append(f"High financial impact: ${case_data['yearly_usd_saved']:,.0f}/yr")
    if rank <= 3: strengths.append(f"Top performer — ranked #{rank} of {total}")
    if not strengths: strengths.append("Solid initiative with growth potential")
    if (case_data.get("time_saved") or 0) < avg_t and case_data.get("time_saved") is not None: weaknesses.append(f"Time savings below average")
    if (case_data.get("dev_time_hours") or 0) > 150: weaknesses.append("High development effort")
    if not weaknesses: weaknesses.append("No significant weaknesses")
    if (case_data.get("accuracy") or 0) < 90: suggestions.append("Consider additional training data to improve accuracy")
    if case_data.get("status") == "Developing": suggestions.append("Prioritize moving to UAT")
    if not suggestions: suggestions.append("Continue current trajectory")
    if case_data.get("accuracy") is None: risks.append("No accuracy metric reported")
    if (case_data.get("dev_time_hours") or 0) > 200: risks.append("Extended timeline increases scope creep risk")
    if not risks: risks.append("Low risk profile")
    return {"strengths":strengths,"weaknesses":weaknesses,"suggestions":suggestions,"risks":risks,
            "summary":f"Ranked #{rank} of {total}. Score: {case_data.get('composite_score',0)}/100."}
