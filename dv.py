
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==================================================
# PAGE SETUP
# ==================================================
st.set_page_config(
    page_title="Healthcare Insights",
    page_icon="🩺",
    layout="wide"
)

# ==================================================
# SAMPLE DATA
# Demonstration data only — not real patient records
# ==================================================
@st.cache_data
def create_sample_data():
    rng = np.random.default_rng(42)
    n = 500

    age = rng.integers(18, 86, n)
    conditions = rng.choice(
        ["Diabetes", "Hypertension", "Heart Disease",
         "Respiratory", "None"],
        n,
        p=[0.25, 0.25, 0.15, 0.12, 0.23]
    )

    df = pd.DataFrame({
        "Patient_ID": [f"P{i:04d}" for i in range(1, n + 1)],
        "Age": age,
        "Gender": rng.choice(["Female", "Male"], n),
        "Condition": conditions,
        "Blood_Sugar": np.clip(
            rng.normal(125, 32, n), 65, 260
        ).round(1),
        "Systolic_BP": np.clip(
            rng.normal(128, 17, n), 85, 200
        ).round().astype(int),
        "Exercise_Days": rng.integers(0, 8, n),
        "Sleep_Hours": np.clip(
            rng.normal(6.8, 1.2, n), 3, 11
        ).round(1),
        "Follow_Up": rng.choice(
            ["Completed", "Pending"], n, p=[0.72, 0.28]
        )
    })

    df["Age_Group"] = pd.cut(
        df["Age"],
        bins=[0, 20, 30, 40, 50, 60, 70, 120],
        labels=[
            "0–20", "21–30", "31–40", "41–50",
            "51–60", "61–70", "71+"
        ]
    )

    return df


# ==================================================
# DATA SOURCE
# ==================================================
st.sidebar.title("🩺 Healthcare Insights")
st.sidebar.caption("From Data to Better Care")

