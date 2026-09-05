"""
Synthetic HR and workforce data generator for Meridian Analytics Group.

Generates a multi-year (2022-01 to 2026-08) HR dataset for a fictional
mid-size company, covering headcount, hiring pipeline, terminations,
compensation history, performance reviews, and engagement surveys.

The data is fully synthetic (Faker-generated names, seeded for
reproducibility) and is meant to feed a dbt project that builds staging
and mart models, which in turn feed a Tableau workforce analytics
dashboard.

Run:
    python generate_hr_data.py

Output:
    ../dbt_project/seeds/raw_*.csv
"""

import csv
import os
import random
from datetime import date, timedelta

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dbt_project", "seeds")
os.makedirs(OUTPUT_DIR, exist_ok=True)

COMPANY_START = date(2022, 1, 1)
DATA_END = date(2026, 8, 31)

DIVISIONS = {
    "Engineering": ["Backend", "Frontend", "Platform", "QA"],
    "Product": ["Product Management", "Product Design"],
    "Sales": ["Enterprise Sales", "SMB Sales", "Sales Development"],
    "Marketing": ["Growth Marketing", "Brand Marketing"],
    "Customer Success": ["Support", "Onboarding"],
    "Operations": ["Facilities", "IT"],
    "Finance": ["Accounting", "FP&A"],
    "People": ["Talent Acquisition", "HR Business Partners"],
}

LEVELS = ["Junior", "Mid", "Senior", "Lead", "Manager", "Director"]
LEVEL_WEIGHTS = [0.22, 0.30, 0.22, 0.12, 0.10, 0.04]

LOCATIONS = [
    ("Bremen", "Germany"),
    ("Berlin", "Germany"),
    ("Munich", "Germany"),
    ("Dubai", "UAE"),
    ("Cairo", "Egypt"),
    ("London", "UK"),
    ("Remote", "Remote"),
]

SOURCE_CHANNELS = ["LinkedIn", "Employee Referral", "Job Board", "Agency", "Career Site"]
TERMINATION_REASONS_VOLUNTARY = ["Better Opportunity", "Relocation", "Career Change", "Return to Study"]
TERMINATION_REASONS_INVOLUNTARY = ["Performance", "Restructuring", "Role Eliminated"]

BASE_SALARY_BY_LEVEL = {
    "Junior": (42000, 55000),
    "Mid": (55000, 72000),
    "Senior": (72000, 95000),
    "Lead": (90000, 110000),
    "Manager": (95000, 120000),
    "Director": (120000, 160000),
}


def daterange_months(start, end):
    months = []
    current = date(start.year, start.month, 1)
    while current <= end:
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months


def random_date(start, end):
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


def build_departments():
    rows = []
    dept_id = 1
    dept_lookup = {}
    for division, depts in DIVISIONS.items():
        for dept in depts:
            rows.append({"department_id": dept_id, "department_name": dept, "division": division})
            dept_lookup[dept] = dept_id
            dept_id += 1
    return rows, dept_lookup


def pick_level():
    return random.choices(LEVELS, weights=LEVEL_WEIGHTS, k=1)[0]


def pick_salary(level):
    lo, hi = BASE_SALARY_BY_LEVEL[level]
    return round(random.uniform(lo, hi), -2)


