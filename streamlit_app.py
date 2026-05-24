import json
import os
from pathlib import Path

import streamlit as st

try:
    import google.generativeai as genai
except Exception:
    genai = None


DATA_FILE = Path(__file__).parent / "student_advisor_data.json"
REPORT_FILE = Path(__file__).parent / "Student_Career_Advisor_Project_Report.pdf"


st.set_page_config(
    page_title="Student Career Advisor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_advisor_data():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_secret(name):
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.environ.get(name)


def money(value):
    if not value:
        return "N/A"
    return f"${int(value):,}"


def top_names(items, limit=5):
    return [item.get("name", "") for item in items[:limit] if item.get("name")]


def find_matched_role(message, role_profiles, role_aliases):
    message_lower = message.lower()

    for alias in sorted(role_aliases.keys(), key=len, reverse=True):
        if alias in message_lower:
            return role_aliases[alias]

    for role in sorted(role_profiles.keys(), key=len, reverse=True):
        if role.lower() in message_lower:
            return role

    return None


def build_roadmap_skills(profile):
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

    return skills


def status_for(value, is_next):
    if value >= 80:
        return "mastered"
    if is_next:
        return "next"
    if value >= 40:
        return "learning"
    return "pending"


def mermaid_html(skills, progress):
    next_skill = next((skill for skill in skills if progress.get(skill, 0) < 80), None)
    lines = [
        "flowchart LR",
        "classDef mastered fill:#065f46,stroke:#10b981,color:#ecfdf5,stroke-width:2px;",
        "classDef learning fill:#164e63,stroke:#06b6d4,color:#ecfeff,stroke-width:2px;",
        "classDef next fill:#78350f,stroke:#f59e0b,color:#fff7ed,stroke-width:3px;",
        "classDef pending fill:#111827,stroke:#475569,color:#cbd5e1,stroke-width:1px;",
    ]

    for index, skill in enumerate(skills):
        clean = skill.replace('"', "'").replace("[", "(").replace("]", ")")
        lines.append(f'n{index}["{clean}"]')
        if index:
            lines.append(f"n{index - 1} --> n{index}")

    for index, skill in enumerate(skills):
        lines.append(f"class n{index} {status_for(progress.get(skill, 0), skill == next_skill)};")

    chart = "\n".join(lines)
    return f"""
    <div class="mermaid">{chart}</div>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
      mermaid.initialize({{ startOnLoad: true, theme: "base", securityLevel: "strict" }});
    </script>
    """


def generate_advisor_reply(message, matched_role, profile):
    api_key = get_secret("GEMINI_API_KEY")

    if not api_key or not genai:
        if matched_role and profile:
            return (
                f"You are exploring **{matched_role}**. Based on the survey profile, "
                f"start with **{', '.join(top_names(profile.get('languages', []), 3))}**. "
                f"The median salary in the dataset is **{money(profile.get('salary', {}).get('median_usd'))}**, "
                f"with median coding experience of **{profile.get('experience', {}).get('median_years', 'N/A')} years**."
            )
        return (
            "Tell me a career track such as Data Scientist, Back-End Developer, "
            "AI / ML Engineer, Cybersecurity Engineer, or Full-Stack Developer."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=(
            "You are a warm Student Career Advisor. Give concise, practical advice. "
            "When survey data is provided, use those exact figures and do not invent statistics."
        ),
    )

    if matched_role and profile:
        salary = profile.get("salary", {})
        experience = profile.get("experience", {})
        context = (
            f"Role: {matched_role}\n"
            f"Sample size: {profile.get('sample_count', 0)}\n"
            f"Median salary: {money(salary.get('median_usd'))}\n"
            f"Salary range: {money(salary.get('p25_usd'))} to {money(salary.get('p75_usd'))}\n"
            f"Median coding experience: {experience.get('median_years', 'N/A')} years\n"
            f"Top languages: {', '.join(top_names(profile.get('languages', []), 5))}\n"
            f"Top databases: {', '.join(top_names(profile.get('databases', []), 5))}\n"
            f"Top frameworks: {', '.join(top_names(profile.get('frameworks', []), 5))}\n"
            f"Top platforms: {', '.join(top_names(profile.get('platforms', []), 5))}\n"
        )
        prompt = f"{context}\nStudent question: {message}"
    else:
        prompt = message

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        return f"I could not reach Gemini right now, but the dashboard still works. Error: {exc}"


def render_metric_cards(profile):
    salary = profile.get("salary", {})
    experience = profile.get("experience", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Survey Responses", f"{profile.get('sample_count', 0):,}")
    col2.metric("Median Salary", money(salary.get("median_usd")))
    col3.metric("Salary Range", f"{money(salary.get('p25_usd'))} - {money(salary.get('p75_usd'))}")
    col4.metric("Median Experience", f"{experience.get('median_years', 'N/A')} yrs")


def render_bar_list(title, items, sample_count, limit=5):
    st.subheader(title)
    if not items:
        st.caption("No data available.")
        return

    max_count = max(item.get("count", 0) for item in items[:limit]) or 1
    for item in items[:limit]:
        name = item.get("name", "Unknown")
        count = item.get("count", 0)
        pct = round((count / sample_count) * 100) if sample_count else 0
        st.write(f"**{name}** · {pct}%")
        st.progress(count / max_count)


def render_distribution(title, values):
    st.subheader(title)
    total = sum(values.values()) or 1
    rows = sorted(values.items(), key=lambda item: item[1], reverse=True)[:5]
    for label, count in rows:
        pct = round((count / total) * 100)
        st.write(f"**{label}** · {pct}%")
        st.progress(pct / 100)


def render_roadmap(role, profile):
    st.subheader("Learning Roadmap Visualizer")
    st.caption("What do you know about this track? Rate your confidence in each skill.")

    skills = build_roadmap_skills(profile)
    if not skills:
        st.info("No roadmap data is available for this role yet.")
        return

    progress = {}
    for skill in skills:
        key = f"roadmap_{role}_{skill}"
        progress[skill] = st.slider(
            f"How confident are you with {skill}?",
            min_value=0,
            max_value=100,
            value=st.session_state.get(key, 0),
            step=5,
            key=key,
        )

    average = round(sum(progress.values()) / len(skills))
    next_skill = next((skill for skill in skills if progress.get(skill, 0) < 80), None)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Roadmap Readiness", f"{average}%")
        if next_skill:
            st.warning(f"Next priority: {next_skill}")
        else:
            st.success("Every roadmap skill is at 80% or higher.")

    with col2:
        st.components.v1.html(mermaid_html(skills, progress), height=260, scrolling=True)


def render_role_dashboard(role, profile):
    st.header(role)
    render_metric_cards(profile)

    tab_overview, tab_skills, tab_roadmap = st.tabs(["Overview", "Skills & Background", "Roadmap"])

    with tab_overview:
        left, right = st.columns(2)
        with left:
            render_bar_list("Top Languages", profile.get("languages", []), profile.get("sample_count", 0))
        with right:
            render_bar_list("Top Databases", profile.get("databases", []), profile.get("sample_count", 0))

    with tab_skills:
        left, right = st.columns(2)
        with left:
            render_bar_list("Top Frameworks", profile.get("frameworks", []), profile.get("sample_count", 0))
            render_distribution("Education Background", profile.get("education", {}))
        with right:
            render_bar_list("Top Platforms / Tools", profile.get("platforms", []), profile.get("sample_count", 0))
            render_distribution("Employment Type", profile.get("employment", {}))

    with tab_roadmap:
        render_roadmap(role, profile)


def render_comparison(role_profiles):
    st.header("Compare Careers")
    roles = sorted(role_profiles.keys())
    role_a, role_b = st.columns(2)
    selected_a = role_a.selectbox("Career Path A", roles, index=roles.index("Data Scientist") if "Data Scientist" in roles else 0)
    selected_b = role_b.selectbox("Career Path B", roles, index=roles.index("Back-End Developer") if "Back-End Developer" in roles else 1)

    if selected_a == selected_b:
        st.warning("Choose two different roles to compare.")
        return

    rows = []
    for role in [selected_a, selected_b]:
        profile = role_profiles[role]
        rows.append(
            {
                "Role": role,
                "Responses": f"{profile.get('sample_count', 0):,}",
                "Median Salary": money(profile.get("salary", {}).get("median_usd")),
                "Median Experience": f"{profile.get('experience', {}).get('median_years', 'N/A')} yrs",
                "Top Languages": ", ".join(top_names(profile.get("languages", []), 4)),
                "Roadmap": " -> ".join(build_roadmap_skills(profile)),
            }
        )

    st.table(rows)


def main():
    data = load_advisor_data()
    role_profiles = data.get("role_profiles", {})
    role_aliases = data.get("role_aliases", {})
    roles = sorted(role_profiles.keys())

    st.title("Student Career Advisor")
    st.write(
        "Explore developer career tracks with real survey statistics, AI guidance, "
        "career comparison, and personalized learning roadmaps."
    )

    with st.sidebar:
        st.header("Explore Paths")
        selected_role = st.selectbox("Choose a career track", roles)
        st.caption("Data source: Stack Overflow Developer Survey 2024")
        st.divider()
        st.info("For full AI chat, add GEMINI_API_KEY in Streamlit secrets.")

    chat_tab, dashboard_tab, compare_tab, report_tab = st.tabs(
        ["AI Advisor", "Career Dashboard", "Compare Careers", "Project Report"]
    )

    with chat_tab:
        st.header("Ask the Career Advisor")
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": "Hi. Ask me about a track like Data Scientist, Back-End Developer, AI / ML Engineer, or Cybersecurity Engineer.",
                }
            ]

        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_message = st.chat_input("Ask about a career track...")
        if user_message:
            matched_role = find_matched_role(user_message, role_profiles, role_aliases)
            profile = role_profiles.get(matched_role) if matched_role else None

            st.session_state.chat_messages.append({"role": "user", "content": user_message})
            with st.chat_message("user"):
                st.markdown(user_message)

            reply = generate_advisor_reply(user_message, matched_role, profile)
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)

            if matched_role:
                st.session_state.selected_from_chat = matched_role
                st.success(f"Matched track: {matched_role}. Open the Career Dashboard tab to see the visuals.")

    with dashboard_tab:
        role_to_render = st.session_state.get("selected_from_chat", selected_role)
        render_role_dashboard(role_to_render, role_profiles[role_to_render])

    with compare_tab:
        render_comparison(role_profiles)

    with report_tab:
        st.header("Project Report")
        if REPORT_FILE.exists():
            st.write("Download the PDF report that explains the project idea, data, architecture, and features.")
            st.download_button(
                "Download PDF Report",
                data=REPORT_FILE.read_bytes(),
                file_name="Student_Career_Advisor_Project_Report.pdf",
                mime="application/pdf",
            )
        else:
            st.info("The PDF report file is not available in this repository.")


if __name__ == "__main__":
    main()