uploaded_file = st.sidebar.file_uploader(
    "Upload patient CSV (optional)",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        required = [
            "Age", "Condition", "Blood_Sugar",
            "Systolic_BP", "Exercise_Days",
            "Sleep_Hours", "Follow_Up"
        ]

        missing = [c for c in required if c not in df.columns]

        if missing:
            st.error(
                "Missing required columns: "
                + ", ".join(missing)
            )
            st.stop()

        df = df.copy()

        numeric_cols = [
            "Age", "Blood_Sugar", "Systolic_BP",
            "Exercise_Days", "Sleep_Hours"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=required)

        if df.empty:
            st.error("The uploaded CSV has no valid records.")
            st.stop()

        if "Patient_ID" not in df.columns:
            df["Patient_ID"] = [
                f"P{i:04d}" for i in range(1, len(df) + 1)
            ]

        if "Gender" not in df.columns:
            df["Gender"] = "Not specified"

        if "Age_Group" not in df.columns:
            df["Age_Group"] = pd.cut(
                df["Age"],
                bins=[0, 20, 30, 40, 50, 60, 70, 120],
                labels=[
                    "0–20", "21–30", "31–40", "41–50",
                    "51–60", "61–70", "71+"
                ]
            )

    except Exception as exc:
        st.error(f"Could not read this CSV: {exc}")
        st.stop()
else:
    df = create_sample_data()
    st.sidebar.info(
        "Showing synthetic demo data. Upload your own CSV "
        "to explore another dataset."
    )

# ==================================================
# SIDEBAR NAVIGATION
# ==================================================
page = st.sidebar.radio(
    "Explore the story",
    [
        "🏠 Overview",
        "👥 Patient Overview",
        "📊 Disease Analysis",
        "💊 Treatment Insights",
        "ℹ️ About"
    ]
)

# ==================================================
# HEADER
# ==================================================
st.title("💙 Patient Health Analysis")
st.markdown(
    "Every dataset tells a story. Explore patient profiles, "
    "health patterns, and follow-up opportunities — "
    "from understanding risk to supporting prevention."
)

st.caption(
    "Educational analytics only. This dashboard does not "
    "diagnose disease or replace a qualified clinician."
)

# ==================================================
# FILTERS
# ==================================================
st.sidebar.divider()
st.sidebar.subheader("🔎 Refine the story")

age_min = int(df["Age"].min())
age_max = int(df["Age"].max())

age_range = st.sidebar.slider(
    "Patient age range",
    min_value=age_min,
    max_value=age_max,
    value=(age_min, age_max)
)

condition_options = sorted(
    df["Condition"].dropna().astype(str).unique()
)

selected_conditions = st.sidebar.multiselect(
    "Health condition",
    options=condition_options,
    default=condition_options
)

filtered = df[
    df["Age"].between(age_range[0], age_range[1])
    & df["Condition"].astype(str).isin(selected_conditions)
].copy()

if filtered.empty:
    st.warning("No records match these filters. Change the selections.")
    st.stop()

# ==================================================
# OVERVIEW PAGE
# ==================================================
if page == "🏠 Overview":

    st.subheader("📖 Chapter 1: Who are our patients?")

    total = len(filtered)
    risk_count = int(
        (
            (filtered["Blood_Sugar"] >= 126)
            | (filtered["Systolic_BP"] >= 140)
        ).sum()
    )
    avg_age = filtered["Age"].mean()
    common_condition = filtered["Condition"].mode().iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Patients in view", f"{total:,}")
    c2.metric("Records with elevated readings", f"{risk_count:,}")
    c3.metric("Average age", f"{avg_age:.1f} years")
    c4.metric("Most common condition", str(common_condition))

    st.info(
        "Story so far: start by understanding who is represented "
        "in the data. The elevated-reading count is a screening "
        "indicator for this demo, not a medical diagnosis."
    )

    left, right = st.columns(2)

    with left:
        st.markdown("### 👥 Patient age groups")

        age_counts = (
            filtered.groupby("Age_Group", observed=False)
            .size()
            .reset_index(name="Patients")
        )

        fig_age = px.bar(
            age_counts,
            x="Age_Group",
            y="Patients",
            color="Patients",
            title="Patient Distribution by Age",
            labels={"Age_Group": "Age group"},
            color_continuous_scale="Blues"
        )

        st.plotly_chart(fig_age, use_container_width=True)

    with right:
        st.markdown("### 🩺 What conditions appear?")

        disease_counts = (
            filtered["Condition"]
            .value_counts()
            .rename_axis("Condition")
            .reset_index(name="Patients")
        )

        fig_disease = px.pie(
            disease_counts,
            names="Condition",
            values="Patients",
            hole=0.45,
            title="Condition Distribution"
        )

        st.plotly_chart(fig_disease, use_container_width=True)

    st.subheader("📖 Chapter 2: What patterns should we explore?")

    left, right = st.columns(2)

    with left:
        fig_sugar = px.histogram(
            filtered,
            x="Blood_Sugar",
            color="Condition",
            nbins=25,
            title="Blood Sugar Reading Distribution",
            labels={"Blood_Sugar": "Blood sugar reading"}
        )
        st.plotly_chart(fig_sugar, use_container_width=True)

    with right:
        fig_bp = px.scatter(
            filtered,
            x="Age",
            y="Systolic_BP",
            color="Condition",
            hover_data=["Exercise_Days", "Sleep_Hours"],
            title="Age vs Systolic Blood Pressure",
            labels={"Systolic_BP": "Systolic BP (mmHg)"}
        )
        st.plotly_chart(fig_bp, use_container_width=True)

    st.subheader("📖 Chapter 3: Turning insights into action")

    completed = (
        filtered["Follow_Up"].astype(str).str.lower()
        == "completed"
    ).mean() * 100

    c1, c2 = st.columns(2)

    c1.metric("Follow-ups completed", f"{completed:.1f}%")
    c2.metric("Follow-ups pending", f"{100 - completed:.1f}%")

    st.markdown(
        """
        **Suggested next steps for a healthcare team**

        - Review unusual readings with an authorized clinician.
        - Check which patients need follow-up appointments.
        - Explore whether age, activity, or sleep patterns
          are associated with different readings.
        - Use validated clinical guidance before making care decisions.
        """
    )

# ==================================================
# PATIENT OVERVIEW
# ==================================================
elif page == "👥 Patient Overview":

    st.subheader("👥 Chapter: Meet the patient population")

    left, right = st.columns(2)

    with left:
        gender_counts = (
            filtered["Gender"].astype(str)
            .value_counts()
            .rename_axis("Gender")
            .reset_index(name="Patients")
        )

        fig_gender = px.bar(
            gender_counts,
            x="Gender",
            y="Patients",
            color="Gender",
            title="Patient Profile by Gender"
        )
        st.plotly_chart(fig_gender, use_container_width=True)

    with right:
        fig_sleep = px.scatter(
            filtered,
            x="Sleep_Hours",
            y="Blood_Sugar",
            color="Condition",
            title="Sleep vs Blood Sugar Readings",
            labels={"Sleep_Hours": "Sleep (hours)"}
        )
        st.plotly_chart(fig_sleep, use_container_width=True)

    st.markdown("### Patient records")

    display_cols = [
        "Patient_ID", "Age", "Gender", "Condition",
        "Blood_Sugar", "Systolic_BP",
        "Exercise_Days", "Sleep_Hours", "Follow_Up"
    ]

    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "📥 Download filtered records",
        data=filtered[display_cols].to_csv(index=False).encode("utf-8"),
        file_name="filtered_patient_records.csv",
        mime="text/csv"
    )

