"""
preprocess.py
=============
Preprocessing pipeline for Stack Overflow Developer Survey (results.csv).
Produces student_advisor_data.json — a knowledge base that maps developer
roles to their most-used languages, databases, frameworks, platforms and
learning paths, so a student helper chatbot can give data-driven answers.

Run:  python preprocess.py
"""

import json
import re
import pandas as pd
from collections import Counter

# ---------------------------------------------
# 1. LOAD
# ---------------------------------------------
print("[*] Loading results.csv ...")
df = pd.read_csv("results.csv", low_memory=False)
print(f"   Loaded {len(df):,} rows x {len(df.columns)} columns")

# ---------------------------------------------
# 2. KEEP ONLY RELEVANT COLUMNS
# ---------------------------------------------
KEEP = [
    "DevType",
    "LanguageHaveWorkedWith",
    "LanguageWantToWorkWith",
    "DatabaseHaveWorkedWith",
    "WebframeHaveWorkedWith",
    "PlatformHaveWorkedWith",
    "YearsCode",
    "EdLevel",
    "Employment",
    "ConvertedCompYearly",
    "Country",
    "Age",
    "LearnCode",
    "Industry",
]
df = df[KEEP].copy()
print(f"   Kept {len(KEEP)} columns")

# ---------------------------------------------
# 3. CLEAN & NORMALISE
# ---------------------------------------------

def split_multi(series):
    """Split semicolon-separated values into lists; NaN -> empty list."""
    return series.fillna("").apply(
        lambda v: [x.strip() for x in v.split(";") if x.strip()] if v else []
    )

def top_n(counter, n=10):
    """Return top-n items from a Counter as a list of dicts."""
    return [{"name": name, "count": cnt} for name, cnt in counter.most_common(n)]

# Convert all multi-value columns
multi_cols = [
    "LanguageHaveWorkedWith",
    "LanguageWantToWorkWith",
    "DatabaseHaveWorkedWith",
    "WebframeHaveWorkedWith",
    "PlatformHaveWorkedWith",
    "LearnCode",
    "DevType",
]
for col in multi_cols:
    df[col] = split_multi(df[col])

# Clean YearsCode
df["YearsCode"] = pd.to_numeric(df["YearsCode"], errors="coerce")

# Clean salary (remove extreme outliers — keep <$1 M/yr)
df["ConvertedCompYearly"] = pd.to_numeric(df["ConvertedCompYearly"], errors="coerce")
df.loc[df["ConvertedCompYearly"] > 1_000_000, "ConvertedCompYearly"] = None

print("   Cleaning done.")

# ---------------------------------------------
# 4. ROLE-TO-SKILLS MAPPING
# ---------------------------------------------

# Canonical role names we want to expose to the student
ROLES = {
    "Data scientist":                           "Data Scientist",
    "AI/ML engineer":                           "AI / ML Engineer",
    "Data engineer":                            "Data Engineer",
    "Developer, full-stack":                    "Full-Stack Developer",
    "Developer, back-end":                      "Back-End Developer",
    "Developer, front-end":                     "Front-End Developer",
    "Developer, mobile":                        "Mobile Developer",
    "Developer, embedded applications or devices": "Embedded / IoT Developer",
    "DevOps engineer or professional":          "DevOps Engineer",
    "Cloud infrastructure engineer":            "Cloud Engineer",
    "Cybersecurity or InfoSec professional":    "Cybersecurity Engineer",
    "Data or business analyst":                 "Data / Business Analyst",
    "Database administrator or engineer":       "Database Administrator",
    "Developer, game or graphics":              "Game Developer",
    "Developer, desktop or enterprise applications": "Desktop / Enterprise Developer",
    "Developer, QA or test":                    "QA / Test Engineer",
    "UX, Research Ops or UI design professional": "UX / UI Designer",
    "Architect, software or solutions":         "Software Architect",
    "Engineering manager":                      "Engineering Manager",
}

print("\n🔨 Building role profiles ...")
role_profiles = {}

for raw_role, display_role in ROLES.items():

    # Filter rows where this role appears in the person's DevType list
    mask = df["DevType"].apply(lambda lst: raw_role in lst)
    sub = df[mask]
    n = len(sub)

    if n < 30:
        print(f"   !  Skipping '{display_role}' — only {n} samples")
        continue

    print(f"   ✔  {display_role:45s} -> {n:5,} respondents")

    # -- Skills --------------------------------
    def pool(col):
        c = Counter()
        for lst in sub[col]:
            c.update(lst)
        return c

    langs_counter    = pool("LanguageHaveWorkedWith")
    langs_want       = pool("LanguageWantToWorkWith")
    db_counter       = pool("DatabaseHaveWorkedWith")
    fw_counter       = pool("WebframeHaveWorkedWith")
    plat_counter     = pool("PlatformHaveWorkedWith")
    learn_counter    = pool("LearnCode")

    # -- Salary --------------------------------
    sal = sub["ConvertedCompYearly"].dropna()
    salary_stats = {}
    if len(sal) >= 10:
        salary_stats = {
            "median_usd": round(sal.median()),
            "p25_usd":    round(sal.quantile(0.25)),
            "p75_usd":    round(sal.quantile(0.75)),
            "sample_size": len(sal),
        }

    # -- Experience ----------------------------
    exp = sub["YearsCode"].dropna()
    exp_stats = {}
    if len(exp) >= 10:
        exp_stats = {
            "median_years": round(exp.median(), 1),
            "p25_years":    round(exp.quantile(0.25), 1),
            "p75_years":    round(exp.quantile(0.75), 1),
        }

    # -- Education -----------------------------
    ed_counts = sub["EdLevel"].dropna().value_counts().head(5).to_dict()

    # -- Employment ----------------------------
    emp_counts = sub["Employment"].dropna().value_counts().head(4).to_dict()

    role_profiles[display_role] = {
        "sample_count":  n,
        "languages":     top_n(langs_counter, 10),
        "languages_wanted": top_n(langs_want, 8),
        "databases":     top_n(db_counter, 8),
        "frameworks":    top_n(fw_counter, 8),
        "platforms":     top_n(plat_counter, 8),
        "learning_resources": top_n(learn_counter, 6),
        "salary":        salary_stats,
        "experience":    exp_stats,
        "education":     ed_counts,
        "employment":    emp_counts,
    }

