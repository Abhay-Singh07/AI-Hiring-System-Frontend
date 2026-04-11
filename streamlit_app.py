import streamlit as st
import requests
import time
import pandas as pd
import json
import plotly.express as px

st.set_page_config(page_title="GenAI ATS", layout="wide")

BACKEND_URL = "https://ai-hiring-system-production.up.railway.app"

if "ranking" not in st.session_state:
    st.session_state.ranking = []

if "result" not in st.session_state:
    st.session_state.result = {}

st.title("🚀 GenAI Resume ATS")
st.caption("AI-powered candidate ranking using LLM + RAG + Hybrid Scoring")

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF)",
    type=["pdf"],
    accept_multiple_files=True
)

job_description = st.text_area("Paste Job Description")

if st.button("Analyze Candidates"):

    if uploaded_files and job_description:

        files = [
            ("files", (file.name, file.getvalue(), "application/pdf"))
            for file in uploaded_files
        ]

        data = {
            "job_description": job_description
        }

        with st.spinner("Analyzing resumes..."):

            progress = st.progress(0)

            for i in range(100):
                time.sleep(0.005)
                progress.progress(i + 1)

            try:
                response = requests.post(
                    f"{BACKEND_URL}/analyze",
                    files=files,
                    data=data,
                    timeout=120
                )

                if response.status_code != 200:
                    st.error(f"Error: {response.text}")
                    st.stop()

                result = response.json()

            except Exception:
                st.error("Backend connection failed")
                st.stop()

        ranking = result.get("ranking", [])

        if not ranking:
            st.warning("No valid results returned.")
            st.stop()

        st.session_state.ranking = ranking
        st.session_state.result = result

ranking = st.session_state.ranking
result = st.session_state.result

if ranking:

    top_candidate = ranking[0]

    st.success(
        f"🏆 Best Candidate: {top_candidate['candidate']} "
        f"({top_candidate['score']}%)"
    )

    df = pd.DataFrame([
        {
            "Candidate": c["candidate"],
            "Score": c["score"]
        }
        for c in ranking
    ])

    fig = px.bar(
        df,
        x="Candidate",
        y="Score",
        text="Score",
        color="Score",
        color_continuous_scale="Blues",
        title="Candidate Score Comparison"
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        xaxis_title="Candidate",
        yaxis_title="Score (%)",
        yaxis=dict(range=[0, 100])
    )

    st.plotly_chart(fig, use_container_width=True)

    st.header("🏆 Candidate Ranking")

    for idx, candidate in enumerate(ranking, start=1):

        analysis = candidate["analysis"]

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(f"#{idx} {candidate['candidate']}")

        with col2:
            st.metric("Score", f"{candidate['score']}%")

        decision = analysis.get("selection_decision", "N/A")

        if decision == "Selected":
            st.success(f"✅ {decision}")
        elif decision == "Borderline":
            st.warning(f"⚠️ {decision}")
        else:
            st.error(f"❌ {decision}")

        with st.expander("View Full Analysis"):

            st.write("### 🧠 Summary")
            st.write(analysis.get("summary", ""))

            st.write("### 🎯 Matched Skills")
            st.write(analysis.get("matched_skills", []))

            st.write("### ❌ Missing Skills")
            st.write(analysis.get("missing_skills", []))

            st.write("### 📊 Score Breakdown")
            st.json(analysis.get("score_breakdown", {}))

            st.write("### 💡 Feedback")
            st.write(analysis.get("resume_feedback", ""))

            st.write("### 🧾 Decision Reasoning")

            reasoning = analysis.get("decision_reasoning", [])

            if reasoning:
                for point in reasoning:
                    st.write(f"- {point}")
            else:
                st.write("No reasoning provided.")

    st.download_button(
        "📥 Download Results",
        data=json.dumps(result, indent=2),
        file_name="ranking.json",
        mime="application/json"
    )

    st.header("🤖 Dual Copilot System")

    tab1, tab2 = st.tabs(
        ["👔 Recruiter Copilot", "🧑‍💻 Candidate Copilot"]
    )

    with tab1:

        recruiter_query = st.text_input(
            "Ask recruiter questions",
            placeholder="Who is best fit and why?"
        )

        if st.button("Ask Recruiter Copilot"):

            if recruiter_query:

                payload = {
                    "query": recruiter_query,
                    "context": json.dumps(ranking, indent=2),
                    "type": "recruiter"
                }

                with st.spinner("Thinking..."):

                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/copilot",
                            json=payload,
                            timeout=120
                        )

                        answer = response.json().get(
                            "answer",
                            "No response"
                        )

                        st.info(answer)

                    except Exception:
                        st.error("Copilot unavailable")

    with tab2:

        candidate_names = [
            c["candidate"] for c in ranking
        ]

        selected_candidate = st.selectbox(
            "Select Candidate",
            candidate_names
        )

        candidate_query = st.text_input(
            "Ask candidate questions",
            placeholder="How can I improve for this role?"
        )

        if st.button("Ask Candidate Copilot"):

            if selected_candidate and candidate_query:

                selected_data = next(
                    c for c in ranking
                    if c["candidate"] == selected_candidate
                )

                payload = {
                    "query": candidate_query,
                    "context": json.dumps(selected_data, indent=2),
                    "type": "candidate"
                }

                with st.spinner("Thinking..."):

                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/copilot",
                            json=payload,
                            timeout=120
                        )

                        answer = response.json().get(
                            "answer",
                            "No response"
                        )

                        st.info(answer)

                    except Exception:
                        st.error("Copilot unavailable")

else:
    st.info("Upload resumes and analyze candidates to begin.")
