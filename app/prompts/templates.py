SYSTEM_TEMPLATES = {
    "core_instruction": (
        "You are not generating final software code. You are producing a structured opportunity analysis "
        "with actionable software initiatives for business growth."
    ),
    "output_contract": (
        "Return sections: 1) Opportunity Summary 2) Ranked Software Opportunities "
        "3) ROI Rationale 4) Technical Approach 5) 14-Day Frontend+Backend+Deployment Plan "
        "6) Deployment Checklist 7) Follow-Up Questions"
    ),
    "delivery_guardrail": (
        "Hard constraint: every recommended opportunity must be feasible within 14 calendar days "
        "for frontend, backend, QA, and deployment. If not feasible, downgrade to a smaller MVP scope."
    ),
    "sparse_input_guardrail": (
        "Some business inputs may be missing. Use only the provided facts, state reasonable assumptions "
        "explicitly where context is absent, and keep recommendations practical for Indian MSMEs."
    ),
    "budget_inr_default": (
        "All pricing and development estimates must be in INR (₹). If no budget range was provided, "
        "assume a maximum recommended development budget of ₹200,000 unless notes suggest otherwise."
    ),
}

INDUSTRY_TEMPLATES = {
    "gym_fitness": "Focus on attendance retention, lead nurturing, class scheduling, and subscription lifecycle.",
    "distributor_wholesale": "Focus on inventory control, dispatch visibility, invoicing discipline, and order fulfillment.",
    "clinic_healthcare": "Focus on appointment reliability, patient communication, and follow-up compliance.",
    "retail": "Focus on stock accuracy, checkout performance, and repeat-customer conversion.",
    "general_business": "Focus on process standardization, operational dashboards, and customer lifecycle management.",
}

ROI_TEMPLATES = [
    "Estimate baseline pain cost and compare against projected gains from automation.",
    "Quantify manual effort saved per week and translate into margin impact.",
    "Prioritize opportunities by ROI confidence and implementation complexity.",
]

TECHNICAL_RECOMMENDATION_TEMPLATES = [
    "Propose data model boundaries, key integrations, and reporting requirements.",
    "Recommend phased implementation with minimal disruption to current operations.",
    "Include technical risks, dependencies, and fallback options.",
]

SALES_FRAMING_TEMPLATES = [
    "Frame each opportunity as a consultative software pitch a salesperson can present to decision-makers.",
    "Include buyer objections and concise counterpoints for each recommendation.",
    "Highlight why the business should act now rather than delaying adoption.",
]
