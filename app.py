import streamlit as st
import pandas as pd
import plotly.express as px

# ---  PAGE CONFIG ---
st.set_page_config(
    page_title="PH Maternal Health Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
        /* 1. Main Background - Dark */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* 2. Sidebar Background */
        section[data-testid="stSidebar"] {
            background-color: #262730;
        }
        
        /* 3. Metric Cards */
        div[data-testid="stMetric"] {
            background-color: #262730;
            border: 1px solid #41444e;
            border-left: 5px solid #FF4B4B; /* Red Accent */
            border-radius: 5px;
            padding: 15px;
        }
        
        /* 4. Text Coloring - Specific targets to avoid breaking Dropdowns */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
            color: #FAFAFA !important;
        }
        
        /* 5. FIX FOR DROPDOWNS & INPUTS */
        /* This targets the Input Box itself (Multiselect, Search) */
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            background-color: #1E1E1E !important;
            color: white !important;
            border-color: #41444e !important;
        }
        
        /* This targets the Dropdown Menu (The list that pops up) */
        div[data-baseweb="popover"], div[data-baseweb="menu"] {
            background-color: #262730 !important;
        }
        
        /* Text color inside the dropdown options */
        div[data-baseweb="select"] span, div[data-baseweb="menu"] li {
            color: white !important;
        }
        
        /* 6. Footer Styling */
        .footer {
            width: 100%;
            background-color: #0E1117;
            color: #bdc3c7;
            text-align: center;
            padding: 30px;
            margin-top: 50px;
            border-top: 1px solid #41444e;
            font-size: 14px;
        }
        .footer a {
            color: #FF4B4B;
            font-weight: bold;
            text-decoration: none;
        }
        
        /* 7. Remove White Background from Dataframes */
        .stDataFrame {
            background-color: #262730;
        }
    </style>
