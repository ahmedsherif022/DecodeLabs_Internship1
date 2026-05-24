import json
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "student_advisor_data.json"
OUTPUT_PATH = BASE_DIR / "Student_Career_Advisor_Project_Report.pdf"


def load_project_data():
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def money(value):
    if not value:
        return "N/A"
    return f"${int(value):,}"


def top_names(items, limit=5):
    return ", ".join(item.get("name", "") for item in items[:limit] if item.get("name"))


def build_roadmap(profile):
    groups = [
        ("languages", 2),
        ("databases", 1),
        ("frameworks", 2),
        ("platforms", 2),
    ]
    seen = set()
    skills = []

    for field, limit in groups:
        for item in profile.get(field, [])[:limit]:
            name = str(item.get("name", "")).strip()
            key = name.lower()
            if name and key not in seen and len(skills) < 6:
                seen.add(key)
                skills.append(name)

    return " -> ".join(skills) if skills else "No roadmap data available"


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=18,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=24,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#111827"),
            spaceBefore=14,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#2563eb"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=15,
            textColor=colors.HexColor("#1f2937"),
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#4b5563"),
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#0f766e"),
            backColor=colors.HexColor("#ecfeff"),
            borderColor=colors.HexColor("#67e8f9"),
            borderPadding=8,
            borderWidth=0.7,
            spaceAfter=12,
        ),
    }


