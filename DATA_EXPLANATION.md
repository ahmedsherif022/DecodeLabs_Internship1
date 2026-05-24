# Data Preprocessing — Explanation Document
**Project:** Student Career Advisor  
**Data Source:** Stack Overflow Developer Survey 2024 (`results.csv`)  
**Output:** `student_advisor_data.json`

---

## What Is This Project?

The goal is to build a **data-driven student advisor** that answers questions like:

> *"What skills do I need to become a Data Scientist?"*  
> → Python, SQL, R + Pandas, NumPy, scikit-learn + PostgreSQL + median salary $X/yr

Instead of guessing, we use **real survey data from 49,191 developers worldwide** to give honest, statistical answers.

---

## What We Did — Step by Step

### Step 1: Load the Raw Data
- Loaded `results.csv` — the Stack Overflow 2024 Developer Survey
- **49,191 rows × 172 columns**
- Each row = one developer's survey response

### Step 2: Explore the Data (Find Problems)
Before cleaning anything, we inspected the raw data to understand its quality issues.

### Step 3: Select Relevant Columns
From 172 columns we kept only **14** that are useful for the student advisor:

| Column | What It Tells Us |
|--------|-----------------|
| `DevType` | What role the developer has |
| `LanguageHaveWorkedWith` | Languages they actually use |
| `LanguageWantToWorkWith` | Languages they want to learn |
| `DatabaseHaveWorkedWith` | Databases they use |
| `WebframeHaveWorkedWith` | Frameworks they use |
| `PlatformHaveWorkedWith` | Platforms/tools they use |
| `YearsCode` | Years of coding experience |
| `EdLevel` | Education level |
| `Employment` | Full-time, part-time, etc. |
| `ConvertedCompYearly` | Annual salary (USD) |
| `Country` | Country of residence |
| `Age` | Age group |
| `LearnCode` | How they learned to code |
| `Industry` | Industry they work in |

### Step 4: Clean and Fix All Problems (see below)

### Step 5: Build Role Profiles
For each of the **19 developer roles**, we:
- Filter all respondents with that role
- Count the most-used languages, databases, frameworks, platforms
- Calculate salary (median, 25th/75th percentile)
- Calculate experience (median years of coding)
- Record most common education level and employment type

### Step 6: Save as JSON
The clean knowledge base is saved to `student_advisor_data.json`.

---

## Problems Found in the Data

### Problem 1 — Too Many Irrelevant Columns (172 total)
**What it looks like:**  
The survey has 172 columns covering topics like AI opinions, Stack Overflow usage, office tools, communication platforms — none of which help a student pick a career.

**How we solved it:**  
Selected only 14 meaningful columns. Dropped the other 158.

---

### Problem 2 — High Missing Values
**What it looks like:**  
Many columns have 50–80%+ missing values. For example:
- `ConvertedCompYearly` — only ~49% of respondents provided salary
- `DatabaseHaveWorkedWith` — many students/academics skipped this
- `Industry` — optional field, widely skipped

**How we solved it:**  
- We did **not** drop rows just because some columns are missing
- Instead, each metric is computed only from rows that *have* that value
- For salary stats, we require at least 10 valid responses per role before reporting

---

### Problem 3 — Multi-Value Semicolon Strings
**What it looks like:**  
```
LanguageHaveWorkedWith: "Python;SQL;JavaScript;Bash/Shell (all shells)"
DatabaseHaveWorkedWith: "PostgreSQL;MySQL;SQLite"
WebframeHaveWorkedWith: "FastAPI;Flask;Django"
```
These are stored as a single string — you can't count them directly.

**How we solved it:**  
Split each string by `;` into a Python list:
```python
"Python;SQL;R"  →  ["Python", "SQL", "R"]
```
Then used Python's `Counter` to count how many developers in each role use each skill.

---

### Problem 4 — YearsCode Mixed Types
**What it looks like:**  
```
YearsCode column sample:
  "10.0"          (numeric string)
  "Less than 1 year"    (text)
  "More than 50 years"  (text)
  NaN             (missing)
```
The column stores both numbers and English phrases — pandas reads it as `object` (string) type.

**How we solved it:**  
```python
df["YearsCode"] = pd.to_numeric(df["YearsCode"], errors="coerce")
```
- Valid numbers like `"10.0"` → `10.0`
- Text like `"Less than 1 year"` → `NaN` (ignored in statistics)
- This lets us compute median/percentile experience per role