""", unsafe_allow_html=True)

# --- DATA PROCESSING ---
@st.cache_data
def load_data():
    # --- TABLE 19 (GEOGRAPHY) ---
    df_geo = pd.read_csv('table19.csv', header=2, usecols=range(11))
    df_geo.columns = ['Place', 'Total', 'Under 15', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+']
    df_geo = df_geo.dropna(subset=['Place'])
    
    # Island Groups
    def get_island_group(place):
        place = str(place).upper()
        if any(x in place for x in ['NCR', 'CAR', 'REGION I', 'REGION II', 'REGION III', 'REGION IV', 'MIMAROPA', 'REGION V']):
            return 'Luzon'
        elif any(x in place for x in ['REGION VI', 'REGION VII', 'REGION VIII']):
            return 'Visayas'
        elif any(x in place for x in ['REGION IX', 'REGION X', 'REGION XI', 'REGION XII', 'CARAGA', 'BARMM']):
            return 'Mindanao'
        return 'Other'

    df_geo['Island Group'] = df_geo['Place'].apply(get_island_group)
    df_geo['IsRegion'] = df_geo['Place'].apply(lambda x: "REGION" in str(x) or "NCR" in str(x) or "CAR" in str(x) or "BARMM" in str(x))

    # Melt
    df_geo_long = df_geo.melt(id_vars=['Place', 'IsRegion', 'Island Group'], 
                              value_vars=['Under 15', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+'],
                              var_name='Age Group', value_name='Deaths')
    df_geo_long['Deaths'] = pd.to_numeric(df_geo_long['Deaths'], errors='coerce').fillna(0)

    # --- TABLE 20 (CAUSES) ---
    df_cause = pd.read_csv('table20.csv', header=1, usecols=range(12))
    df_cause.columns = ['ICD Code', 'Cause', 'Total', 'Under 15', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+']
    df_cause = df_cause.dropna(subset=['ICD Code'])
    df_cause = df_cause[df_cause['ICD Code'] != 'ICD-10 Code'] 
    
    # Melt
    df_cause_long = df_cause.melt(id_vars=['ICD Code', 'Cause'], 
                                  value_vars=['Under 15', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+'],
                                  var_name='Age Group', value_name='Deaths')
    df_cause_long['Deaths'] = pd.to_numeric(df_cause_long['Deaths'], errors='coerce').fillna(0)
    
    return df_geo_long, df_cause_long

try:
    df_geo, df_cause = load_data()
except Exception as e:
    st.error(f"❌ Data Error: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("📊 Filter Data")
    
    # Filter 1: Age
    selected_age = st.multiselect(
        "Filter by Age Group:", 
        options=df_cause['Age Group'].unique(), 
        default=['20-24', '25-29', '30-34', '35-39']
    )
    
    st.markdown("---")
    
    # Filter 2: Island Group
    island_options = ['Luzon', 'Visayas', 'Mindanao']
    selected_island = st.multiselect("Region / Island Group:", island_options, default=island_options)
    
    st.markdown("---")
    
    # Filter 3: Search
    search_cause = st.text_input("Search Complication", placeholder="e.g. Hypertension")

# FILTER LOGIC
if selected_age:
    filtered_cause = df_cause[df_cause['Age Group'].isin(selected_age)]
    filtered_geo = df_geo[df_geo['Age Group'].isin(selected_age)]
else:
    filtered_cause = df_cause
    filtered_geo = df_geo

if selected_island:
    filtered_geo = filtered_geo[filtered_geo['Island Group'].isin(selected_island)]

if search_cause:
    filtered_cause = filtered_cause[filtered_cause['Cause'].str.contains(search_cause, case=False, na=False)]

# --- DASHBOARD UI ---

st.title("Philippines Maternal Health Dashboard (2021)")
st.markdown("### *Analysis of Maternal Mortality Risks*")
st.markdown("---")

# METRICS ROW
total_deaths = int(filtered_cause['Deaths'].sum())
geo_deaths = int(filtered_geo[filtered_geo['IsRegion']]['Deaths'].sum())

if not filtered_cause.empty:
    top_cause_row = filtered_cause.groupby('Cause')['Deaths'].sum().reset_index().sort_values('Deaths', ascending=False).iloc[0]
    top_cause_name = top_cause_row['Cause']
else:
    top_cause_name = "None"

c1, c2, c3 = st.columns(3)
c1.metric("Total Deaths (Selection)", f"{total_deaths:,}")
c2.metric("Deaths in Selected Islands", f"{geo_deaths:,}")
c3.metric("Leading Complication", top_cause_name)

st.markdown("<br>", unsafe_allow_html=True) # Spacing

# CHARTS ROW 1
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🩺 Top 10 Complications")
    if not filtered_cause.empty:
        cause_summary = filtered_cause.groupby('Cause')['Deaths'].sum().reset_index().sort_values('Deaths', ascending=False).head(10)
        
        # BAR CHART
        fig_bar = px.bar(cause_summary, x='Deaths', y='Cause', orientation='h', 
                         text='Deaths', 
                         color='Deaths', 
                         color_continuous_scale='Reds',
                         template="plotly_dark")
        
        fig_bar.update_layout(
            yaxis={'categoryorder':'total ascending', 'title': None},
            xaxis={'title': 'Number of Deaths'},
            margin=dict(l=0, r=0, t=10, b=0),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data found for current filters.")

with col_right:
    st.subheader("👥 Age Group Share")
    if not filtered_cause.empty:
        age_summary = filtered_cause.groupby('Age Group')['Deaths'].sum().reset_index()
        
        # PIE CHART
        fig_pie = px.pie(age_summary, values='Deaths', names='Age Group', hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Pastel,
                         template="plotly_dark")
        
        fig_pie.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            margin=dict(l=0, r=0, t=0, b=0),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# ROW 2 - MAP
st.subheader("📍 Regional Analysis")
regions_only = filtered_geo[filtered_geo['IsRegion'] == True]

if not regions_only.empty:
    geo_summary = regions_only.groupby('Place')['Deaths'].sum().reset_index().sort_values('Deaths', ascending=False)
    
    # MAP CHART
    fig_map = px.bar(geo_summary, x='Place', y='Deaths', 
                     color='Deaths', 
                     color_continuous_scale='Teal',
                     labels={'Place': 'Region'},
                     template="plotly_dark")
    
    fig_map.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=0, r=0, t=10, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No regions match your filter.")

# --- FOOTER ---
st.markdown(""" 
<div class="footer">
    <p><b>Maternal Mortality Risk Profiler: Analyzing common complications leading to maternal deaths in rural areas.</p>
    <p>Submitted by: <b>John Cedrick B. Dela Corta</b> | Professor: <b>Sir Val Fabregas</b></p>
    <p>
        Data Source: 
        <a href="https://psa.gov.ph/statistics/vital-statistics/report" target="_blank">
            Philippine Statistics Authority (PSA) Vital Statistics Report 2021
        </a>
    </p>
</div>
""", unsafe_allow_html=True)