from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryRule:
    category: str
    keywords: set[str]
    problems: list[str]
    software: list[str]


RULES = [
    CategoryRule(
        category="gym_fitness",
        keywords={"gym", "fitness", "trainer", "membership", "workout"},
        problems=["attendance leakage", "lead follow-up delays", "manual subscription renewals"],
        software=["membership CRM", "attendance automation", "whatsapp follow-up workflows"],
    ),
    CategoryRule(
        category="distributor_wholesale",
        keywords={"distributor", "wholesale", "stock", "inventory", "logistics"},
        problems=["inventory mismatch", "late dispatch visibility", "manual invoice reconciliation"],
        software=["inventory management suite", "order tracking portal", "invoice automation"],
    ),
    CategoryRule(
        category="clinic_healthcare",
        keywords={"clinic", "patient", "doctor", "hospital", "appointment"},
        problems=["appointment scheduling conflicts", "patient follow-up drop-off", "manual reminder process"],
        software=["appointment scheduler", "patient CRM", "automated reminder engine"],
    ),
    CategoryRule(
        category="retail",
        keywords={"retail", "store", "shop", "pos", "counter"},
        problems=["inconsistent stock updates", "slow billing flow", "poor repeat-customer tracking"],
        software=["omnichannel POS", "inventory sync", "customer retention workflows"],
    ),
]


def classify_business(business_type: str, biggest_problem: str, current_process: str) -> tuple[str, list[str], list[str]]:
    haystack = f"{business_type} {biggest_problem} {current_process}".lower()

    best_rule = None
    best_score = -1
    for rule in RULES:
        score = sum(1 for keyword in rule.keywords if keyword in haystack)
        if score > best_score:
            best_score = score
            best_rule = rule

    if not best_rule or best_score <= 0:
        return (
            "general_business",
            ["manual process dependency", "limited operational visibility", "delayed decision cycles"],
            ["workflow automation platform", "business dashboard", "lightweight CRM"],
        )

    return best_rule.category, best_rule.problems, best_rule.software
