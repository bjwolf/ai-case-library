"""Seed the database with sample AI initiative cases."""
from app.database import SessionLocal, engine, Base
from app.models import Case, User
from app.auth import hash_password

Base.metadata.create_all(bind=engine)

SAMPLE_CASES = [
    {
        "owner_login": "jsmith",
        "job_level": "L6",
        "program_team": "Supply Chain",
        "use_case_title": "Demand Forecasting with ML",
        "problem_statement": "Manual demand forecasting is slow and inaccurate, leading to overstock and stockouts.",
        "ai_technique": "Time Series Forecasting",
        "tools_services": "Amazon SageMaker, Prophet",
        "key_prompts": "Predict weekly demand for top 500 SKUs",
        "input_data": "3 years of historical sales data, promotions calendar",
        "output_outcome": "Automated weekly forecasts with 92% accuracy",
        "time_saved": 40.0,
        "yearly_hc_saved": 2.0,
        "accuracy": 92.0,
        "cost_reduction": 15.0,
        "yearly_usd_saved": 150000.0,
        "dev_time_hours": 120.0,
        "status": "In Production",
        "scalability_score": 8.5,
        "innovation_score": 7.0,
    },
    {
        "owner_login": "adoe",
        "job_level": "L5",
        "program_team": "Customer Service",
        "use_case_title": "Automated Ticket Classification",
        "problem_statement": "Support tickets are manually triaged, causing delays in routing to the right team.",
        "ai_technique": "NLP Text Classification",
        "tools_services": "Amazon Comprehend, Lambda",
        "key_prompts": "Classify incoming tickets into 12 categories",
        "input_data": "500K labeled support tickets",
        "output_outcome": "Auto-classification with 88% accuracy, 60% reduction in triage time",
        "time_saved": 60.0,
        "yearly_hc_saved": 5.0,
        "accuracy": 88.0,
        "cost_reduction": 25.0,
        "yearly_usd_saved": 500000.0,
        "dev_time_hours": 80.0,
        "status": "In Production",
        "scalability_score": 9.0,
        "innovation_score": 6.5,
    },
    {
        "owner_login": "bwang",
        "job_level": "L7",
        "program_team": "Operations",
        "use_case_title": "Warehouse Robot Path Optimization",
        "problem_statement": "Warehouse robots follow static paths, causing congestion and inefficiency.",
        "ai_technique": "Reinforcement Learning",
        "tools_services": "Amazon SageMaker RL, RoboMaker",
        "key_prompts": "Optimize pick paths for 200 robots in real-time",
        "input_data": "Warehouse layout, order queue, robot positions",
        "output_outcome": "18% improvement in pick throughput",
        "time_saved": 18.0,
        "yearly_hc_saved": 1.0,
        "accuracy": None,
        "cost_reduction": 12.0,
        "yearly_usd_saved": 200000.0,
        "dev_time_hours": 200.0,
        "status": "UAT",
        "scalability_score": 7.0,
        "innovation_score": 9.5,
    },
    {
        "owner_login": "clee",
        "job_level": "L5",
        "program_team": "Marketing",
        "use_case_title": "AI-Generated Product Descriptions",
        "problem_statement": "Writing product descriptions for 10K new items per month is a bottleneck.",
        "ai_technique": "Generative AI (LLM)",
        "tools_services": "Amazon Bedrock, Claude",
        "key_prompts": "Generate SEO-optimized product descriptions from bullet points and images",
        "input_data": "Product attributes, images, category taxonomy",
        "output_outcome": "Auto-generated descriptions for 80% of new products, 3x faster time-to-market",
        "time_saved": 70.0,
        "yearly_hc_saved": 8.0,
        "accuracy": 85.0,
        "cost_reduction": 30.0,
        "yearly_usd_saved": 800000.0,
        "dev_time_hours": 60.0,
        "status": "Developing",
        "scalability_score": 9.5,
        "innovation_score": 8.0,
    },
    {
        "owner_login": "dkim",
        "job_level": "L6",
        "program_team": "Finance",
        "use_case_title": "Invoice Anomaly Detection",
        "problem_statement": "Fraudulent or erroneous invoices slip through manual review processes.",
        "ai_technique": "Anomaly Detection",
        "tools_services": "Amazon SageMaker, XGBoost",
        "key_prompts": "Flag invoices with anomalous amounts, vendors, or patterns",
        "input_data": "2M historical invoices with fraud labels",
        "output_outcome": "Caught 95% of anomalous invoices, saving $2M annually",
        "time_saved": 50.0,
        "yearly_hc_saved": 3.0,
        "accuracy": 95.0,
        "cost_reduction": 40.0,
        "yearly_usd_saved": 2000000.0,
        "dev_time_hours": 150.0,
        "status": "In Production",
        "scalability_score": 8.0,
        "innovation_score": 7.5,
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(Case).count()
        if existing > 0:
            print(f"Database already has {existing} cases. Skipping seed.")
            return

        # Create default admin user
        if not db.query(User).filter(User.login == "admin").first():
            admin = User(
                login="admin", email="admin@example.com", display_name="Admin",
                hashed_password=hash_password("admin123"), role="admin",
            )
            db.add(admin)
            print("Created admin user (login: admin, password: admin123)")

        for data in SAMPLE_CASES:
            db.add(Case(**data))
        db.commit()
        print(f"Seeded {len(SAMPLE_CASES)} sample cases.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
