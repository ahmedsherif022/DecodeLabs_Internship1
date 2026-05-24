import json

def cell(ctype, source, id_):
    base = {"cell_type": ctype, "metadata": {}, "source": source, "id": id_}
    if ctype == "code":
        base["outputs"] = []
        base["execution_count"] = None
    return base

C = cell  # shorthand

cells = [

# ── TITLE ──────────────────────────────────────────────────────────────────
C("markdown", [
"# Student Career Advisor — Data Preprocessing\n",
"\n",
"**Source:** Stack Overflow Developer Survey 2024 (`results.csv`)  \n",
"**Goal:** Build `student_advisor_data.json` — a knowledge base that maps  \n",
"developer roles → required skills, so students can ask *'What do I need to become a Data Scientist?'* and get a real, data-driven answer.\n",
"\n",
"---\n",
"### Notebook Flow\n",
"1. Load raw data\n",
"2. Explore & identify problems\n",
"3. Clean each problem\n",
"4. Build role profiles\n",
"5. Visualise\n",
"6. Save JSON knowledge base\n",
], "md-title"),

# ── IMPORTS ─────────────────────────────────────────────────────────────────
C("code", [
"import pandas as pd\n",
"import json\n",
"import warnings\n",
"from collections import Counter\n",
"import matplotlib.pyplot as plt\n",
"import matplotlib\n",
"matplotlib.rcParams['figure.figsize'] = (12, 4)\n",
"warnings.filterwarnings('ignore')\n",
"print('Libraries loaded OK')\n",
], "cell-imports"),

# ── STEP 1: LOAD ─────────────────────────────────────────────────────────────
C("markdown", ["## Step 1 — Load Raw Data\n"], "md-step1"),

C("code", [
"df_raw = pd.read_csv('results.csv', low_memory=False)\n",
"print(f'Rows    : {len(df_raw):,}')\n",
"print(f'Columns : {len(df_raw.columns)}')\n",
"df_raw.head(2)\n",
], "cell-load"),

# ── STEP 2: EXPLORE ──────────────────────────────────────────────────────────
C("markdown", [
"## Step 2 — Explore & Identify Problems\n",
"\n",
"We run quick audits on the raw data before touching anything.\n",
], "md-step2"),

C("code", [
"# 2a. Missing values\n",
"missing = df_raw.isnull().mean().sort_values(ascending=False) * 100\n",
"print('=== Top 20 columns by % missing ===')\n",
"print(missing.head(20).round(1).to_string())\n",
], "cell-missing"),

C("code", [
"# 2b. Show that many columns are semicolon-separated multi-value strings\n",
"multi_cols = ['DevType','LanguageHaveWorkedWith','DatabaseHaveWorkedWith',\n",
"              'WebframeHaveWorkedWith','PlatformHaveWorkedWith','LearnCode']\n",
"print('=== Multi-value columns (raw) ===')\n",
"for c in multi_cols:\n",
"    sample = df_raw[c].dropna().iloc[0]\n",
"    print(f'{c}:\\n  {str(sample)[:100]}\\n')\n",
], "cell-multivals"),

C("code", [
"# 2c. YearsCode has mixed types: strings + numbers\n",
"print('YearsCode value counts (top 15):')\n",
"print(df_raw['YearsCode'].value_counts().head(15).to_string())\n",
], "cell-yearscode"),

C("code", [
"# 2d. Salary extreme outliers\n",
"sal_raw = pd.to_numeric(df_raw['ConvertedCompYearly'], errors='coerce')\n",
"coverage = sal_raw.notna().mean() * 100\n",
"print(f'Salary non-null: {sal_raw.notna().sum():,} / {len(df_raw):,} ({coverage:.1f}%)')\n",
"print(f'Min salary  : ${sal_raw.min():,.0f}')\n",
"print(f'Max salary  : ${sal_raw.max():,.0f}  <-- likely bad data')\n",
"print(f'Median      : ${sal_raw.median():,.0f}')\n",
"print(f'Rows >$1M/yr: {(sal_raw > 1_000_000).sum()}')\n",
], "cell-salary"),

C("code", [
"# 2e. Check if DevType has multiple roles per person (semicolon-separated)\n",
"devtype_raw = df_raw['DevType'].dropna()\n",
"multi_role = devtype_raw.str.contains(';').sum()\n",
"pct = multi_role / len(devtype_raw) * 100\n",
"print(f'Total DevType responses : {len(devtype_raw):,}')\n",
"print(f'Multi-role rows (with ;): {multi_role:,} ({pct:.1f}%)')\n",
"print()\n",
"if multi_role > 0:\n",
"    print('Example multi-role:', devtype_raw[devtype_raw.str.contains(';')].iloc[0])\n",
"else:\n",
"    print('Finding: Each respondent has exactly ONE DevType in this dataset.')\n",
"    print('Unique roles found:', devtype_raw.nunique())\n",
"    print('\\nTop 10 roles:')\n",
"    print(devtype_raw.value_counts().head(10).to_string())\n",
], "cell-multirole"),

# ── PROBLEMS SUMMARY ─────────────────────────────────────────────────────────
C("markdown", [
"## Step 3 — Problems Found & Solutions\n",
"\n",
"| # | Problem | Column(s) | Solution |\n",
"|---|---------|-----------|----------|\n",
"| 1 | **172 columns, only ~14 useful** | All | Select only 14 relevant columns |\n",
"| 2 | **High missing values** (up to 80%+) | Many columns | Drop irrelevant columns; use per-role filtering |\n",
"| 3 | **Multi-value semicolon strings** | Languages, DBs, Frameworks, Platforms... | Split by `;` into Python lists |\n",
"| 4 | **YearsCode mixed types** (`str` + `int`) | YearsCode | `pd.to_numeric(errors='coerce')` — text becomes NaN |\n",
"| 5 | **Salary extreme outliers** ($1 to $50M/yr) | ConvertedCompYearly | Cap at $1M/yr; use median not mean |\n",
"| 6 | **DevType is single-value per person** | DevType | No split needed; filter rows by exact role match |\n",
], "md-problems"),

# ── STEP 4: SELECT COLUMNS ────────────────────────────────────────────────────
C("markdown", ["## Step 4 — Select Relevant Columns\n"], "md-step4"),

C("code", [
"KEEP = [\n",
"    'DevType',\n",
"    'LanguageHaveWorkedWith',\n",
"    'LanguageWantToWorkWith',\n",
"    'DatabaseHaveWorkedWith',\n",
"    'WebframeHaveWorkedWith',\n",
"    'PlatformHaveWorkedWith',\n",
"    'YearsCode',\n",
"    'EdLevel',\n",
"    'Employment',\n",
"    'ConvertedCompYearly',\n",
"    'Country',\n",
"    'Age',\n",
"    'LearnCode',\n",
"    'Industry',\n",
"]\n",
"df = df_raw[KEEP].copy()\n",
"print(f'Reduced: {len(df_raw.columns)} columns --> {len(df.columns)} columns')\n",
"print(f'Rows   : {len(df):,}')\n",
"df.isnull().mean().round(3).mul(100).rename('% missing').to_frame()\n",
], "cell-select"),

# ── STEP 5: FIX MULTI-VALUE ──────────────────────────────────────────────────
C("markdown", [
"## Step 5 — Fix Problem 3: Split Multi-Value Columns\n",
"\n",
"Each semicolon-separated string becomes a Python list.\n",
], "md-step5"),

C("code", [
"def split_multi(series):\n",
"    \"\"\"Split semicolon-separated strings into lists; NaN -> empty list.\"\"\"\n",
"    return series.fillna('').apply(\n",
"        lambda v: [x.strip() for x in v.split(';') if x.strip()] if v else []\n",
"    )\n",
"\n",
"multi_cols = ['DevType','LanguageHaveWorkedWith','LanguageWantToWorkWith',\n",
"              'DatabaseHaveWorkedWith','WebframeHaveWorkedWith',\n",
"              'PlatformHaveWorkedWith','LearnCode']\n",
"for col in multi_cols:\n",
"    df[col] = split_multi(df[col])\n",
"\n",
"# Show before vs after\n",
"raw_val = df_raw['LanguageHaveWorkedWith'].dropna().iloc[0]\n",
"clean_val = df['LanguageHaveWorkedWith'].iloc[0]\n",
"print('BEFORE (raw string):')\n",
"print(' ', raw_val)\n",
"print('\\nAFTER (Python list):')\n",
"print(' ', clean_val)\n",
], "cell-split"),

# ── STEP 6: FIX YEARSCODE ────────────────────────────────────────────────────
C("markdown", [
"## Step 6 — Fix Problem 4: YearsCode Mixed Types\n",
"\n",
"Text values like *'Less than 1 year'* and *'More than 50 years'* become `NaN`  \n",
"via `pd.to_numeric(errors='coerce')`. We keep valid numeric years.\n",
], "md-step6"),

C("code", [
"df['YearsCode'] = pd.to_numeric(df['YearsCode'], errors='coerce')\n",
"print('YearsCode after cleaning:')\n",
"print(df['YearsCode'].describe().round(1))\n",
"print(f'\\nNaN (was text / missing): {df[\"YearsCode\"].isna().sum():,}')\n",
], "cell-yearscode-fix"),

# ── STEP 7: FIX SALARY ──────────────────────────────────────────────────────
C("markdown", [
"## Step 7 — Fix Problem 5: Salary Outliers\n",
"\n",
"We cap salaries at **$1,000,000/yr** — anything above is likely a data entry error  \n",
"or a currency-conversion issue in the survey.\n",
], "md-step7"),

C("code", [
"df['ConvertedCompYearly'] = pd.to_numeric(df['ConvertedCompYearly'], errors='coerce')\n",
"before_max = df['ConvertedCompYearly'].max()\n",
"removed = (df['ConvertedCompYearly'] > 1_000_000).sum()\n",
"df.loc[df['ConvertedCompYearly'] > 1_000_000, 'ConvertedCompYearly'] = None\n",
"print(f'Outliers removed (>$1M/yr): {removed}')\n",
"print(f'Max before : ${before_max:,.0f}')\n",
"print(f'Max after  : ${df[\"ConvertedCompYearly\"].max():,.0f}')\n",
"print('\\nSalary stats after cleaning:')\n",
"print(df['ConvertedCompYearly'].describe().round(0))\n",
], "cell-salary-fix"),

# ── STEP 8: BUILD PROFILES ───────────────────────────────────────────────────
C("markdown", [
"## Step 8 — Build Role Profiles\n",
"\n",
"For each developer role, we:\n",
"- Filter respondents who chose that role (a person can have multiple roles)\n",
"- Count the most-used languages, databases, frameworks, platforms\n",
"- Compute salary statistics and years of experience\n",
"- Record education level and employment type\n",
], "md-step8"),

C("code", [
"ROLES = {\n",
"    'Data scientist'                              : 'Data Scientist',\n",
"    'AI/ML engineer'                              : 'AI / ML Engineer',\n",
"    'Data engineer'                               : 'Data Engineer',\n",
"    'Developer, full-stack'                       : 'Full-Stack Developer',\n",
"    'Developer, back-end'                         : 'Back-End Developer',\n",
"    'Developer, front-end'                        : 'Front-End Developer',\n",
"    'Developer, mobile'                           : 'Mobile Developer',\n",
"    'Developer, embedded applications or devices' : 'Embedded / IoT Developer',\n",
"    'DevOps engineer or professional'             : 'DevOps Engineer',\n",
"    'Cloud infrastructure engineer'               : 'Cloud Engineer',\n",
"    'Cybersecurity or InfoSec professional'       : 'Cybersecurity Engineer',\n",
"    'Data or business analyst'                    : 'Data / Business Analyst',\n",
"    'Database administrator or engineer'          : 'Database Administrator',\n",
"    'Developer, game or graphics'                 : 'Game Developer',\n",
"    'Developer, desktop or enterprise applications': 'Desktop / Enterprise Developer',\n",
"    'Developer, QA or test'                       : 'QA / Test Engineer',\n",
"    'UX, Research Ops or UI design professional'  : 'UX / UI Designer',\n",
"    'Architect, software or solutions'            : 'Software Architect',\n",
"    'Engineering manager'                         : 'Engineering Manager',\n",
"}\n",
"print(f'Roles to profile: {len(ROLES)}')\n",
], "cell-roles"),

C("code", [
"def top_n(counter, n=10):\n",
"    return [{'name': k, 'count': v} for k, v in counter.most_common(n)]\n",
"\n",
"role_profiles = {}\n",
"\n",
"for raw_role, display_role in ROLES.items():\n",
"    mask = df['DevType'].apply(lambda lst: raw_role in lst)\n",
"    sub  = df[mask]\n",
"    n    = len(sub)\n",
"    if n < 30:\n",
"        continue\n",
"\n",
"    def pool(col):\n",
"        c = Counter()\n",
"        for lst in sub[col]: c.update(lst)\n",
"        return c\n",
"\n",
"    sal = sub['ConvertedCompYearly'].dropna()\n",
"    exp = sub['YearsCode'].dropna()\n",
"\n",
"    salary_stats = {}\n",
"    if len(sal) >= 10:\n",
"        salary_stats = {\n",
"            'median_usd'  : round(sal.median()),\n",
"            'p25_usd'     : round(sal.quantile(0.25)),\n",
"            'p75_usd'     : round(sal.quantile(0.75)),\n",
"            'sample_size' : len(sal),\n",
"        }\n",
"\n",
"    exp_stats = {}\n",
"    if len(exp) >= 10:\n",
"        exp_stats = {\n",
"            'median_years': round(exp.median(), 1),\n",
"            'p25_years'   : round(exp.quantile(0.25), 1),\n",
"            'p75_years'   : round(exp.quantile(0.75), 1),\n",
"        }\n",
"\n",
"    role_profiles[display_role] = {\n",
"        'sample_count'      : n,\n",
"        'languages'         : top_n(pool('LanguageHaveWorkedWith'), 10),\n",
"        'languages_wanted'  : top_n(pool('LanguageWantToWorkWith'), 8),\n",
"        'databases'         : top_n(pool('DatabaseHaveWorkedWith'), 8),\n",
"        'frameworks'        : top_n(pool('WebframeHaveWorkedWith'), 8),\n",
"        'platforms'         : top_n(pool('PlatformHaveWorkedWith'), 8),\n",
"        'learning_resources': top_n(pool('LearnCode'), 6),\n",
"        'salary'            : salary_stats,\n",
"        'experience'        : exp_stats,\n",
"        'education'         : sub['EdLevel'].dropna().value_counts().head(5).to_dict(),\n",
"        'employment'        : sub['Employment'].dropna().value_counts().head(4).to_dict(),\n",
"    }\n",
"\n",
"print(f'Built {len(role_profiles)} role profiles')\n",
"print('-' * 55)\n",
"for role, p in role_profiles.items():\n",
"    print(f\"  {p['sample_count']:5,}  respondents  ->  {role}\")\n",
], "cell-build"),

# ── STEP 9: VISUALISE ────────────────────────────────────────────────────────
C("markdown", ["## Step 9 — Visualise Top Skills per Role\n"], "md-step9"),

C("code", [
"def plot_top_skills(role_name, skill_key='languages', top=8, color='#4F86F7'):\n",
"    if role_name not in role_profiles:\n",
"        print(f'Role not found: {role_name}'); return\n",
"    items  = role_profiles[role_name][skill_key][:top]\n",
"    names  = [i['name'] for i in items]\n",
"    counts = [i['count'] for i in items]\n",
"    fig, ax = plt.subplots(figsize=(10, 3.5))\n",
"    bars = ax.barh(names[::-1], counts[::-1], color=color)\n",
"    ax.set_xlabel('Respondents')\n",
"    ax.set_title(f'{role_name}  |  {skill_key.replace(\"_\",\" \").title()}')\n",
"    for bar, cnt in zip(bars, counts[::-1]):\n",
"        ax.text(bar.get_width()+2, bar.get_y()+bar.get_height()/2,\n",
"                str(cnt), va='center', fontsize=9)\n",
"    plt.tight_layout(); plt.show()\n",
"\n",
"plot_top_skills('Data Scientist',     'languages',   color='#6366f1')\n",
"plot_top_skills('Data Scientist',     'frameworks',  color='#8b5cf6')\n",
"plot_top_skills('Full-Stack Developer','languages',  color='#3b82f6')\n",
"plot_top_skills('DevOps Engineer',    'platforms',   color='#10b981')\n",
"plot_top_skills('AI / ML Engineer',   'languages',   color='#f59e0b')\n",
], "cell-plot-skills"),

C("code", [
"# Salary comparison across all roles\n",
"salary_data = [(role, p['salary']['median_usd'])\n",
"               for role, p in role_profiles.items() if p.get('salary')]\n",
"salary_data.sort(key=lambda x: x[1])\n",
"roles_s, medians = zip(*salary_data)\n",
"\n",
"fig, ax = plt.subplots(figsize=(11, 6))\n",
"colors  = ['#22c55e' if m >= 100000 else '#f59e0b' if m >= 70000 else '#ef4444'\n",
"           for m in medians]\n",
"bars = ax.barh(roles_s, [m/1000 for m in medians], color=colors)\n",
"ax.set_xlabel('Median Annual Salary (USD thousands)')\n",
"ax.set_title('Median Salary by Developer Role  (green = >$100k)')\n",
"for bar, val in zip(bars, [m/1000 for m in medians]):\n",
"    ax.text(bar.get_width()+0.5,\n",
"            bar.get_y()+bar.get_height()/2,\n",
"            f'${val:.0f}k', va='center', fontsize=9)\n",
"plt.tight_layout(); plt.show()\n",
], "cell-salary-chart"),

C("code", [
"# Years of experience comparison\n",
"exp_data = [(role, p['experience']['median_years'])\n",
"            for role, p in role_profiles.items() if p.get('experience')]\n",
"exp_data.sort(key=lambda x: x[1])\n",
"roles_e, exps = zip(*exp_data)\n",
"\n",
"fig, ax = plt.subplots(figsize=(11, 6))\n",
"ax.barh(roles_e, exps, color='#6366f1')\n",
"ax.set_xlabel('Median Years of Coding Experience')\n",
"ax.set_title('Experience Level by Developer Role')\n",
"for i, (val, role) in enumerate(zip(exps, roles_e)):\n",
"    ax.text(val+0.1, i, f'{val}y', va='center', fontsize=9)\n",
"plt.tight_layout(); plt.show()\n",
], "cell-exp-chart"),

# ── STEP 10: GLOBAL STATS ────────────────────────────────────────────────────
C("markdown", ["## Step 10 — Global Stats & Role Aliases\n"], "md-step10"),

C("code", [
"all_langs = Counter()\n",
"for lst in df['LanguageHaveWorkedWith']: all_langs.update(lst)\n",
"all_dbs = Counter()\n",
"for lst in df['DatabaseHaveWorkedWith']: all_dbs.update(lst)\n",
"all_fws = Counter()\n",
"for lst in df['WebframeHaveWorkedWith']: all_fws.update(lst)\n",
"\n",
"global_stats = {\n",
"    'total_respondents'      : len(df),\n",
"    'top_languages_overall'  : top_n(all_langs, 15),\n",
"    'top_databases_overall'  : top_n(all_dbs, 15),\n",
"    'top_frameworks_overall' : top_n(all_fws, 15),\n",
"}\n",
"\n",
"ALIASES = {\n",
"    'data scientist':'Data Scientist', 'data science':'Data Scientist',\n",
"    'machine learning':'AI / ML Engineer', 'ml engineer':'AI / ML Engineer',\n",
"    'ai engineer':'AI / ML Engineer', 'deep learning':'AI / ML Engineer',\n",
"    'data engineer':'Data Engineer', 'etl':'Data Engineer',\n",
"    'analyst':'Data / Business Analyst', 'business analyst':'Data / Business Analyst',\n",
"    'full stack':'Full-Stack Developer', 'fullstack':'Full-Stack Developer',\n",
"    'backend':'Back-End Developer', 'back end':'Back-End Developer',\n",
"    'frontend':'Front-End Developer', 'front end':'Front-End Developer',\n",
"    'web developer':'Full-Stack Developer',\n",
"    'mobile':'Mobile Developer', 'android':'Mobile Developer',\n",
"    'ios':'Mobile Developer', 'flutter':'Mobile Developer',\n",
"    'devops':'DevOps Engineer', 'sre':'DevOps Engineer',\n",
"    'cloud':'Cloud Engineer', 'aws':'Cloud Engineer', 'azure':'Cloud Engineer',\n",
"    'security':'Cybersecurity Engineer', 'cybersecurity':'Cybersecurity Engineer',\n",
"    'game':'Game Developer', 'unity':'Game Developer', 'unreal':'Game Developer',\n",
"    'qa':'QA / Test Engineer', 'testing':'QA / Test Engineer',\n",
"    'ux':'UX / UI Designer', 'designer':'UX / UI Designer',\n",
"    'dba':'Database Administrator',\n",
"    'embedded':'Embedded / IoT Developer', 'iot':'Embedded / IoT Developer',\n",
"    'architect':'Software Architect', 'manager':'Engineering Manager',\n",
"}\n",
"print(f'Global stats done. Aliases defined: {len(ALIASES)}')\n",
], "cell-global"),

# ── STEP 11: SAVE JSON ───────────────────────────────────────────────────────
C("markdown", ["## Step 11 — Save Knowledge Base\n"], "md-step11"),

C("code", [
"output = {\n",
"    'meta': {\n",
"        'source'     : 'Stack Overflow Developer Survey 2024',\n",
"        'total_rows' : len(df),\n",
"        'roles_count': len(role_profiles),\n",
"    },\n",
"    'global_stats' : global_stats,\n",
"    'role_profiles': role_profiles,\n",
"    'role_aliases' : ALIASES,\n",
"}\n",
"with open('student_advisor_data.json', 'w', encoding='utf-8') as f:\n",
"    json.dump(output, f, ensure_ascii=False, indent=2)\n",
"\n",
"import os\n",
"size_kb = os.path.getsize('student_advisor_data.json') / 1024\n",
"print(f'Saved: student_advisor_data.json  ({size_kb:.1f} KB)')\n",
"print(f'Roles: {len(role_profiles)}')\n",
], "cell-save"),

C("code", [
"# Quick sanity check\n",
"print('=== Data Scientist ===')\n",
"ds = role_profiles['Data Scientist']\n",
"print(f\"Respondents : {ds['sample_count']:,}\")\n",
"print(f\"Median Salary: ${ds['salary']['median_usd']:,}/yr\")\n",
"print(f\"Median Exp   : {ds['experience']['median_years']} years\")\n",
"print('Top languages:', [x['name'] for x in ds['languages'][:5]])\n",
"print('Top databases:', [x['name'] for x in ds['databases'][:4]])\n",
"print('Top frameworks:', [x['name'] for x in ds['frameworks'][:4]])\n",
], "cell-check"),

C("markdown", [
"---\n",
"## Done!\n",
"\n",
"The file `student_advisor_data.json` is now ready.  \n",
"It contains **role profiles** for 19 developer careers — each with:\n",
"- Top languages, databases, frameworks, platforms\n",
"- Salary range (25th / median / 75th percentile)\n",
"- Years of experience\n",
"- Education level & employment type\n",
"- Learning resource preferences\n",
"\n",
"This JSON feeds the **Student Career Advisor** chatbot.\n",
], "md-done"),

]

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.12.0"
        }
    },
    "cells": cells,
}

with open("student_advisor_preprocessing.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook written: student_advisor_preprocessing.ipynb")