def build_workforce(dept_rows, dept_lookup, target_headcount=950):
    """
    Simulate month-by-month headcount growth from a 120-person seed company
    up to roughly target_headcount by DATA_END, with hiring, attrition, and
    seasonal hiring slowdowns (Nov-Dec), to give the dashboard real trend
    and seasonality to talk about.
    """
    employees = []
    requisitions = []
    hires = []
    terminations = []
    performance_reviews = []
    compensation_history = []
    engagement_surveys = []

    employee_id_seq = 1
    req_id_seq = 1
    hire_id_seq = 1
    term_id_seq = 1
    review_id_seq = 1
    comp_id_seq = 1
    survey_id_seq = 1

    managers_by_dept = {d["department_name"]: [] for d in dept_rows}
    active_employees = []

    def new_employee(dept_name, hire_date, level=None, is_seed=False):
        nonlocal employee_id_seq, hire_id_seq, req_id_seq, comp_id_seq
        level = level or pick_level()
        gender = random.choice(["Female", "Male"])
        first = fake.first_name_female() if gender == "Female" else fake.first_name_male()
        last = fake.last_name()
        location_city, location_country = random.choice(LOCATIONS)
        salary = pick_salary(level)
        manager_pool = managers_by_dept.get(dept_name, [])
        manager_id = random.choice(manager_pool) if manager_pool and level not in ("Director",) else None

        emp = {
            "employee_id": employee_id_seq,
            "first_name": first,
            "last_name": last,
            "gender": gender,
            "department_id": dept_lookup[dept_name],
            "job_title": f"{level} {dept_name} Specialist" if level in ("Junior", "Mid", "Senior") else f"{level}, {dept_name}",
            "level": level,
            "hire_date": hire_date.isoformat(),
            "location_city": location_city,
            "location_country": location_country,
            "employment_type": random.choices(["Full-time", "Part-time", "Contract"], weights=[0.88, 0.07, 0.05])[0],
            "manager_id": manager_id,
            "base_salary": salary,
        }
        employees.append(emp)

        compensation_history.append({
            "comp_id": comp_id_seq,
            "employee_id": employee_id_seq,
            "effective_date": hire_date.isoformat(),
            "salary": salary,
            "change_reason": "New Hire",
        })
        comp_id_seq += 1

        if level in ("Manager", "Director", "Lead"):
            managers_by_dept.setdefault(dept_name, []).append(employee_id_seq)

        if not is_seed:
            req_open = hire_date - timedelta(days=random.randint(18, 65))
            requisitions.append({
                "requisition_id": req_id_seq,
                "department_id": dept_lookup[dept_name],
                "job_title": emp["job_title"],
                "opened_date": req_open.isoformat(),
                "closed_date": hire_date.isoformat(),
                "status": "Filled",
                "source_channel": random.choices(SOURCE_CHANNELS, weights=[0.35, 0.25, 0.2, 0.1, 0.1])[0],
            })
            hires.append({
                "hire_id": hire_id_seq,
                "requisition_id": req_id_seq,
                "employee_id": employee_id_seq,
                "offer_date": (hire_date - timedelta(days=random.randint(3, 10))).isoformat(),
                "start_date": hire_date.isoformat(),
                "source_channel": requisitions[-1]["source_channel"],
                "signing_bonus": round(random.choice([0, 0, 0, 1500, 2500, 5000]), 2),
            })
            req_id_seq += 1
            hire_id_seq += 1

        active_employees.append(employee_id_seq)
        employee_id_seq += 1
        return employee_id_seq - 1

    # Seed the company with an initial workforce as of COMPANY_START
    seed_count = 120
    dept_names = [d["department_name"] for d in dept_rows]
    # seed leadership first so managers exist before staff
    for dept_name in dept_names:
        new_employee(dept_name, COMPANY_START, level="Director", is_seed=True)
        new_employee(dept_name, COMPANY_START, level="Manager", is_seed=True)
    remaining_seed = seed_count - len(dept_names) * 2
    for _ in range(max(remaining_seed, 0)):
        dept_name = random.choices(dept_names, weights=[3 if "Engineering" in d or "Sales" in d else 1 for d in dept_names])[0]
        new_employee(dept_name, COMPANY_START, is_seed=True)

    # Grow month by month
    months = daterange_months(COMPANY_START, DATA_END)[1:]
    for month_start in months:
        month_end = date(month_start.year + (month_start.month == 12), (month_start.month % 12) + 1, 1) - timedelta(days=1)
        current_headcount = len(active_employees)
        progress = (month_start - COMPANY_START).days / (DATA_END - COMPANY_START).days
        growth_curve_target = 120 + (target_headcount - 120) * min(progress * 1.15, 1.0)
        gap = growth_curve_target - current_headcount

        seasonal_factor = 0.4 if month_start.month in (11, 12) else 1.0
        planned_hires = max(int(gap * 0.35 * seasonal_factor) + random.randint(-2, 4), 0)

        for _ in range(planned_hires):
            dept_name = random.choices(dept_names, weights=[3 if "Engineering" in d or "Sales" in d else 1 for d in dept_names])[0]
            hire_date = random_date(month_start, min(month_end, DATA_END))
            new_employee(dept_name, hire_date)

        # attrition: base monthly rate ~1.1%, with a bump every summer (seasonal voluntary churn)
        monthly_attrition_rate = 0.011 * (1.3 if month_start.month in (6, 7, 8) else 1.0)
        n_terms = int(len(active_employees) * monthly_attrition_rate)
        for _ in range(n_terms):
            if not active_employees:
                break
            emp_id = random.choice(active_employees)
            active_employees.remove(emp_id)
            emp = next(e for e in employees if e["employee_id"] == emp_id)
            term_date = random_date(month_start, min(month_end, DATA_END))
            voluntary = random.random() < 0.72
            reason = random.choice(TERMINATION_REASONS_VOLUNTARY if voluntary else TERMINATION_REASONS_INVOLUNTARY)
            emp["termination_date"] = term_date.isoformat()
            terminations.append({
                "termination_id": term_id_seq,
                "employee_id": emp_id,
                "termination_date": term_date.isoformat(),
                "voluntary": voluntary,
                "reason": reason,
                "exit_survey_score": round(random.uniform(2.0, 9.5), 1) if random.random() < 0.6 else None,
            })
            term_id_seq += 1

        # quarterly-ish performance reviews and comp changes for a sample of active employees
        if month_start.month in (3, 6, 9, 12):
            period_label = f"{month_start.year}-Q{(month_start.month // 3)}"
            for emp_id in active_employees:
                if random.random() < 0.85:
                    rating = round(min(max(random.gauss(3.4, 0.8), 1), 5), 0)
                    performance_reviews.append({
                        "review_id": review_id_seq,
                        "employee_id": emp_id,
                        "review_period": period_label,
                        "rating": int(rating),
                        "review_date": random_date(month_start, min(month_end, DATA_END)).isoformat(),
                    })
                    review_id_seq += 1

                    if rating >= 4 and random.random() < 0.3:
                        emp = next(e for e in employees if e["employee_id"] == emp_id)
                        raise_pct = random.uniform(0.04, 0.12)
                        new_salary = round(emp["base_salary"] * (1 + raise_pct), -2)
                        emp["base_salary"] = new_salary
                        compensation_history.append({
                            "comp_id": comp_id_seq,
                            "employee_id": emp_id,
                            "effective_date": month_end.isoformat(),
                            "salary": new_salary,
                            "change_reason": random.choice(["Merit", "Merit", "Promotion"]),
                        })
                        comp_id_seq += 1

        # semi-annual engagement survey (Apr and Oct)
        if month_start.month in (4, 10):
            survey_wave = f"{month_start.year}-{'Spring' if month_start.month == 4 else 'Fall'}"
            for emp_id in active_employees:
                if random.random() < 0.68:
                    engagement_surveys.append({
                        "survey_id": survey_id_seq,
                        "employee_id": emp_id,
                        "survey_wave": survey_wave,
                        "survey_date": random_date(month_start, min(month_end, DATA_END)).isoformat(),
                        "engagement_score": round(random.uniform(3.5, 9.8), 1),
                        "satisfaction_score": round(random.uniform(3.0, 9.8), 1),
                    })
                    survey_id_seq += 1

    return {
        "employees": employees,
        "requisitions": requisitions,
        "hires": hires,
        "terminations": terminations,
        "performance_reviews": performance_reviews,
        "compensation_history": compensation_history,
        "engagement_surveys": engagement_surveys,
    }


