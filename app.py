import zlib
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

# ==========================================
# PAGE CONFIGURATION & CUSTOM STYLING
# ==========================================
st.set_page_config(
    page_title="HotelPulse AI | Accor Paris Multi-Property Engine",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.8rem; padding-bottom: 2.5rem; }

    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card-alert {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-left: 6px solid #e11d48;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(225, 29, 72, 0.06);
        height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-title { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: #64748b; }
    .kpi-value { font-size: 1.7rem; font-weight: 700; color: #0f172a; line-height: 1.2; }
    .kpi-subtext-positive { font-size: 0.8rem; font-weight: 600; color: #16a34a; }
    .kpi-subtext-neutral { font-size: 0.8rem; font-weight: 500; color: #475569; }
    .kpi-alert-value { font-size: 1.0rem; font-weight: 700; color: #be123c; line-height: 1.3; }
    .kpi-alert-subtext { font-size: 0.78rem; font-weight: 500; color: #9f1239; }

    .action-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 3px 8px rgba(15, 23, 42, 0.04);
    }
    .action-high { border-left: 7px solid #ef4444; }
    .action-medium { border-left: 7px solid #f59e0b; }
    .action-low { border-left: 7px solid #10b981; }
    .action-addressed { border-left: 7px solid #64748b; background-color: #f8fafc; opacity: 0.88; }

    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .badge-high { background-color: #fee2e2; color: #b91c1c; }
    .badge-medium { background-color: #fef3c7; color: #b45309; }
    .badge-low { background-color: #d1fae5; color: #047857; }
    .badge-dept { background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .badge-status-open { background-color: #f1f5f9; color: #475569; }
    .badge-status-assigned { background-color: #e0e7ff; color: #4338ca; }
    .badge-status-done { background-color: #dcfce7; color: #15803d; }

    .action-headline { font-size: 1.05rem; font-weight: 600; color: #0f172a; margin: 8px 0 4px 0; }
    .action-meta { font-size: 0.83rem; color: #64748b; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 15 ACCOR PARIS HOTELS MASTER METADATA
# ==========================================
HOTELS_METADATA = pd.DataFrame([
    {"name": "Le Royal Monceau - Raffles Paris", "brand": "Raffles", "group": "Accor Luxury", "stars": 5, "lat": 48.8763, "lon": 2.3004, "color": [147, 51, 234]},
    {"name": "Sofitel Paris Le Faubourg", "brand": "Sofitel", "group": "Accor Luxury", "stars": 5, "lat": 48.8687, "lon": 2.3218, "color": [147, 51, 234]},
    {"name": "Sofitel Paris Baltimore Tour Eiffel", "brand": "Sofitel", "group": "Accor Luxury", "stars": 5, "lat": 48.8654, "lon": 2.2902, "color": [147, 51, 234]},
    {"name": "Pullman Paris Tour Eiffel", "brand": "Pullman", "group": "Accor Premium", "stars": 4, "lat": 48.8554, "lon": 2.2929, "color": [37, 99, 235]},
    {"name": "Pullman Paris Montparnasse", "brand": "Pullman", "group": "Accor Premium", "stars": 4, "lat": 48.8396, "lon": 2.3228, "color": [37, 99, 235]},
    {"name": "Pullman Paris Bercy", "brand": "Pullman", "group": "Accor Premium", "stars": 4, "lat": 48.8315, "lon": 2.3862, "color": [37, 99, 235]},
    {"name": "Hôtel Novotel Paris les Halles", "brand": "Novotel", "group": "Accor Midscale", "stars": 4, "lat": 48.8606, "lon": 2.3461, "color": [16, 185, 129]},
    {"name": "Novotel Paris Centre Tour Eiffel", "brand": "Novotel", "group": "Accor Midscale", "stars": 4, "lat": 48.8507, "lon": 2.2825, "color": [16, 185, 129]},
    {"name": "Novotel Paris Vaugirard Montparnasse", "brand": "Novotel", "group": "Accor Midscale", "stars": 4, "lat": 48.8385, "lon": 2.3045, "color": [16, 185, 129]},
    {"name": "Hôtel Mercure Paris Centre Tour Eiffel", "brand": "Mercure", "group": "Accor Midscale", "stars": 4, "lat": 48.8542, "lon": 2.2941, "color": [245, 158, 11]},
    {"name": "Mercure Paris Opéra Garnier", "brand": "Mercure", "group": "Accor Midscale", "stars": 4, "lat": 48.8751, "lon": 2.3262, "color": [245, 158, 11]},
    {"name": "Mercure Paris Montmartre Sacré-Cœur", "brand": "Mercure", "group": "Accor Midscale", "stars": 4, "lat": 48.8858, "lon": 2.3312, "color": [245, 158, 11]},
    {"name": "Hôtel ibis Paris Tour Eiffel Cambronne", "brand": "ibis", "group": "Accor Economy", "stars": 3, "lat": 48.8465, "lon": 2.3032, "color": [239, 68, 68]},
    {"name": "ibis Paris Bastille Opéra", "brand": "ibis", "group": "Accor Economy", "stars": 3, "lat": 48.8553, "lon": 2.3689, "color": [239, 68, 68]},
    {"name": "ibis Styles Paris République", "brand": "ibis Styles", "group": "Accor Economy", "stars": 3, "lat": 48.8672, "lon": 2.3644, "color": [239, 68, 68]},
])

# Map dot colors per segment (same palette as the dashboard badges)
GROUP_COLORS = {
    "Accor Luxury": "#9333ea",
    "Accor Premium": "#2563eb",
    "Accor Midscale": "#10b981",
    "Accor Economy": "#ef4444",
}

# Initialize Session State
if "selected_hotel" not in st.session_state:
    st.session_state.selected_hotel = "Pullman Paris Tour Eiffel"

if "action_states" not in st.session_state:
    st.session_state.action_states = {
        hotel: {
            "card_1": {"status": "Open", "assigned_to": None},
            "card_2": {"status": "Open", "assigned_to": None},
            "card_3": {"status": "Open", "assigned_to": None},
        }
        for hotel in HOTELS_METADATA["name"]
    }


# ==========================================
# SYNTHETIC DATA GENERATOR
# ==========================================
@st.cache_data
def generate_synthetic_review_dataset(hotel_name: str):
    # crc32 is stable across runs (Python's hash() is randomized per process), so the data is reproducible
    np.random.seed(zlib.crc32(hotel_name.encode("utf-8")))
    today = datetime(2026, 10, 27)

    platforms = ["Google Reviews", "TripAdvisor", "Booking.com"]
    languages = ["English 🇬🇧", "French 🇫🇷", "German 🇩🇪", "Spanish 🇪🇸"]
    dept_aspects = {
        "Front Desk": ["Check-in Speed", "Staff Politeness", "Arrival Flow"],
        "Housekeeping": ["Room Cleanliness", "Bedding Comfort", "Bathroom Space"],
        "Maintenance": ["Wi-Fi Speed", "Air Conditioning", "Elevator Delay"],
        "F&B": ["Breakfast Variety", "Coffee Quality", "Room Service Speed"],
    }

    records = []
    for _ in range(120):
        review_date = (today - timedelta(days=int(np.random.randint(0, 300)))).date()
        dept = np.random.choice(list(dept_aspects.keys()))
        aspect = np.random.choice(dept_aspects[dept])
        platform = np.random.choice(platforms)
        lang = np.random.choice(languages, p=[0.4, 0.3, 0.15, 0.15])

        rating_val = np.random.choice([5, 4, 3, 2, 1], p=[0.50, 0.25, 0.15, 0.07, 0.03])
        sentiment = "Positive" if rating_val >= 4 else ("Neutral" if rating_val == 3 else "Negative")

        records.append({
            "Date": review_date,
            "Rating": rating_val,
            "Platform": platform,
            "Language": lang,
            "Department": dept,
            "Aspect": aspect,
            "Sentiment": sentiment,
            "Original Text": f"Sample feedback regarding {aspect.lower()} at {hotel_name}.",
        })

    return pd.DataFrame(records)


def get_hotel_actions(hotel_name: str, filtered_df: pd.DataFrame):
    lang_counts = filtered_df["Language"].value_counts().to_dict()
    en_cnt = lang_counts.get("English 🇬🇧", 8)
    fr_cnt = lang_counts.get("French 🇫🇷", 6)
    de_cnt = lang_counts.get("German 🇩🇪", 4)
    es_cnt = lang_counts.get("Spanish 🇪🇸", 3)

    if "Raffles" in hotel_name or "Sofitel" in hotel_name:
        return [
            {
                "id": "card_1",
                "priority": "High Priority",
                "priority_level": "high",
                "department": "Front Desk",
                "dept_head": "Alexandre de Saint-Germain (Chef Concierge)",
                "recommendation": "Add secondary valet team during peak checkout (10 AM - 12 PM) to avoid car dispatch delays.",
                "impact": "Estimated +0.25 overall lift | Root Aspect: Valet & Luggage Service",
                "languages_affected": f"English ({en_cnt}), French ({fr_cnt})",
            },
            {
                "id": "card_2",
                "priority": "Medium Priority",
                "priority_level": "medium",
                "department": "F&B",
                "dept_head": "Chef Jérôme Charles (Culinary Director)",
                "recommendation": "Extend late-night gourmet room service menu options until 2:00 AM.",
                "impact": "Estimated +0.14 overall lift | Root Aspect: Night Dining Variety",
                "languages_affected": f"English ({en_cnt-2}), Spanish ({es_cnt})",
            },
            {
                "id": "card_3",
                "priority": "Low Priority",
                "priority_level": "low",
                "department": "Housekeeping",
                "dept_head": "Marie-Thérèse Blanc (Executive Housekeeper)",
                "recommendation": "Introduce customizable organic room scent profiles upon guest check-in.",
                "impact": "Estimated +0.05 overall lift | Root Aspect: Sensory Room Comfort",
                "languages_affected": f"French ({fr_cnt}), German ({de_cnt})",
            },
        ]
    elif "Pullman" in hotel_name:
        return [
            {
                "id": "card_1",
                "priority": "High Priority",
                "priority_level": "high",
                "department": "Maintenance",
                "dept_head": "Marc Dubois (Chief Engineer)",
                "recommendation": "Reprogram elevator dispatch algorithms during morning breakfast peak hours (8:30 AM - 10 AM).",
                "impact": "Estimated +0.30 overall lift | Root Aspect: Elevator Wait Time",
                "languages_affected": f"English ({en_cnt}), French ({fr_cnt}), German ({de_cnt})",
            },
            {
                "id": "card_2",
                "priority": "Medium Priority",
                "priority_level": "medium",
                "department": "Front Desk",
                "dept_head": "Claire Moreau (Front Office Manager)",
                "recommendation": "Open dedicated ALL Accor Loyalty desk during convention check-in rushes.",
                "impact": "Estimated +0.18 overall lift | Root Aspect: Check-in Speed",
                "languages_affected": f"English ({en_cnt-1}), Spanish ({es_cnt})",
            },
            {
                "id": "card_3",
                "priority": "Low Priority",
                "priority_level": "low",
                "department": "F&B",
                "dept_head": "Antoine Mercier (F&B Lead)",
                "recommendation": "Restock plant-based milk and gluten-free items more frequently on the main buffet.",
                "impact": "Estimated +0.08 overall lift | Root Aspect: Breakfast Variety",
                "languages_affected": f"French ({fr_cnt}), German ({de_cnt})",
            },
        ]
    elif "Novotel" in hotel_name or "Mercure" in hotel_name:
        return [
            {
                "id": "card_1",
                "priority": "High Priority",
                "priority_level": "high",
                "department": "Front Desk",
                "dept_head": "Sophie Laurent (Guest Relations Manager)",
                "recommendation": "Increase front desk staffing between 2:30 PM and 5:00 PM to handle peak train/metro arrivals.",
                "impact": "Estimated +0.28 overall lift | Root Aspect: Arrival Queue Speed",
                "languages_affected": f"English ({en_cnt}), French ({fr_cnt}), German ({de_cnt})",
            },
            {
                "id": "card_2",
                "priority": "Medium Priority",
                "priority_level": "medium",
                "department": "Maintenance",
                "dept_head": "Gérard Lefebvre (Facilities Lead)",
                "recommendation": "Service HVAC cooling valves and recalibrate room thermostats on floors 3 & 4.",
                "impact": "Estimated +0.20 overall lift | Root Aspect: Air Conditioning",
                "languages_affected": f"German ({de_cnt}), French ({fr_cnt})",
            },
            {
                "id": "card_3",
                "priority": "Low Priority",
                "priority_level": "low",
                "department": "F&B",
                "dept_head": "David Perrin (Restaurant Lead)",
                "recommendation": "Install secondary self-serve coffee station to reduce morning queue times.",
                "impact": "Estimated +0.09 overall lift | Root Aspect: Coffee Quality & Speed",
                "languages_affected": f"English ({en_cnt-3}), Spanish ({es_cnt})",
            },
        ]
    else:
        return [
            {
                "id": "card_1",
                "priority": "High Priority",
                "priority_level": "high",
                "department": "Housekeeping",
                "dept_head": "Nathalie Caron (Head Housekeeper)",
                "recommendation": "Inspect and replace faulty shower gel dispensers across all odd-numbered rooms.",
                "impact": "Estimated +0.22 overall lift | Root Aspect: Bathroom Fixtures",
                "languages_affected": f"French ({fr_cnt}), English ({en_cnt}), German ({de_cnt})",
            },
            {
                "id": "card_2",
                "priority": "Medium Priority",
                "priority_level": "medium",
                "department": "Maintenance",
                "dept_head": "Luc Rossi (Building Maintenance)",
                "recommendation": "Adjust hydraulic hallway door closers to prevent night slamming noise.",
                "impact": "Estimated +0.16 overall lift | Root Aspect: Hallway Noise Isolation",
                "languages_affected": f"German ({de_cnt}), French ({fr_cnt})",
            },
            {
                "id": "card_3",
                "priority": "Low Priority",
                "priority_level": "low",
                "department": "F&B",
                "dept_head": "Karim Haddad (Bar & Snack Lead)",
                "recommendation": "Add USB charging ports near the 24/7 lobby lounge seating area.",
                "impact": "Estimated +0.06 overall lift | Root Aspect: Lounge Comfort",
                "languages_affected": f"English ({en_cnt-2}), Spanish ({es_cnt})",
            },
        ]


# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.markdown("## 🏨 HotelPulse AI")
    st.caption("Accor Paris Multi-Property Dashboard")
    st.markdown("---")

    st.markdown("### 🔍 Property Filters")

    selected_stars = st.multiselect(
        "🌟 Filter by Star Rating",
        options=[3, 4, 5],
        default=[3, 4, 5],
        format_func=lambda x: f"{x} Stars",
    )

    available_brands = HOTELS_METADATA["brand"].unique().tolist()
    selected_brands = st.multiselect(
        "🏷️ Filter by Brand Family",
        options=available_brands,
        default=available_brands,
    )

    filtered_hotels_df = HOTELS_METADATA[
        (HOTELS_METADATA["stars"].isin(selected_stars)) &
        (HOTELS_METADATA["brand"].isin(selected_brands))
    ]

    if filtered_hotels_df.empty:
        st.error("No properties match your star/brand filters.")
        st.stop()

    hotel_names_list = filtered_hotels_df["name"].tolist()

    # A map click stores the hotel in "pending_hotel"; it is applied here, before the
    # selectbox is drawn, because Streamlit forbids changing a widget's value after it is rendered.
    if "pending_hotel" in st.session_state:
        st.session_state.selected_hotel = st.session_state.pop("pending_hotel")
    if st.session_state.selected_hotel not in hotel_names_list:
        st.session_state.selected_hotel = hotel_names_list[0]

    # The selectbox and the map share the same session key, so they always stay in sync
    st.selectbox(
        "📍 Select Property Details",
        options=hotel_names_list,
        key="selected_hotel",
    )

    st.markdown("---")

    selected_date_range = st.selectbox(
        "📅 Date Range Window",
        options=["Last 30 Days", "Q3 2026", "Full Year 2026", "Custom Range"],
        index=0,
    )

    today = datetime(2026, 10, 27).date()
    if selected_date_range == "Last 30 Days":
        start_date = today - timedelta(days=30)
        end_date = today
    elif selected_date_range == "Q3 2026":
        start_date = datetime(2026, 7, 1).date()
        end_date = datetime(2026, 9, 30).date()
    elif selected_date_range == "Full Year 2026":
        start_date = datetime(2026, 1, 1).date()
        end_date = today
    else:
        col_d1, col_d2 = st.columns(2)
        with col_d1: start_date = st.date_input("Start", today - timedelta(days=60))
        with col_d2: end_date = st.date_input("End", today)

    st.markdown("---")
    plat_google = st.checkbox("Google Reviews", value=True)
    plat_tripadvisor = st.checkbox("TripAdvisor", value=True)
    plat_booking = st.checkbox("Booking.com", value=True)

    selected_platforms = []
    if plat_google: selected_platforms.append("Google Reviews")
    if plat_tripadvisor: selected_platforms.append("TripAdvisor")
    if plat_booking: selected_platforms.append("Booking.com")


# ==========================================
# DATA PROCESSING & COMPUTATION
# ==========================================
selected_hotel = st.session_state.selected_hotel
raw_df = generate_synthetic_review_dataset(selected_hotel)
filtered_df = raw_df[
    (raw_df["Date"] >= start_date) &
    (raw_df["Date"] <= end_date) &
    (raw_df["Platform"].isin(selected_platforms))
]

total_reviews_count = len(filtered_df)
avg_score = filtered_df["Rating"].mean() if total_reviews_count > 0 else 0.0
negative_alerts_count = len(filtered_df[filtered_df["Sentiment"] == "Negative"])

actions = get_hotel_actions(selected_hotel, filtered_df)


# ==========================================
# MAIN SIDE-BY-SIDE LAYOUT (CONTENT LEFT | MAP RIGHT)
# ==========================================
st.title("HotelPulse AI: Accor Guest Sentiment & Action Engine")
st.markdown(
    f"*Selected Property:* {selected_hotel} &nbsp;|&nbsp; "
    f"*Window:* {start_date} to {end_date} &nbsp;|&nbsp; "
    f"*Sources:* {', '.join(selected_platforms)}"
)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

col_left, col_right = st.columns([1.15, 0.85])

# ------------------------------------------
# LEFT COLUMN: KPI CARDS & REVIEW DASHBOARD
# ------------------------------------------
with col_left:
    # Top KPI Cards
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    with kpi_col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Satisfaction Score</div>
                <div class="kpi-value">⭐ {avg_score:.2f} / 5.0</div>
                <div class="kpi-subtext-positive">▲ {total_reviews_count} reviews</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Review Volume</div>
                <div class="kpi-value">{total_reviews_count} Reviews</div>
                <div class="kpi-subtext-neutral">🌍 4 languages</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col3:
        st.markdown(
            f"""
            <div class="kpi-card-alert">
                <div class="kpi-title" style="color: #9f1239;">Urgent Alerts</div>
                <div class="kpi-alert-value">⚠️ {negative_alerts_count} Negative Mentions</div>
                <div class="kpi-alert-subtext">Requires lead action</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # Dashboard Tabs in Left Column
    tab1, tab2, tab3 = st.tabs(
        [
            "🔥 Action Matrix",
            "🏢 Department Ratings",
            "🌍 Live Feed",
        ]
    )

    with tab1:
        st.subheader(f"Weekly Priority Actions — {selected_hotel}")
        hotel_states = st.session_state.action_states[selected_hotel]
        completed_count = sum(1 for v in hotel_states.values() if v["status"] == "Addressed")
        st.progress(
            completed_count / len(actions),
            text=f"Progress: {completed_count} of {len(actions)} actions addressed",
        )

        for idx, item in enumerate(actions):
            card_id = item["id"]
            current_state = hotel_states[card_id]["status"]
            assigned_person = hotel_states[card_id]["assigned_to"]

            border_class = "action-addressed" if current_state == "Addressed" else f"action-{item['priority_level']}"
            priority_badge_class = f"badge-{item['priority_level']}"

            if current_state == "Addressed":
                status_badge = '<span class="badge badge-status-done">✓ Addressed</span>'
            elif assigned_person:
                status_badge = f'<span class="badge badge-status-assigned">👤 Assigned: {assigned_person}</span>'
            else:
                status_badge = '<span class="badge badge-status-open">● Pending</span>'

            st.markdown(
                f"""
                <div class="action-card {border_class}">
                    <div>
                        <span class="badge {priority_badge_class}">{item["priority"]}</span>
                        <span class="badge badge-dept">🏢 {item["department"]}</span>
                        {status_badge}
                    </div>
                    <div class="action-headline">Action {idx + 1}: "{item["recommendation"]}"</div>
                    <div class="action-meta">
                        <strong>📊 Impact:</strong> {item["impact"]} &nbsp;|&nbsp;
                        <strong>🗣️ Languages:</strong> {item["languages_affected"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_col1, btn_col2, _ = st.columns([1.5, 2.0, 3])
            with btn_col1:
                is_done = current_state == "Addressed"
                if st.button(
                    "✓ Addressed" if not is_done else "↺ Reopen",
                    key=f"btn_done_{selected_hotel}_{card_id}",
                    type="primary" if not is_done else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.action_states[selected_hotel][card_id]["status"] = "Open" if is_done else "Addressed"
                    st.rerun()

            with btn_col2:
                if st.button(
                    f"📋 Assign Lead",
                    key=f"btn_assign_{selected_hotel}_{card_id}",
                    use_container_width=True,
                    disabled=(current_state == "Addressed"),
                ):
                    st.session_state.action_states[selected_hotel][card_id]["assigned_to"] = item["dept_head"]
                    st.toast(f"Assigned to {item['dept_head']}!", icon="📨")
                    st.rerun()

            st.markdown("<hr style='margin: 8px 0 14px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)

    with tab2:
        st.subheader("Departmental Deep-Dive & Aspect Scores")
        if total_reviews_count > 0:
            dept_sentiment = filtered_df.groupby(["Department", "Sentiment"]).size().unstack(fill_value=0)
            for col in ["Positive", "Neutral", "Negative"]:
                if col not in dept_sentiment.columns: dept_sentiment[col] = 0

            dept_pct = (dept_sentiment.div(dept_sentiment.sum(axis=1), axis=0) * 100).reset_index().melt(
                id_vars="Department", value_name="Percentage", var_name="Sentiment"
            )

            fig_dept = px.bar(
                dept_pct, x="Percentage", y="Department", color="Sentiment", orientation="h",
                title="Sentiment Share by Department (%)",
                color_discrete_map={"Positive": "#10b981", "Neutral": "#94a3b8", "Negative": "#ef4444"},
            )
            fig_dept.update_layout(barmode="stack", height=280, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_dept, use_container_width=True)

            aspect_df = filtered_df.groupby("Aspect")["Rating"].agg(["mean", "count"]).reset_index()
            aspect_df.columns = ["Aspect", "Score", "Count"]
            aspect_df = aspect_df.sort_values(by="Score", ascending=True)

            aspect_df["Tier"] = aspect_df["Score"].apply(
                lambda v: "Healthy (≥ 4.0)" if v >= 4.0 else ("At Risk (3.5 - 3.9)" if v >= 3.5 else "Critical (< 3.5)")
            )

            fig_aspects = px.bar(
                aspect_df, x="Score", y="Aspect", orientation="h", text=aspect_df["Score"].round(2),
                color="Tier",
                color_discrete_map={"Healthy (≥ 4.0)": "#10b981", "At Risk (3.5 - 3.9)": "#f59e0b", "Critical (< 3.5)": "#ef4444"},
                title="Computed Aspect Ratings (1-5 Scale)",
            )
            fig_aspects.add_vline(x=4.0, line_dash="dash", line_color="#ef4444", annotation_text="Benchmark (4.0)")
            fig_aspects.update_layout(xaxis=dict(range=[0, 5.5]), height=300, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_aspects, use_container_width=True)

    with tab3:
        st.subheader("Filtered Live Review Feed")
        if total_reviews_count > 0:
            for _, r in filtered_df.head(6).iterrows():
                sentiment_color = "#10b981" if r["Sentiment"] == "Positive" else ("#f59e0b" if r["Sentiment"] == "Neutral" else "#ef4444")
                st.markdown(
                    f"""
                    <div style="background-color: #ffffff; border-radius: 8px; padding: 12px 14px; border: 1px solid #e2e8f0; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 0.85rem;"><strong>{r['Platform']}</strong> | {r['Language']} | <span style="color: #64748b;">{r['Date']}</span></span>
                            <span style="background-color: {sentiment_color}22; color: {sentiment_color}; font-weight: 700; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem;">
                                ⭐ {r['Rating']}/5
                            </span>
                        </div>
                        <div style="font-size: 0.88rem; color: #1e293b; margin-bottom: 4px;"><em>"{r['Original Text']}"</em></div>
                        <div><span class="badge badge-dept">🏢 {r['Department']}</span> <span style="font-size: 0.75rem; color: #475569;">🏷️ {r['Aspect']}</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ------------------------------------------
# RIGHT COLUMN: MAP PIN CLICK LOADS HOTEL REVIEWS PAGE
# ------------------------------------------
with col_right:
    st.subheader("🗺️ Interactive Map Switcher")
    st.caption("Click any hotel pin on the map to switch directly to its review page.")

    selected_row = filtered_hotels_df[filtered_hotels_df["name"] == selected_hotel].iloc[0]

    # Light CARTO basemap: white, minimal, matches the page (no API key needed)
    hotel_map = folium.Map(
        location=[float(selected_row["lat"]), float(selected_row["lon"])],
        zoom_start=13,
        tiles="CartoDB positron",
    )
    # Keep the required map credits, but as a small transparent line instead of a white bar
    hotel_map.get_root().header.add_child(folium.Element(
        "<style>.leaflet-control-attribution{font-size:9px!important;background:rgba(255,255,255,0.55)!important;"
        "color:#94a3b8!important;padding:0 4px!important;}"
        ".leaflet-control-attribution a{color:#94a3b8!important;}</style>"
    ))
    for _, h in filtered_hotels_df.iterrows():
        is_selected = h["name"] == selected_hotel
        folium.CircleMarker(
            location=[float(h["lat"]), float(h["lon"])],
            radius=11 if is_selected else 7,
            color="#0f172a" if is_selected else "#ffffff",
            weight=3 if is_selected else 2,
            fill=True,
            fill_color=GROUP_COLORS.get(h["group"], "#64748b"),
            fill_opacity=0.95,
            tooltip=f"{h['name']} — {h['brand']} | {h['stars']}★",
        ).add_to(hotel_map)

    map_event = st_folium(
        hotel_map,
        height=420,
        use_container_width=True,
        returned_objects=["last_object_clicked"],
        key="hotel_map",
    )
    st.markdown(
        "<div style='font-size:0.78rem; color:#64748b; margin-top:-6px;'>"
        + " &nbsp; ".join(
            f"<span style='color:{c};'>●</span> {g.replace('Accor ', '')}" for g, c in GROUP_COLORS.items()
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    # The last click stays in the map's state across reruns, so only react to a NEW click;
    # otherwise an old click would override a hotel picked later in the sidebar.
    clicked = (map_event or {}).get("last_object_clicked")
    if clicked:
        click_pos = (round(clicked["lat"], 5), round(clicked["lng"], 5))
        if click_pos != st.session_state.get("last_map_click"):
            st.session_state.last_map_click = click_pos
            distances = (filtered_hotels_df["lat"] - clicked["lat"]) ** 2 + (filtered_hotels_df["lon"] - clicked["lng"]) ** 2
            clicked_hotel = filtered_hotels_df.loc[distances.idxmin(), "name"]
            if clicked_hotel != selected_hotel:
                st.session_state.pending_hotel = clicked_hotel
                st.rerun()

    # Active Hotel Details Card (under the map)
    if total_reviews_count > 0:
        positive_share = (filtered_df["Sentiment"] == "Positive").mean() * 100
        aspect_scores = filtered_df.groupby("Aspect")["Rating"].mean()
        weakest_aspect = f"{aspect_scores.idxmin()} ({aspect_scores.min():.2f}/5)"
        top_language = filtered_df["Language"].value_counts().idxmax()
    else:
        positive_share = 0.0
        weakest_aspect = top_language = "—"

    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(selected_row['name'] + ' Paris')}"

    with st.container(border=True):
        st.markdown(f"#### 🏨 {selected_row['name']}")
        st.caption(f"{selected_row['brand']} · {selected_row['group']} · {'★' * int(selected_row['stars'])}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Score", f"{avg_score:.2f}/5")
        m2.metric("Reviews", total_reviews_count)
        m3.metric("Positive", f"{positive_share:.0f}%")
        st.markdown(
            f"**⚠️ Weakest aspect:** {weakest_aspect}  \n"
            f"**🚨 Negative mentions:** {negative_alerts_count}  \n"
            f"**🗣️ Main review language:** {top_language}"
        )
        st.link_button("📍 Open in Google Maps", google_maps_url, use_container_width=True)