# ==================================================
# DISEASE ANALYSIS
# ==================================================
elif page == "📊 Disease Analysis":

    st.subheader("📊 Chapter: Understanding health patterns")

    left, right = st.columns(2)

    with left:
        fig_condition_age = px.box(
            filtered,
            x="Condition",
            y="Age",
            color="Condition",
            title="Age Distribution by Condition"
        )
        st.plotly_chart(fig_condition_age, use_container_width=True)

    with right:
        fig_activity = px.box(
            filtered,
            x="Condition",
            y="Exercise_Days",
            color="Condition",
            title="Weekly Exercise Days by Condition"
        )
        st.plotly_chart(fig_activity, use_container_width=True)

    numeric = filtered[
        ["Age", "Blood_Sugar", "Systolic_BP",
         "Exercise_Days", "Sleep_Hours"]
    ]

    st.markdown("### 🔗 Relationships between measurements")

    fig_corr = px.imshow(
        numeric.corr(),
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlation Matrix"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    st.caption(
        "Correlation shows association, not proof that one factor "
        "causes another."
    )

# ==================================================
# TREATMENT INSIGHTS
# ==================================================
elif page == "💊 Treatment Insights":

    st.subheader("💊 Chapter: From observation to follow-up")

    followup_counts = (
        filtered["Follow_Up"].astype(str)
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Patients")
    )

    fig_follow = px.bar(
        followup_counts,
        x="Status",
        y="Patients",
        color="Status",
        title="Follow-up Status"
    )
    st.plotly_chart(fig_follow, use_container_width=True)

    st.markdown("### Records that may need review")

    pending = filtered[
        filtered["Follow_Up"].astype(str).str.lower() == "pending"
    ]

    st.write(f"Pending follow-up records: **{len(pending)}**")

    st.dataframe(
        pending[
            ["Patient_ID", "Age", "Condition",
             "Blood_Sugar", "Systolic_BP", "Follow_Up"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.warning(
        "This list is for administrative follow-up tracking, "
        "not for ranking urgency. A clinician must determine "
        "clinical priority using appropriate protocols."
    )

# ==================================================
# ABOUT
# ==================================================
else:

    st.subheader("ℹ️ About this project")

    st.markdown(
        """
        **Project:** Healthcare Insights — Storytelling with Data

        **Technologies:** Python, Streamlit, Pandas, Plotly

        **Purpose:** Explore patient demographics, condition
        distributions, measurements, and follow-up status.

        **Data:** Synthetic sample records are generated by default.
        Upload a compatible CSV to explore your own authorized dataset.

        **Privacy:** Do not upload identifiable or confidential
        patient records to a public GitHub repository or an
        unapproved deployment service.

        **Limitations:** This is a demonstration analytics tool.
        It does not diagnose illness, recommend medication,
        or replace professional medical judgment.
        """
    )

    st.markdown("### Required CSV columns")

    st.code(
        "Age, Condition, Blood_Sugar, Systolic_BP, "
        "Exercise_Days, Sleep_Hours, Follow_Up"
    )

    st.markdown("### The story in one sentence")

    st.success(
        "Understand the population → explore patterns → "
        "support appropriate follow-up → improve care processes."
    )