# ---------------------------------------------
# 5. GLOBAL STATS (for comparison / ranking)
# ---------------------------------------------
print("\n📊 Computing global stats ...")

all_langs = Counter()
for lst in df["LanguageHaveWorkedWith"]:
    all_langs.update(lst)

all_dbs = Counter()
for lst in df["DatabaseHaveWorkedWith"]:
    all_dbs.update(lst)

all_fws = Counter()
for lst in df["WebframeHaveWorkedWith"]:
    all_fws.update(lst)

global_stats = {
    "total_respondents": len(df),
    "top_languages_overall": top_n(all_langs, 15),
    "top_databases_overall": top_n(all_dbs, 15),
    "top_frameworks_overall": top_n(all_fws, 15),
}

# ---------------------------------------------
# 6. ROLE ALIASES (for fuzzy matching in chatbot)
# ---------------------------------------------
ALIASES = {
    # Data science / ML
    "data scientist":         "Data Scientist",
    "data science":           "Data Scientist",
    "machine learning":       "AI / ML Engineer",
    "ml engineer":            "AI / ML Engineer",
    "ai engineer":            "AI / ML Engineer",
    "artificial intelligence":"AI / ML Engineer",
    "deep learning":          "AI / ML Engineer",
    "data engineer":          "Data Engineer",
    "data pipeline":          "Data Engineer",
    "etl":                    "Data Engineer",
    "analyst":                "Data / Business Analyst",
    "business analyst":       "Data / Business Analyst",
    "bi":                     "Data / Business Analyst",
    # Web
    "full stack":             "Full-Stack Developer",
    "fullstack":              "Full-Stack Developer",
    "full-stack":             "Full-Stack Developer",
    "backend":                "Back-End Developer",
    "back end":               "Back-End Developer",
    "back-end":               "Back-End Developer",
    "server side":            "Back-End Developer",
    "frontend":               "Front-End Developer",
    "front end":              "Front-End Developer",
    "front-end":              "Front-End Developer",
    "ui developer":           "Front-End Developer",
    "web developer":          "Full-Stack Developer",
    # Mobile
    "mobile":                 "Mobile Developer",
    "android":                "Mobile Developer",
    "ios":                    "Mobile Developer",
    "flutter":                "Mobile Developer",
    "react native":           "Mobile Developer",
    # DevOps / Cloud
    "devops":                 "DevOps Engineer",
    "sre":                    "DevOps Engineer",
    "site reliability":       "DevOps Engineer",
    "cloud":                  "Cloud Engineer",
    "aws":                    "Cloud Engineer",
    "azure":                  "Cloud Engineer",
    "gcp":                    "Cloud Engineer",
    # Security
    "security":               "Cybersecurity Engineer",
    "cybersecurity":          "Cybersecurity Engineer",
    "infosec":                "Cybersecurity Engineer",
    "penetration":            "Cybersecurity Engineer",
    # Other
    "game":                   "Game Developer",
    "gaming":                 "Game Developer",
    "unity":                  "Game Developer",
    "unreal":                 "Game Developer",
    "qa":                     "QA / Test Engineer",
    "testing":                "QA / Test Engineer",
    "quality assurance":      "QA / Test Engineer",
    "ux":                     "UX / UI Designer",
    "ui design":              "UX / UI Designer",
    "designer":               "UX / UI Designer",
    "dba":                    "Database Administrator",
    "database admin":         "Database Administrator",
    "embedded":               "Embedded / IoT Developer",
    "iot":                    "Embedded / IoT Developer",
    "firmware":               "Embedded / IoT Developer",
    "desktop":                "Desktop / Enterprise Developer",
    "enterprise":             "Desktop / Enterprise Developer",
    "architect":              "Software Architect",
    "solutions architect":    "Software Architect",
    "manager":                "Engineering Manager",
    "tech lead":              "Engineering Manager",
}

# ---------------------------------------------
# 7. SAVE
# ---------------------------------------------
output = {
    "meta": {
        "source":     "Stack Overflow Developer Survey 2024",
        "total_rows": len(df),
        "roles_count": len(role_profiles),
    },
    "global_stats":   global_stats,
    "role_profiles":  role_profiles,
    "role_aliases":   ALIASES,
}

with open("student_advisor_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved student_advisor_data.json")
print(f"   {len(role_profiles)} role profiles ready.")
print("\n🎯 Roles available:")
for role in role_profiles:
    n = role_profiles[role]["sample_count"]
    print(f"   * {role} ({n:,} respondents)")