---

### Problem 5 — Salary Extreme Outliers
**What it looks like:**  
```
Min salary  : $1/yr       ← clearly wrong
Max salary  : $50,000,000/yr  ← impossible
Median      : $75,320/yr   ← realistic
Rows >$1M/yr: ~200 rows
```
Extreme values are likely:
- Currency conversion errors (e.g., salary entered in local currency, multiplied incorrectly)
- Data entry mistakes
- Test/fake responses

**How we solved it:**  
Cap salaries at **$1,000,000/yr** — anything above is set to `NaN`:
```python
df.loc[df["ConvertedCompYearly"] > 1_000_000, "ConvertedCompYearly"] = None
```
We also report **median** salary (not mean), which is more resistant to remaining outliers.

---

### Problem 6 — DevType Is Single-Value Per Person
**What it looks like:**  
Unlike languages/databases, `DevType` in this dataset stores **one role per respondent** (no semicolons). Each person picked their primary role.

**Impact:**  
A person who identifies as "Data Scientist" might also do ML work, but only their primary role is recorded.

**How we solved it:**  
We do a direct **exact match** filter per role:
```python
mask = df["DevType"] == "Data scientist"
sub  = df[mask]
```
Then aggregate all their skills to build the role profile.

---

## Output: student_advisor_data.json

### Structure
```json
{
  "meta": {
    "source": "Stack Overflow Developer Survey 2024",
    "total_rows": 49191,
    "roles_count": 19
  },
  "global_stats": {
    "top_languages_overall": [...],
    "top_databases_overall": [...],
    "top_frameworks_overall": [...]
  },
  "role_profiles": {
    "Data Scientist": {
      "sample_count": 574,
      "languages": [
        {"name": "Python", "count": 498},
        {"name": "SQL", "count": 380},
        ...
      ],
      "databases": [...],
      "frameworks": [...],
      "platforms": [...],
      "salary": {
        "median_usd": 120000,
        "p25_usd": 75000,
        "p75_usd": 180000,
        "sample_size": 210
      },
      "experience": {
        "median_years": 8.0,
        "p25_years": 4.0,
        "p75_years": 15.0
      },
      "education": {...},
      "employment": {...}
    },
    ...19 roles total
  },
  "role_aliases": {
    "data science": "Data Scientist",
    "machine learning": "AI / ML Engineer",
    "backend": "Back-End Developer",
    ...
  }
}
```

### The 19 Roles Covered
| Role | Survey Sample |
|------|--------------|
| Data Scientist | ~574 |
| AI / ML Engineer | ~677 |
| Data Engineer | ~770 |
| Full-Stack Developer | ~12,351 |
| Back-End Developer | ~6,453 |
| Front-End Developer | ~1,974 |
| Mobile Developer | ~1,391 |
| DevOps Engineer | ~1,053 |
| Cloud Engineer | ~441 |
| Cybersecurity Engineer | ~370 |
| Data / Business Analyst | ~351 |
| Database Administrator | ~175 |
| Game Developer | ~451 |
| Desktop / Enterprise Developer | ~1,919 |
| QA / Test Engineer | ~343 |
| UX / UI Designer | ~115 |
| Software Architect | ~2,684 |
| Engineering Manager | ~1,068 |
| Embedded / IoT Developer | ~1,274 |

---

## How the Student Advisor Uses This Data

When a student asks:  
> *"What do I need to work as a Data Scientist?"*

The advisor:
1. Matches the question to `"Data Scientist"` via the alias map
2. Looks up `role_profiles["Data Scientist"]`
3. Returns the top languages, databases, frameworks, salary range, and learning tips

**Example answer generated:**
```
To become a Data Scientist you need:

  Languages  : Python, SQL, R, Bash/Shell, Julia
  Databases  : PostgreSQL, MySQL, SQLite, MongoDB
  Frameworks : Pandas/NumPy (via Python), scikit-learn, TensorFlow, PyTorch
  Platforms  : Docker, AWS, Pip, Jupyter

  Salary     : $75k – $120k – $180k/yr (25th / median / 75th)
  Experience : Median 8 years coding

Based on 574 real Data Scientist responses from the
Stack Overflow Developer Survey 2024.
```
