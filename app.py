import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Technical Hiring Program",
    page_icon="📊",
    layout="wide"
)

TARGET = 5000

@st.cache_data
def load_data():
    df = pd.read_csv("Candidates_Prepared.csv")

    for col in ["Application_Date", "Hire_Date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["Clean_Days_to_Hire"] = pd.to_numeric(
        df["Clean_Days_to_Hire"], errors="coerce"
    )

    return df

df = load_data()


st.markdown("""
<style>
.stApp {
    background-color: #F5F7FB;
    color: #172B4D;
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E5EAF2;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #E5EAF2;
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 3px 12px rgba(23, 43, 77, 0.04);
}

[data-testid="stMetricLabel"] {
    color: #526581;
}

[data-testid="stMetricValue"] {
    color: #163B70;
    font-weight: 700;
}

[data-testid="stPlotlyChart"] {
    background-color: #FFFFFF;
    border: 1px solid #E5EAF2;
    border-radius: 14px;
    padding: 8px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    margin-top: 16px;
    margin-bottom: 12px;
}

.stTabs [data-baseweb="tab"] {
    padding: 12px 20px;
    border-radius: 10px;
}

.stTabs [aria-selected="true"] {
    background-color: #E8EFFC;
    color: #1D4ED8;
}

.hero {
    background: linear-gradient(120deg, #12345B, #2458A0);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 24px;
    color: white;
}

.hero h1 {
    color: white;
    font-size: 30px;
    margin: 0 0 8px;
    padding: 0;
}

.hero p {
    color: #DBEAFE;
    margin: 0;
    font-size: 15px;
}

.hero .eyebrow {
    color: #BFDBFE;
    font-size: 12px;
    letter-spacing: 2px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# تنسيق موحد للرسوم
import plotly.io as pio

pio.templates["hiring_dashboard"] = pio.templates["plotly_white"]
pio.templates["hiring_dashboard"].layout.update(
    font=dict(family="Arial", size=13, color="#334155"),
    title=dict(font=dict(size=18, color="#172B4D")),
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    margin=dict(l=20, r=20, t=65, b=30),
    colorway=["#2563EB", "#0D9488", "#F59E0B", "#7C3AED"],
    xaxis=dict(gridcolor="#EEF2F7", zeroline=False),
    yaxis=dict(gridcolor="#EEF2F7", zeroline=False),
    hoverlabel=dict(bgcolor="white", font_size=13)
)

pio.templates.default = "hiring_dashboard"

st.markdown("""
<div class="hero">
    <div class="eyebrow">WORKFORCE DEVELOPMENT</div>
    <h1>Technical Hiring Program</h1>
    <p>Progress toward 5,000 hires · Performance, opportunities and next actions</p>
</div>
""", unsafe_allow_html=True)

st.caption("Synthetic assessment dataset")


# مؤشرات البرنامج كاملة
total_hired = int(df["Status"].eq("Hired").sum())
remaining = max(TARGET - total_hired, 0)

st.subheader("Overall program progress")

cols = st.columns(4)
cols[0].metric("Hiring target", f"{TARGET:,}")
cols[1].metric("Total hired", f"{total_hired:,}")
cols[2].metric("Remaining hires", f"{remaining:,}")
cols[3].metric("Target achievement", f"{total_hired / TARGET:.1%}")

st.progress(min(total_hired / TARGET, 1.0))

st.caption(
    "Program KPIs above show the full dataset. "
    "Filters below apply to the selected-candidate KPIs and analysis."
)

# الفلاتر
st.sidebar.header("Explore the data")
st.sidebar.caption(
    "Select one or more options. Leave a filter empty to include all."
)

filtered = df.copy()

for column, label in [
    ("Region_Group", "Region group"),
    ("Technical_Role", "Technical role"),
    ("Employer", "Employer"),
    ("Hiring_Source", "Hiring source")
]:
    options = sorted(df[column].dropna().unique().tolist())
    selected = st.sidebar.multiselect(label, options)

    if selected:
        filtered = filtered[filtered[column].isin(selected)]

if filtered.empty:
    st.warning("No candidates match these filters.")
    st.stop()

hired = filtered[filtered["Status"].eq("Hired")].copy()
durations = hired["Clean_Days_to_Hire"].dropna()

st.subheader("Performance for your selection")

cols = st.columns(4)
cols[0].metric("Hired", f"{len(hired):,}")
cols[1].metric(
    "Active pipeline",
    f"{filtered['Status'].eq('Pipeline').sum():,}"
)
cols[2].metric(
    "Hiring rate",
    f"{len(hired) / len(filtered):.1%}"
)
cols[3].metric(
    "Average time to hire",
    f"{durations.mean():.1f} days" if len(durations) else "N/A"
)

st.caption(
    f"Selected candidates: {len(filtered):,}. "
    "Hiring rate = hired / all selected candidates, including active pipeline. "
    f"Time-to-hire analysis uses {len(durations):,} valid hired records."
)

# جدول مقارنة: العدد والنسبة معًا
def performance_table(column):
    result = (
        filtered.groupby(column)
        .agg(
            Candidates=("Candidate_ID", "size"),
            Hired=("Status", lambda values: values.eq("Hired").sum()),
            Pipeline=("Status", lambda values: values.eq("Pipeline").sum())
        )
        .reset_index()
    )

    result["Hiring_Rate"] = result["Hired"] / result["Candidates"]
    return result.sort_values("Hired", ascending=False)

def hiring_chart(table, column, title):
    fig = px.bar(
        table.sort_values("Hired"),
        x="Hired",
        y=column,
        orientation="h",
        title=title,
        text="Hired",
        hover_data={
            "Candidates": True,
            "Pipeline": True,
            "Hiring_Rate": ":.1%"
        },
        color_discrete_sequence=["#2563EB"]
    )

    fig.update_layout(
        xaxis_title="Hired candidates",
        yaxis_title=None
    )
    return fig

region = performance_table("Region_Group")
role = performance_table("Technical_Role")
employer = performance_table("Employer")
source = performance_table("Hiring_Source")


tab_analysis, tab_actions, tab_data = st.tabs([
    "Performance analysis",
    "Insights & actions",
    "Data quality & records"
])

with tab_analysis:
    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            hiring_chart(region, "Region_Group", "Hires by region group"),
            width="stretch"
        )

    with right:
        st.plotly_chart(
            hiring_chart(role, "Technical_Role", "Hires by technical role"),
            width="stretch"
        )

    # الشركات ومصادر التقديم
    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            hiring_chart(employer.head(10), "Employer", "Top 10 employers by hires"),
            width="stretch"
        )

    with right:
        source_chart = px.bar(
            source.sort_values("Hiring_Rate"),
            x="Hiring_Rate",
            y="Hiring_Source",
            orientation="h",
            title="Hiring rate by source",
            hover_data=["Candidates", "Hired", "Pipeline"],
            color_discrete_sequence=["#0D9488"]
        )

        source_chart.update_layout(
            xaxis_title="Hired / candidates",
            xaxis_tickformat=".0%",
            yaxis_title=None
        )

        st.plotly_chart(source_chart, width="stretch")


    # مساهمة مصادر التقديم
    st.markdown("#### Hiring source contribution")

    source_contribution = source.copy()

    source_contribution["Share_of_Selected_Hires_Percent"] = (
        source_contribution["Hired"] / len(hired) * 100
        if len(hired) else float("nan")
    )

    source_contribution["Hiring_Rate_Percent"] = (
        source_contribution["Hiring_Rate"] * 100
    )

    source_contribution = source_contribution.sort_values(
        ["Hired", "Candidates"], ascending=False
    )

    st.dataframe(
        source_contribution[
            [
                "Hiring_Source",
                "Candidates",
                "Hired",
                "Pipeline",
                "Share_of_Selected_Hires_Percent",
                "Hiring_Rate_Percent"
            ]
        ].rename(columns={
            "Hiring_Source": "Hiring source",
            "Share_of_Selected_Hires_Percent": "Share of selected hires (%)",
            "Hiring_Rate_Percent": "Hiring rate (%)"
        }),
        hide_index=True,
        width="stretch",
        column_config={
            "Share of selected hires (%)":
                st.column_config.NumberColumn(format="%.1f"),
            "Hiring rate (%)":
                st.column_config.NumberColumn(format="%.1f")
        }
    )

    if len(hired):
        leading_source = source_contribution.iloc[0]

        st.info(
            f"{leading_source['Hiring_Source']} contributes the most "
            f"selected hires: {int(leading_source['Hired']):,}, "
            f"representing "
            f"{leading_source['Share_of_Selected_Hires_Percent']:.1f}% "
            "of hires in the current selection."
        )

    st.caption(
        "Contribution share = source hires / all selected hires. "
        "Hiring rate = source hires / candidates from that source, "
        "including active pipeline candidates. "
        "A high contribution count is different from a high hiring rate."
    )

    # الاتجاه الزمني
    st.subheader("Hiring trend")

    # استخدام السجلات المجتازة لفحص التواريخ في مرحلة التجهيز
    trend_records = hired[
        hired["Clean_Days_to_Hire"].notna()
    ].copy()

    included_count = len(trend_records)
    excluded_count = len(hired) - included_count
    coverage = included_count / len(hired) if len(hired) else 0

    st.caption(
        f"Date-checked records: {included_count:,} of "
        f"{len(hired):,} selected hires ({coverage:.1%} coverage). "
        f"Excluded from this chart: {excluded_count:,}."
    )

    if trend_records.empty:
        st.info(
            "No hired records pass the date checks for this selection."
        )
    else:
        monthly = (
            trend_records
            .set_index("Hire_Date")
            .resample("MS")
            .size()
            .rename("Hires")
            .reset_index()
        )

        fig = px.line(
            monthly,
            x="Hire_Date",
            y="Hires",
            markers=True,
            title="Monthly hires — date-checked records only",
            labels={
                "Hire_Date": "Hire month",
                "Hires": "Hired candidates"
            },
            color_discrete_sequence=["#2563EB"]
        )

        fig.update_layout(
            xaxis=dict(
                dtick="M1",
                tickformat="%b %Y"
            )
        )

        st.plotly_chart(fig, width="stretch")

    st.warning(
        "This chart excludes records with missing dates, "
        "hire dates before application dates, or dates beyond "
        "the reporting cutoff (30 September 2026). "
        "It shows a subset of hires, not the complete program trend. "
        "Original dates remain unchanged, and total hiring KPIs "
        "retain all records marked Hired."
    )

    # تقييم المسار نحو المستهدف
    st.markdown("#### Path to target — overall program")

    program_hires = df[df["Status"].eq("Hired")].copy()
    program_hired_count = len(program_hires)
    program_gap = max(TARGET - program_hired_count, 0)
    program_pipeline = int(df["Status"].eq("Pipeline").sum())

    minimum_external_hires = max(
        program_gap - program_pipeline, 0
    )

    program_valid = program_hires[
        program_hires["Clean_Days_to_Hire"].notna()
    ]

    date_coverage = (
        len(program_valid) / program_hired_count
        if program_hired_count else 0
    )

    st.caption(
        "This assessment uses the full program, regardless of sidebar filters."
    )

    st.write(
        f"**Remaining requirement:** {program_gap:,} hires. "
        f"**Active pipeline:** {program_pipeline:,} candidates."
    )

    st.write(
        f"Even with 100% conversion of the current active pipeline, "
        f"at least **{minimum_external_hires:,} further hires** "
        "would be required outside that pipeline. "
        "This is a best-case capacity calculation, not a forecast."
    )

    if not program_valid.empty:
        program_monthly = (
            program_valid.set_index("Hire_Date")
            .resample("MS").size()
            .rename("Hires")
        )

        # مقارنة آخر شهرين مكتملين حتى نهاية التقرير
        completed_months = program_monthly[
            program_monthly.index <= pd.Timestamp("2026-09-01")
        ]

        if len(completed_months) >= 2:
            previous_count = int(completed_months.iloc[-2])
            latest_count = int(completed_months.iloc[-1])
            previous_month = completed_months.index[-2].strftime("%b %Y")
            latest_month = completed_months.index[-1].strftime("%b %Y")

            st.write(
                f"**Observed date-checked trend:** "
                f"{previous_count:,} hires in {previous_month}, "
                f"compared with {latest_count:,} in {latest_month}. "
                "These counts describe the included records only."
            )

    st.warning(
        f"Date-checked records cover {date_coverage:.1%} of program hires. "
        "Exclusions may distort the observed trend, so it cannot establish "
        "a reliable program-wide hiring pace. The current pipeline alone "
        "is insufficient to close the gap, and reaching the target by a "
        "deadline cannot be assessed without an agreed completion date, "
        "validated dates and future hiring commitments."
    )

    # المراحل الحالية ومدة التوظيف
    left, right = st.columns(2)

    with left:
        stages = (
            filtered["Current_Stage"]
            .value_counts()
            .rename_axis("Stage")
            .reset_index(name="Candidates")
        )

        fig = px.bar(
            stages.sort_values("Candidates"),
            x="Candidates",
            y="Stage",
            orientation="h",
            title="Current recruitment stages",
            text="Candidates"
        )

        st.plotly_chart(fig, width="stretch")

        st.caption(
            "Latest-stage snapshot. Counts do not represent "
            "historical transitions or stage-to-stage conversion rates."
        )

    with right:
        time_by_role = (
            hired.groupby("Technical_Role")["Clean_Days_to_Hire"]
            .agg(Mean_Days="mean", Valid_Hires="count")
            .reset_index()
            .query("Valid_Hires > 0")
        )

        if not time_by_role.empty:
            fig = px.bar(
                time_by_role.sort_values("Mean_Days"),
                x="Mean_Days",
                y="Technical_Role",
                orientation="h",
                title="Average time to hire by role",
                hover_data=["Valid_Hires"],
                color_discrete_sequence=["#F59E0B"]
            )

            fig.update_layout(
                xaxis_title="Days",
                yaxis_title=None
            )

            st.plotly_chart(fig, width="stretch")

    # تحليل توزيع المدة والقيم غير المعتادة
    st.subheader("Time-to-hire distribution & unusual durations")

    time_records = hired[
        hired["Clean_Days_to_Hire"].notna()
    ].copy()

    if time_records.empty:
        st.info("No valid hiring durations match the current filters.")

    else:
        # حساب الحد من بيانات البرنامج كاملة لضمان ثباته مع الفلاتر
        reference_durations = df.loc[
            df["Status"].eq("Hired"),
            "Clean_Days_to_Hire"
        ].dropna()

        q1 = reference_durations.quantile(0.25)
        q3 = reference_durations.quantile(0.75)
        iqr = q3 - q1
        upper_limit = q3 + 1.5 * iqr

        enough_data = len(reference_durations) >= 4 and iqr > 0

        fig = px.histogram(
            time_records,
            x="Clean_Days_to_Hire",
            nbins=25,
            title="How are valid hiring durations distributed?",
            color_discrete_sequence=["#2563EB"],
            labels={"Clean_Days_to_Hire": "Time to hire (days)"}
        )

        fig.add_vline(
            x=time_records["Clean_Days_to_Hire"].median(),
            line_dash="dash",
            line_color="#0D9488",
            annotation_text="Selected median"
        )

        if enough_data:
            fig.add_vline(
                x=upper_limit,
                line_dash="dot",
                line_color="#D97706",
                annotation_text="Program IQR upper threshold"
            )

        fig.update_layout(
            yaxis_title="Hired candidates",
            bargap=0.08
        )

        st.plotly_chart(fig, width="stretch")

        st.caption(
            f"Distribution covers {len(time_records):,} date-checked "
            "hires in the current selection. Records excluded during "
            "date preparation remain excluded."
        )

        if enough_data:
            long_records = time_records[
                time_records["Clean_Days_to_Hire"].gt(upper_limit)
            ].copy()

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Program upper threshold",
                f"{upper_limit:.1f} days"
            )
            col2.metric(
                "Unusually long durations",
                f"{len(long_records):,}"
            )
            col3.metric(
                "Share of valid selected hires",
                f"{len(long_records) / len(time_records):.1%}"
            )

            st.caption(
                "Upper threshold = Q3 + 1.5 × (Q3 − Q1), calculated "
                "from all valid hired records in the program. "
                "It stays fixed when filters change. This is a statistical "
                "review flag, not a service target or proof of an error."
            )

            if long_records.empty:
                st.success(
                    "No selected durations exceed the program IQR threshold. "
                    "This does not establish that recruitment is fast; "
                    "no agreed time-to-hire target is supplied."
                )

            else:
                role_review = (
                    time_records.groupby("Technical_Role")
                    .agg(
                        Valid_Hires=("Candidate_ID", "size"),
                        Median_Days=("Clean_Days_to_Hire", "median")
                    )
                    .reset_index()
                )

                long_counts = (
                    long_records.groupby("Technical_Role").size()
                )

                role_review["Long_Durations"] = (
                    role_review["Technical_Role"]
                    .map(long_counts)
                    .fillna(0)
                    .astype(int)
                )

                role_review["Long_Duration_Share_Percent"] = (
                    role_review["Long_Durations"]
                    / role_review["Valid_Hires"] * 100
                )

                role_review = role_review.sort_values(
                    ["Long_Durations", "Long_Duration_Share_Percent"],
                    ascending=False
                )

                st.markdown("**Roles with durations requiring review**")

                st.dataframe(
                    role_review,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Long_Duration_Share_Percent":
                            st.column_config.NumberColumn(
                                "Long duration share (%)",
                                format="%.1f"
                            ),
                        "Median_Days":
                            st.column_config.NumberColumn(
                                "Median days", format="%.1f"
                            )
                    }
                )

                with st.expander("View flagged records"):
                    st.dataframe(
                        long_records[
                            [
                                "Candidate_ID",
                                "Technical_Role",
                                "Employer",
                                "Application_Date",
                                "Hire_Date",
                                "Clean_Days_to_Hire"
                            ]
                        ].sort_values(
                            "Clean_Days_to_Hire",
                            ascending=False
                        ),
                        hide_index=True,
                        width="stretch"
                    )

                st.info(
                    "Review these cases with recruitment teams to understand "
                    "the reasons for long durations. Keep them in the duration "
                    "metrics unless a verified data error is found. "
                    "Stage-specific delays cannot be identified without "
                    "stage entry and exit timestamps."
                )

        else:
            st.info(
                "The program reference has too few records or no IQR spread; "
                "an IQR-based long-duration classification is not applied."
            )

    # خصائص المرشحات
    st.subheader("Candidate profile")

    profile_options = {
        "Education major": "Education_Major",
        "Experience level": "Experience",
        "Age group": "Age",
        "Assessment score": "Assessment_Score",
        "Interview score": "Interview_Score"
    }

    selected_profile = st.selectbox(
        "Compare hiring outcomes by",
        options=list(profile_options.keys()),
        key="candidate_profile_choice"
    )

    profile_column = profile_options[selected_profile]
    profile_data = filtered.copy()

    if profile_column == "Age":
        values = pd.to_numeric(
            profile_data[profile_column], errors="coerce"
        )

        # الفئات محددة للتحليل وليست شروط أهلية للبرنامج
        profile_data["Profile_Group"] = pd.cut(
            values,
            bins=[0, 20, 25, 30, 35, float("inf")],
            labels=["Under 20", "20–24", "25–29", "30–34", "35+"],
            right=False
        ).astype("string").fillna("Missing / invalid")

        category_order = [
            "Under 20", "20–24", "25–29",
            "30–34", "35+", "Missing / invalid"
        ]

        st.caption(
            "Age bands are analytical groupings, not program eligibility rules."
        )

    elif profile_column in ["Assessment_Score", "Interview_Score"]:
        values = pd.to_numeric(
            profile_data[profile_column], errors="coerce"
        )

        # افتراض مقياس 0–100 مع إظهار القيم الخارجة عنه
        valid_scores = values.where(values.between(0, 100))

        profile_data["Profile_Group"] = pd.cut(
            valid_scores,
            bins=[0, 60, 70, 80, 90, 101],
            labels=["0–59", "60–69", "70–79", "80–89", "90–100"],
            right=False
        ).astype("string").fillna("Missing / outside 0–100")

        category_order = [
            "0–59", "60–69", "70–79",
            "80–89", "90–100", "Missing / outside 0–100"
        ]

        st.caption(
            "Assumption: recorded scores use a 0–100 scale. "
            "Bands are analytical groupings, not pass/fail thresholds."
        )

        st.warning(
            "Scores are analysed as recorded. The supplied definitions "
            "do not confirm that every candidate completed this stage. "
            "Comparisons are descriptive and do not establish that "
            "scores caused hiring outcomes."
        )

    else:
        profile_data["Profile_Group"] = (
            profile_data[profile_column]
            .astype("string")
            .fillna("Missing")
        )
        category_order = None

    profile_summary = (
        profile_data
        .groupby("Profile_Group", dropna=False)
        .agg(
            Candidates=("Candidate_ID", "size"),
            Hired=("Status", lambda x: x.eq("Hired").sum()),
            Pipeline=("Status", lambda x: x.eq("Pipeline").sum()),
            Not_Selected=("Status", lambda x: x.eq("Not Selected").sum())
        )
        .reset_index()
    )

    profile_summary["Hiring_Rate_Percent"] = (
        profile_summary["Hired"]
        / profile_summary["Candidates"]
        * 100
    )

    if category_order is not None:
        order_map = {
            label: position
            for position, label in enumerate(category_order)
        }

        profile_summary = (
            profile_summary
            .assign(
                Sort_Order=profile_summary["Profile_Group"].map(order_map)
            )
            .sort_values("Sort_Order")
            .drop(columns="Sort_Order")
        )
    else:
        profile_summary = profile_summary.sort_values(
            "Hiring_Rate_Percent"
        )

    fig = px.bar(
        profile_summary,
        x="Hiring_Rate_Percent",
        y="Profile_Group",
        orientation="h",
        text="Hiring_Rate_Percent",
        title=f"Hiring rate by {selected_profile.lower()}",
        hover_data={
            "Candidates": True,
            "Hired": True,
            "Pipeline": True,
            "Not_Selected": True,
            "Hiring_Rate_Percent": ":.1f"
        },
        color_discrete_sequence=["#2563EB"],
        labels={
            "Hiring_Rate_Percent": "Hiring rate (%)",
            "Profile_Group": selected_profile
        }
    )

    fig.update_traces(texttemplate="%{x:.1f}%")

    fig.update_layout(
        xaxis=dict(range=[0, 105], ticksuffix="%"),
        yaxis=dict(
            title=None,
            categoryorder="array",
            categoryarray=profile_summary["Profile_Group"].tolist()
        )
    )

    st.plotly_chart(fig, width="stretch")

    st.caption(
        "Hiring rate = hired / all candidates in each group, "
        "including active pipeline candidates. Hover over bars "
        "to view group sizes. Small groups and differences in "
        "application timing may affect comparisons."
    )

    with st.expander("View candidate profile figures"):
        st.dataframe(
            profile_summary.rename(columns={
                "Profile_Group": selected_profile,
                "Hiring_Rate_Percent": "Hiring rate (%)"
            }),
            hide_index=True,
            width="stretch"
        )

    # تم فصل رسوم التحليل عن ملخص الإدارة
    def decision_table(column):
        table = performance_table(column).copy()
        rejected_counts = (
            filtered[filtered["Status"].eq("Not Selected")]
            .groupby(column).size()
        )
        table["Not_Selected"] = (
            table[column].map(rejected_counts).fillna(0).astype(int)
        )
        return table

    region_decision = decision_table("Region_Group")

    role_decision = decision_table("Technical_Role")

    st.markdown("#### Regional performance")

    fig = px.bar(
        region_decision.sort_values("Hiring_Rate"),
        x="Hiring_Rate",
        y="Region_Group",
        orientation="h",
        title="Which regions have stronger hiring outcomes?",
        hover_data=["Candidates", "Hired", "Pipeline", "Not_Selected"],
        color_discrete_sequence=["#2563EB"]
    )

    fig.update_layout(
        xaxis_tickformat=".0%",
        xaxis_title="Hired / all candidates",
        yaxis_title=None
    )

    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        region_decision,
        hide_index=True,
        width="stretch",
        column_config={
            "Hiring_Rate": st.column_config.NumberColumn(
                "Hiring rate (0–1)", format="%.3f"
            )
        }
    )

    st.caption(
        "Rates include active candidates. Differences may reflect "
        "candidate profiles and application timing. "
        "No regional targets are available."
    )

    st.markdown("#### Role opportunities")

    role_outcomes = role_decision.melt(
        id_vars="Technical_Role",
        value_vars=["Hired", "Pipeline", "Not_Selected"],
        var_name="Outcome",
        value_name="Outcome_Count"
    )

    fig = px.bar(
        role_outcomes,
        x="Outcome_Count",
        y="Technical_Role",
        color="Outcome",
        orientation="h",
        barmode="stack",
        title="Hiring outcomes and active pipeline by role",
        color_discrete_map={
            "Hired": "#2563EB",
            "Pipeline": "#0D9488",
            "Not_Selected": "#CBD5E1"
        },
        labels={
            "Outcome_Count": "Candidates",
            "Technical_Role": "Technical role"
        }
    )

    st.plotly_chart(fig, width="stretch")

    role_rates = role_decision.copy()

    role_rates["Hiring_Rate_Percent"] = role_rates["Hiring_Rate"] * 100

    fig = px.bar(
        role_rates.sort_values("Hiring_Rate_Percent"),
        x="Hiring_Rate_Percent",
        y="Technical_Role",
        orientation="h",
        text="Hiring_Rate_Percent",
        title="Which roles have lower observed hiring rates?",
        hover_data={
            "Candidates": True,
            "Hired": True,
            "Pipeline": True,
            "Not_Selected": True,
            "Hiring_Rate_Percent": ":.1f"
        },
        color_discrete_sequence=["#2563EB"],
        labels={
            "Hiring_Rate_Percent": "Hiring rate (%)",
            "Technical_Role": "Technical role"
        }
    )

    fig.update_traces(texttemplate="%{x:.1f}%")

    fig.update_layout(
        xaxis=dict(range=[0, 105], ticksuffix="%"),
        yaxis_title=None
    )

    st.plotly_chart(fig, width="stretch")

    st.caption(
        "Hiring rate = hired / all candidates for each role, "
        "including active pipeline candidates. "
        "Compare group sizes and application timing before interpreting differences."
    )

    lowest_rate = role_decision["Hiring_Rate"].min()

    lowest_roles = role_decision[
        role_decision["Hiring_Rate"].eq(lowest_rate)
    ]

    lowest_names = ", ".join(
        lowest_roles["Technical_Role"].astype(str)
    )

    st.info(
        f"Lowest observed hiring rate: {lowest_names} "
        f"({lowest_rate:.1%}). Review unsuccessful outcomes and "
        "candidate maturity before deciding on an intervention."
    )

    largest_pipeline = int(role_decision["Pipeline"].max())

    if largest_pipeline > 0:
        pipeline_roles = role_decision[
            role_decision["Pipeline"].eq(largest_pipeline)
        ]

        pipeline_names = ", ".join(
            pipeline_roles["Technical_Role"].astype(str)
        )

        st.info(
            f"Largest active pipeline: {pipeline_names}, "
            f"with {largest_pipeline:,} active candidates per listed role. "
            "Review their current stages and agree next steps with hiring partners."
        )
    else:
        st.caption("No active pipeline candidates match this selection.")

    st.caption(
        "These comparisons identify performance differences and opportunities "
        "to progress active candidates. They do not establish unmet employer "
        "demand. Numerical vacancy shortfalls require role targets or vacancy counts."
    )

    st.markdown("#### Recruitment outcomes and candidate losses")

    outcomes = (
        filtered["Status"].value_counts()
        .rename_axis("Outcome")
        .reset_index(name="Candidates")
    )

    outcomes["Share"] = outcomes["Candidates"] / len(filtered)

    fig = px.bar(
        outcomes,
        x="Outcome",
        y="Candidates",
        text="Candidates",
        hover_data={"Share": ":.1%"},
        title="How many candidates are hired, active or not selected?"
    )

    st.plotly_chart(fig, width="stretch")

    not_selected = filtered[
        filtered["Status"].eq("Not Selected")
    ]

    losses = (
        not_selected["Current_Stage"].value_counts()
        .rename_axis("Recorded_Outcome")
        .reset_index(name="Candidates")
    )

    if not losses.empty:
        losses["Share_of_Not_Selected"] = (
            losses["Candidates"] / len(not_selected)
        )

        fig = px.bar(
            losses.sort_values("Candidates"),
            x="Candidates",
            y="Recorded_Outcome",
            orientation="h",
            text="Candidates",
            hover_data={"Share_of_Not_Selected": ":.1%"},
            title="Where are unsuccessful outcomes recorded?",
            color_discrete_sequence=["#D97706"]
        )
        fig.update_layout(yaxis_title=None)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No unsuccessful outcomes match the current filters.")

    st.caption(
        "Loss shares use all Not Selected candidates as the denominator. "
        "They are not failure rates among candidates who entered each stage. "
        "The dataset contains latest stages, not transition histories."
    )

    global_pipeline = int(df["Status"].eq("Pipeline").sum())

    additional_needed = max(remaining - global_pipeline, 0)

    st.info(
        f"Overall program gap: {remaining:,} hires. "
        f"Active pipeline: {global_pipeline:,} candidates. "
        f"Even if every active candidate were hired, "
        f"{additional_needed:,} further hires would still be needed. "
        "This is an upper-bound scenario, not a forecast."
    )

    st.markdown("#### Concentration & opportunities")

    if len(hired):
        # حصص المناطق
        region_contribution = region_decision.copy()

        region_contribution["Hire_Share_Percent"] = (
            region_contribution["Hired"] / len(hired) * 100
        )

        region_contribution["Hiring_Rate_Percent"] = (
            region_contribution["Hiring_Rate"] * 100
        )

        region_contribution = region_contribution.sort_values(
            "Hired", ascending=False
        )

        region_top3_share = (
            region_contribution.head(3)["Hired"].sum()
            / len(hired) * 100
        )

        st.markdown("**Regional contribution**")

        st.dataframe(
            region_contribution[
                [
                    "Region_Group",
                    "Candidates",
                    "Hired",
                    "Pipeline",
                    "Hire_Share_Percent",
                    "Hiring_Rate_Percent"
                ]
            ].rename(columns={
                "Region_Group": "Region group",
                "Hire_Share_Percent": "Share of selected hires (%)",
                "Hiring_Rate_Percent": "Hiring rate (%)"
            }),
            hide_index=True,
            width="stretch",
            column_config={
                "Share of selected hires (%)":
                    st.column_config.NumberColumn(format="%.1f"),
                "Hiring rate (%)":
                    st.column_config.NumberColumn(format="%.1f")
            }
        )

        st.write(
            f"The three region groups contributing the most hires "
            f"account for **{region_top3_share:.1f}%** of selected hires."
        )

        # حصص الشركات
        employer_contribution = employer.copy()

        employer_contribution["Hire_Share_Percent"] = (
            employer_contribution["Hired"] / len(hired) * 100
        )

        employer_contribution["Hiring_Rate_Percent"] = (
            employer_contribution["Hiring_Rate"] * 100
        )

        employer_contribution = employer_contribution.sort_values(
            "Hired", ascending=False
        )

        employer_top3_share = (
            employer_contribution.head(3)["Hired"].sum()
            / len(hired) * 100
        )

        st.markdown("**Employer contribution and active pipeline**")

        st.dataframe(
            employer_contribution[
                [
                    "Employer",
                    "Candidates",
                    "Hired",
                    "Pipeline",
                    "Hire_Share_Percent",
                    "Hiring_Rate_Percent"
                ]
            ].rename(columns={
                "Hire_Share_Percent": "Share of selected hires (%)",
                "Hiring_Rate_Percent": "Hiring rate (%)"
            }),
            hide_index=True,
            width="stretch",
            column_config={
                "Share of selected hires (%)":
                    st.column_config.NumberColumn(format="%.1f"),
                "Hiring rate (%)":
                    st.column_config.NumberColumn(format="%.1f")
            }
        )

        st.write(
            f"The three largest hiring employers account for "
            f"**{employer_top3_share:.1f}%** of selected hires. "
            "Confirm their next-phase commitments and review whether "
            "the program needs broader partnerships."
        )

        # فرصة متابعة فعلية: جهة لديها مرشحات نشطات
        active_employers = employer_contribution[
            employer_contribution["Pipeline"].gt(0)
        ].sort_values(
            ["Pipeline", "Hired"], ascending=False
        )

        if not active_employers.empty:
            partner = active_employers.iloc[0]

            st.info(
                f"Employer follow-up opportunity: {partner['Employer']} "
                f"has {int(partner['Pipeline']):,} active candidates. "
                "Confirm vacancies, review their stages and agree "
                "next steps. Active candidates are not guaranteed hires."
            )

        # مؤشر وصفي لدراسة توسيع الاستقطاب
        selected_overall_rate = len(hired) / len(filtered)
        median_region_size = region_contribution["Candidates"].median()

        regional_candidates = region_contribution[
            region_contribution["Hiring_Rate"].gt(selected_overall_rate)
            & region_contribution["Candidates"].lt(median_region_size)
            & region_contribution["Candidates"].ge(30)
        ].sort_values("Hiring_Rate", ascending=False)

        if not regional_candidates.empty:
            opportunity = regional_candidates.iloc[0]

            st.info(
                f"Regional opportunity to investigate: "
                f"{opportunity['Region_Group']} has an observed hiring rate "
                f"of {opportunity['Hiring_Rate']:.1%} across "
                f"{int(opportunity['Candidates']):,} candidates. "
                "Its candidate count is below the regional median, "
                "while its rate exceeds the selected overall rate. "
                "Assess employer demand and recruitment capacity "
                "before considering additional sourcing."
            )
        else:
            st.caption(
                "No region meets the illustrative opportunity screen "
                "under the current filters."
            )

        st.caption(
            "Opportunity screen: at least 30 candidates, hiring rate above "
            "the selected overall rate, and candidate count below the "
            "median across selected region groups. These are exploratory "
            "criteria, not evidence of unmet demand. Concentration shares "
            "describe the selection and do not alone prove excessive risk."
        )

    else:
        st.info(
            "No hires match this selection; hiring concentration "
            "and contribution shares cannot be calculated."
        )

with tab_actions:
    st.subheader("Insights / Management Actions")
    st.caption(
        "Program progress and capacity figures are global. "
        "Other findings reflect the current filters."
    )

    st.markdown("#### Key findings")

    st.write(
        f"1. Program achievement is {total_hired / TARGET:.1%}: "
        f"{total_hired:,} hires against {TARGET:,}, "
        f"leaving {remaining:,} hires."
    )

    if not region_decision.empty:
        ordered = region_decision.sort_values(
            ["Hiring_Rate", "Candidates"], ascending=False
        )
        highest = ordered.iloc[0]
        lowest = ordered.iloc[-1]

        st.write(
            f"2. Regional hiring rates range from "
            f"{lowest['Hiring_Rate']:.1%} in {lowest['Region_Group']} "
            f"({int(lowest['Candidates']):,} candidates) to "
            f"{highest['Hiring_Rate']:.1%} in {highest['Region_Group']} "
            f"({int(highest['Candidates']):,} candidates)."
        )

    if not losses.empty:
        largest_loss = losses.iloc[0]
        st.write(
            f"3. {largest_loss['Recorded_Outcome']} is the largest recorded "
            f"unsuccessful outcome: {int(largest_loss['Candidates']):,} "
            f"candidates, or "
            f"{largest_loss['Share_of_Not_Selected']:.1%} "
            "of selected Not Selected records."
        )
    else:
        st.write(
            "3. No Not Selected records appear in this selection; "
            "candidate-loss comparisons are unavailable."
        )

    if len(hired):
        share = employer.head(3)["Hired"].sum() / len(hired)
        partners = ", ".join(employer.head(3)["Employer"].astype(str))

        st.write(
            f"4. The top three employers ({partners}) account for "
            f"{share:.1%} of selected hires. Their future commitments "
            "are material to planning the next phase."
        )
    else:
        st.write(
            "4. No hires appear in this selection; "
            "employer concentration cannot be calculated."
        )

    st.write(
        f"5. The active pipeline cannot close the overall gap alone: "
        f"at least {additional_needed:,} additional hires are needed "
        "outside the current pipeline, even under 100% conversion."
    )

    if len(durations):
        st.write(
            f"6. Valid time-to-hire records cover "
            f"{len(durations) / len(hired):.1%} of selected hires. "
            f"Average duration is {durations.mean():.1f} days "
            f"versus a median of {durations.median():.1f} days. "
            "Review the duration distribution before assuming "
            "a single typical recruitment time."
        )
    else:
        st.write(
            "6. No valid time-to-hire records appear in this selection."
        )

    st.warning(
        "The monthly trend uses only records passing the date checks. Excluded date conflicts remain unresolved, so the trend is incomplete. "
        "It does not establish whether all 5,000 hires will be achieved "
        "by a deadline. Validate excluded dates and confirm the target "
        "completion date before producing a hiring forecast."
    )

    # ثلاث أولويات محددة
    st.markdown("#### Three management priorities")

    # الأولوية الأولى: القدرة المطلوبة
    eligible = source[source["Candidates"] >= 30]
    if eligible.empty:
        eligible = source

    best_source = eligible.sort_values(
        ["Hiring_Rate", "Candidates"], ascending=False
    ).iloc[0]

    st.write(
        f"1. Recruitment lead: secure additional employer vacancies and "
        f"candidate sourcing beyond the {global_pipeline:,} active candidates. "
        f"The minimum additional hiring requirement is {additional_needed:,}. "
        f"Pilot sourcing through {best_source['Hiring_Source']} "
        f"(observed hiring rate {best_source['Hiring_Rate']:.1%} "
        f"across {int(best_source['Candidates']):,} selected candidates), "
        "then compare cost and outcomes before scaling."
    )

    # الأولوية الثانية: الفقد
    if not losses.empty:
        outcome_name = str(largest_loss["Recorded_Outcome"])

        action_map = {
            "Assessment Failed":
                "review assessment criteria and pilot assessment preparation",
            "Interview Rejected":
                "calibrate interview scoring and pilot interview preparation",
            "Screening Rejected":
                "review eligibility communication and screening criteria",
            "Offer Declined":
                "collect decline reasons and review offer terms and response times"
        }

        action = action_map.get(
            outcome_name, "review reasons for this recorded outcome"
        )

        st.write(
            f"2. Recruitment operations lead: focus on {outcome_name}, "
            f"which accounts for "
            f"{largest_loss['Share_of_Not_Selected']:.1%} of unsuccessful "
            f"outcomes in this selection. {action.capitalize()}. "
            "Track subsequent outcomes using stage-entry counts."
        )
    else:
        st.write(
            "2. Recruitment operations lead: progress the active pipeline "
            "and collect stage-entry and exit timestamps to measure "
            "conversion and delays."
        )

    # الأولوية الثالثة: موثوقية التخطيط
    global_valid = int(
        df.loc[df["Status"].eq("Hired"), "Clean_Days_to_Hire"].notna().sum()
    )
    invalid_hired = total_hired - global_valid

    st.write(
        f"3. Data owner: validate dates for the {invalid_hired:,} hired "
        "records excluded from time analysis, document corrections, "
        "and collect stage timestamps. Recalculate the trend and "
        "time-to-hire metrics before setting a target completion forecast."
    )

with tab_data:
    with st.expander("Data quality and assumptions"):
        st.write(
            "The original records are retained. Hiring counts use Status. "
            "Clean_Days_to_Hire uses the difference between hire and application "
            "dates for records passing the preparation checks. "
            "Missing non-hired durations remain missing."
        )

        st.write(
            "Hiring rates include active pipeline candidates in the denominator. "
            "Different application dates and candidate profiles may affect comparisons."
        )

        st.write(
            "No regional or role-specific targets are supplied here, so counts "
            "cannot establish achievement against local targets. "
            "A hiring completion date is not forecast without reliable dated "
            "records and an agreed deadline."
        )

        flags = [
            "Hire_Before_Application",
            "Hired_Missing_Dates",
            "Date_After_Cutoff",
            "Duration_Mismatch"
        ]

        quality_rows = []

        for flag in flags:
            values = (
                filtered[flag].astype(str)
                .str.strip().str.lower()
                .isin(["true", "1", "1.0"])
            )

            quality_rows.append({
                "Quality check": flag,
                "Flagged records": int(values.sum())
            })

        st.dataframe(
            pd.DataFrame(quality_rows),
            hide_index=True,
            width="stretch"
        )

        st.caption("Quality flags may overlap within the same record.")

    with st.expander("View selected candidate data"):
        st.dataframe(filtered, hide_index=True, width="stretch")