def table_style(header_color="#2563eb"):
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.2),
            ("LEADING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )


def paragraph_list(items, styles):
    story = []
    for item in items:
        story.append(Paragraph(f"- {item}", styles["body"]))
    return story


def add_header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#e5e7eb"))
    canvas.line(0.65 * inch, height - 0.55 * inch, width - 0.65 * inch, height - 0.55 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawString(0.65 * inch, height - 0.42 * inch, "Student Career Advisor Project Report")
    canvas.drawRightString(width - 0.65 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_report():
    data = load_project_data()
    styles = make_styles()
    meta = data.get("meta", {})
    role_profiles = data.get("role_profiles", {})
    global_stats = data.get("global_stats", {})

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.78 * inch,
        bottomMargin=0.7 * inch,
        title="Student Career Advisor Project Report",
        author="Student Career Advisor Team",
    )

    story = []

    story.append(Spacer(1, 0.6 * inch))
    story.append(Paragraph("Student Career Advisor", styles["title"]))
    story.append(
        Paragraph(
            "AI mentorship platform using real developer survey statistics, "
            "interactive dashboards, career comparison, and learning roadmaps.",
            styles["subtitle"],
        )
    )

    overview_rows = [
        ["Project Type", "Web-based AI career guidance platform"],
        ["Data Source", meta.get("source", "Stack Overflow Developer Survey 2024")],
        ["Records Processed", f"{meta.get('total_rows', 49191):,} developer responses"],
        ["Career Profiles", f"{len(role_profiles)} developer roles"],
        ["Generated On", date.today().isoformat()],
    ]
    overview_table = Table(overview_rows, colWidths=[1.8 * inch, 4.7 * inch])
    overview_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1d4ed8")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bfdbfe")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(overview_table)
    story.append(PageBreak())

    story.append(Paragraph("1. Project Idea", styles["h1"]))
    story.append(
        Paragraph(
            "The project is a Student Career Advisor website. Its purpose is to help "
            "students understand technology career paths using both conversational AI "
            "and real-world developer statistics. Instead of giving generic advice, "
            "the system grounds its recommendations in cleaned survey data from "
            "professional developers.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "Core idea: a student can ask about a track such as Data Scientist, "
            "Back-End Developer, Cybersecurity Engineer, or AI / ML Engineer. The "
            "website detects the track, answers through an AI advisor, and shows "
            "visual data about salary, experience, skills, education, and employment.",
            styles["callout"],
        )
    )

    story.append(Paragraph("2. What We Built", styles["h1"]))
    story.extend(
        paragraph_list(
            [
                "A Flask backend that serves the website, exposes the survey JSON, and handles chat requests.",
                "A Gemini-powered AI advisor that provides friendly career guidance when an API key is configured.",
                "A role-matching system that detects career paths from user messages using aliases and canonical role names.",
                "An interactive dashboard that shows salary distribution, coding experience, popular languages, databases, education, and employment type.",
                "A career comparison modal for side-by-side role analysis.",
                "A Learning Roadmap Visualizer that builds an ordered skill tree from the survey-backed role profile.",
            ],
            styles,
        )
    )

    story.append(Paragraph("3. Dataset and Preprocessing", styles["h1"]))
    story.append(
        Paragraph(
            "The raw dataset is the Stack Overflow Developer Survey 2024. The raw CSV "
            "contains many columns, but the project focuses on fields that are useful "
            "for career guidance: developer type, languages, databases, frameworks, "
            "platforms, years of coding, education, employment, country, salary, age, "
            "learning resources, and industry.",
            styles["body"],
        )
    )
    story.extend(
        paragraph_list(
            [
                "Selected only the career-relevant columns from the raw survey.",
                "Handled missing values by computing each metric from available responses only.",
                "Split multi-value survey fields such as languages and databases by semicolon.",
                "Cleaned years of coding so numeric experience statistics could be calculated.",
                "Capped unrealistic salary outliers before computing salary percentiles.",
                "Built one profile per supported developer role and saved the result in student_advisor_data.json.",
            ],
            styles,
        )
    )

    story.append(Paragraph("4. System Architecture", styles["h1"]))
    architecture_rows = [
        ["Layer", "Responsibility"],
        ["Frontend", "HTML, CSS, and JavaScript single-page interface with chat, dashboard, comparison modal, and roadmap visualizer."],
        ["Backend", "Flask app in app.py serving static files, survey data, and /api/chat."],
        ["Knowledge Base", "student_advisor_data.json containing role profiles, aliases, global stats, salaries, technologies, education, and employment data."],
        ["AI Layer", "Google Gemini model receives grounded system instructions based on the matched role profile."],
        ["Visualization", "Custom dashboard bars and Mermaid.js flowcharts for learning roadmaps."],
    ]
    arch_table = Table(
        [[Paragraph(cell, styles["small"]) for cell in row] for row in architecture_rows],
        colWidths=[1.4 * inch, 5.1 * inch],
    )
    arch_table.setStyle(table_style("#0f766e"))
    story.append(arch_table)

    story.append(Paragraph("5. Main User Flow", styles["h1"]))
    story.extend(
        paragraph_list(
            [
                "The student opens the website and sees suggested career tracks.",
                "The student clicks a role chip or asks a question in the chat.",
                "The backend matches the message to a career role when possible.",
                "The AI advisor answers using exact statistics from the matched role profile.",
                "The dashboard updates with salary, experience, technology, education, and employment insights.",
                "The roadmap section appears with an ordered skill path and confidence sliders.",
            ],
            styles,
        )
    )

    story.append(PageBreak())

    story.append(Paragraph("6. Supported Career Profiles", styles["h1"]))
    top_roles = sorted(
        role_profiles.items(),
        key=lambda item: item[1].get("sample_count", 0),
        reverse=True,
    )[:10]
    role_rows = [["Role", "Responses", "Median Salary", "Median Experience", "Top Languages"]]
    for role, profile in top_roles:
        role_rows.append(
            [
                role,
                f"{profile.get('sample_count', 0):,}",
                money(profile.get("salary", {}).get("median_usd")),
                f"{profile.get('experience', {}).get('median_years', 'N/A')} yrs",
                top_names(profile.get("languages", []), 3),
            ]
        )
    role_table = Table(
        [[Paragraph(str(cell), styles["small"]) for cell in row] for row in role_rows],
        colWidths=[1.55 * inch, 0.8 * inch, 1.05 * inch, 1.0 * inch, 2.1 * inch],
    )
    role_table.setStyle(table_style("#2563eb"))
    story.append(role_table)

    story.append(Paragraph("7. Learning Roadmap Visualizer", styles["h1"]))
    story.append(
        Paragraph(
            "The newest feature adds a visual ordered skill tree for each selected "
            "track. The roadmap is generated from the same trusted survey profile "
            "used by the dashboard. It takes the top languages, database, frameworks, "
            "and platforms for that role, removes duplicates, and caps the list to "
            "a concise learning path.",
            styles["body"],
        )
    )
    story.extend(
        paragraph_list(
            [
                "Each roadmap is rendered as a Mermaid.js flowchart.",
                "Students rate their confidence in every skill from 0% to 100%.",
                "Skills at 80% or above are treated as mastered.",
                "Skills between 40% and 79% are treated as currently learning.",
                "The first skill below 80% becomes the next priority.",
                "Progress is saved in localStorage per role, so it remains after refresh.",
            ],
            styles,
        )
    )

    example_role = "Data Scientist"
    example_profile = role_profiles.get(example_role, {})
    story.append(Paragraph("Example Roadmap", styles["h2"]))
    story.append(
        Paragraph(
            f"For {example_role}: {build_roadmap(example_profile)}",
            styles["callout"],
        )
    )

    story.append(Paragraph("8. Global Technology Snapshot", styles["h1"]))
    snapshot_rows = [
        ["Category", "Top Items"],
        ["Languages", top_names(global_stats.get("top_languages_overall", []), 6)],
        ["Databases", top_names(global_stats.get("top_databases_overall", []), 6)],
        ["Frameworks", top_names(global_stats.get("top_frameworks_overall", []), 6)],
    ]
    snapshot_table = Table(
        [[Paragraph(str(cell), styles["small"]) for cell in row] for row in snapshot_rows],
        colWidths=[1.3 * inch, 5.2 * inch],
    )
    snapshot_table.setStyle(table_style("#7c3aed"))
    story.append(snapshot_table)

    story.append(PageBreak())

    story.append(Paragraph("9. Project Files", styles["h1"]))
    files_rows = [
        ["File", "Purpose"],
        ["app.py", "Main Flask server, role matching, Gemini chat integration, API routes."],
        ["static/index.html", "Single-page app structure and dashboard sections."],
        ["static/script.js", "Frontend behavior: chat, dashboard rendering, comparison modal, roadmap visualizer."],
        ["static/style.css", "Application layout, dashboard design, responsive styling."],
        ["preprocess.py", "Data cleaning and transformation script."],
        ["student_advisor_data.json", "Preprocessed career knowledge base used by backend and frontend."],
        ["test_app.py", "Basic route and role-matching verification script."],
    ]
    files_table = Table(
        [[Paragraph(str(cell), styles["small"]) for cell in row] for row in files_rows],
        colWidths=[1.7 * inch, 4.8 * inch],
    )
    files_table.setStyle(table_style("#334155"))
    story.append(files_table)

    story.append(Paragraph("10. Testing and Verification", styles["h1"]))
    story.extend(
        paragraph_list(
            [
                "Verified that the app serves the homepage route.",
                "Verified that the preprocessed JSON endpoint returns role profile data.",
                "Verified that chat messages can be matched to known developer roles.",
                "Checked JavaScript syntax after adding the roadmap feature.",
                "Validated roadmap generation against real roles such as Data Scientist, AI / ML Engineer, Back-End Developer, and UX / UI Designer.",
            ],
            styles,
        )
    )

    story.append(Paragraph("11. Limitations and Future Work", styles["h1"]))
    story.extend(
        paragraph_list(
            [
                "The AI chat requires a valid Gemini API key in the .env file.",
                "Roadmaps only use skills available in the current survey profile, so missing libraries are not invented.",
                "The salary data is global and should be interpreted as survey-based guidance, not a guaranteed salary.",
                "Future improvements could add user accounts, downloadable personal study plans, more charts, and country-specific salary filters.",
            ],
            styles,
        )
    )

    story.append(Paragraph("Conclusion", styles["h1"]))
    story.append(
        Paragraph(
            "This project combines real data, AI mentorship, and interactive visual "
            "learning tools to help students explore technology careers with more "
            "confidence. The result is not just a chatbot, but a complete career "
            "guidance dashboard that explains each path, compares roles, and helps "
            "students plan what to learn next.",
            styles["body"],
        )
    )

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return OUTPUT_PATH


if __name__ == "__main__":
    output = build_report()
    print(f"Created {output}")