def write_csv(rows, filename, fieldnames):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Wrote {len(rows):>6} rows to {filename}")


def main():
    dept_rows, dept_lookup = build_departments()
    data = build_workforce(dept_rows, dept_lookup)

    write_csv(dept_rows, "raw_departments.csv", ["department_id", "department_name", "division"])

    write_csv(
        data["employees"],
        "raw_employees.csv",
        ["employee_id", "first_name", "last_name", "gender", "department_id", "job_title", "level",
         "hire_date", "termination_date", "location_city", "location_country", "employment_type",
         "manager_id", "base_salary"],
    )

    write_csv(
        data["requisitions"],
        "raw_requisitions.csv",
        ["requisition_id", "department_id", "job_title", "opened_date", "closed_date", "status", "source_channel"],
    )

    write_csv(
        data["hires"],
        "raw_hires.csv",
        ["hire_id", "requisition_id", "employee_id", "offer_date", "start_date", "source_channel", "signing_bonus"],
    )

    write_csv(
        data["terminations"],
        "raw_terminations.csv",
        ["termination_id", "employee_id", "termination_date", "voluntary", "reason", "exit_survey_score"],
    )

    write_csv(
        data["performance_reviews"],
        "raw_performance_reviews.csv",
        ["review_id", "employee_id", "review_period", "rating", "review_date"],
    )

    write_csv(
        data["compensation_history"],
        "raw_compensation_history.csv",
        ["comp_id", "employee_id", "effective_date", "salary", "change_reason"],
    )

    write_csv(
        data["engagement_surveys"],
        "raw_engagement_surveys.csv",
        ["survey_id", "employee_id", "survey_wave", "survey_date", "engagement_score", "satisfaction_score"],
    )

    print(f"\nFinal active headcount: {sum(1 for e in data['employees'] if not e.get('termination_date'))}")
    print(f"Total employees ever hired: {len(data['employees'])}")
    print(f"Total terminations: {len(data['terminations'])}")


if __name__ == "__main__":
    main()
