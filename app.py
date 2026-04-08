import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="PH Maternal Health Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ADAPTIVE CSS STYLING ---
st.markdown("""
    <style>
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-left: 5px solid #FF4B4B;
            border-radius: 5px;
            padding: 15px;
            min-height: 120px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .footer {
            width: 100%;
            color: gray;
            text-align: center;
            padding: 30px;
            margin-top: 50px;
            border-top: 1px solid rgba(128, 128, 128, 0.2);
            font-size: 14px;
        }
        .footer a { color: #FF4B4B; font-weight: bold; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

# --- DATA PROCESSING ---
@st.cache_data
def load_data():
    # Check if files exist to prevent crash on deployment
    if not os.path.exists('table19.csv') or not os.path.exists('table20.csv'):
        return None, None

    # --- TABLE 19 (GEOGRAPHY) ---
    df_geo = pd.read_csv('table19.csv', header=2, usecols=range(11))
    df_geo.columns = ['Place', 'Total', 'Under 15', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+']
    df_geo = df_geo.dropna(subset=['Place'])
    
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
    df_geo['IsRegion'] = df_geo['Place'].apply(lambda x: any(kw in str(x).upper() for kw in ["REGION", "NCR", "CAR", "BARMM"]))

    df_geo_long = df_geo.melt(id_vars=['Place', 'IsRegion', 'Island Group'], 
                              value_vars=['Under 15', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+'],
                              var_name='Age Group', value_name='Deaths')
    df_geo_long['Deaths'] = pd.to_numeric(df_geo_long['Deaths'], errors='coerce').fillna(0)

    # --- TABLE 20 (CAUSES) ---
    df_cause = pd.read_csv('table20.csv', header=1, usecols=range(12))
    df_cause.columns = ['ICD Code', 'Cause', 'Total', 'Under 15', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+']
    df_cause = df_cause.dropna(subset=['ICD Code'])
    df_cause = df_cause[df_cause['ICD Code'] != 'ICD-10 Code'] 
    
    df_cause_long = df_cause.melt(id_vars=['ICD Code', 'Cause'], 
                                  value_vars=['Under 15', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+'],
                                  var_name='Age Group', value_name='Deaths')
    df_cause_long['Deaths'] = pd.to_numeric(df_cause_long['Deaths'], errors='coerce').fillna(0)
    
    return df_geo_long, df_cause_long

# Initialize data
df_geo, df_cause = load_data()

if df_geo is None or df_cause is None:
    st.error("❌ Data files (table19.csv or table20.csv) not found in the repository!")
    st.info("Please ensure your CSV files are uploaded to the same folder as app.py")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("📊 Filter Data")
    
    # FIX: Ensure Cause column is treated as string and filter out empty values
    all_causes = df_cause['Cause'].dropna().unique()
    unique_causes = sorted([str(c) for c in all_causes])
    
    selected_complications = st.multiselect(
        "Select Specific Complication(s):", 
        options=unique_causes,
        placeholder="Type to search..."
    )

    selected_age = st.multiselect(
        "Filter by Age Group:", 
        options=df_cause['Age Group'].unique(), 
        default=['20-24', '25-29', '30-34', '35-39']
    )
    
    st.markdown("---")
    island_options = ['Luzon', 'Visayas', 'Mindanao']
    selected_island = st.multiselect("Region / Island Group:", island_options, default=island_options)

# --- FILTER LOGIC ---
filtered_cause = df_cause.copy()
filtered_geo = df_geo.copy()

if selected_age:
    filtered_cause = filtered_cause[filtered_cause['Age Group'].isin(selected_age)]
    filtered_geo = filtered_geo[filtered_geo['Age Group'].isin(selected_age)]

if selected_island:
    filtered_geo = filtered_geo[filtered_geo['Island Group'].isin(selected_island)]

if selected_complications:
    filtered_cause = filtered_cause[filtered_cause['Cause'].isin(selected_complications)]

# --- DASHBOARD UI ---
st.title("Philippines Maternal Health Dashboard (2021)")
st.markdown("### *Analysis of Maternal Mortality Risks*")
st.markdown("---")

# METRICS Calculation
total_deaths = int(filtered_cause['Deaths'].sum())
geo_deaths = int(filtered_geo[filtered_geo['IsRegion']]['Deaths'].sum())

if not filtered_cause.empty and total_deaths > 0:
    top_cause_row = filtered_cause.groupby('Cause')['Deaths'].sum().reset_index().sort_values('Deaths', ascending=False).iloc[0]
    full_cause_name = top_cause_row['Cause']
    display_name = (full_cause_name[:22] + "...") if len(full_cause_name) > 22 else full_cause_name
else:
    full_cause_name = "N/A"
    display_name = "N/A"

c1, c2, c3 = st.columns(3)
c1.metric("Total Deaths (Selection)", f"{total_deaths:,}")
c2.metric("Deaths in Selected Islands", f"{geo_deaths:,}")
c3.metric("Leading Complication", display_name, help=f"Full Name: {full_cause_name}") 

# --- VISUALIZATIONS ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🩺 Top 10 Complications")
    if total_deaths > 0:
        cause_summary = filtered_cause.groupby('Cause')['Deaths'].sum().reset_index().sort_values('Deaths', ascending=False).head(10)
        fig_bar = px.bar(cause_summary, x='Deaths', y='Cause', orientation='h', color='Deaths', color_continuous_scale='Reds')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending', 'title': None}, height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data for current filters.")

with col_right:
    st.subheader("👥 Age Group Share")
    if total_deaths > 0:
        age_summary = filtered_cause.groupby('Age Group')['Deaths'].sum().reset_index()
        fig_pie = px.pie(age_summary, values='Deaths', names='Age Group', hole=0.5)
        fig_pie.update_layout(height=400, showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("📍 Regional Analysis")
regions_only = filtered_geo[filtered_geo['IsRegion'] == True]
if not regions_only.empty:
    geo_summary = regions_only.groupby('Place')['Deaths'].sum().reset_index().sort_values('Deaths', ascending=False)
    fig_map = px.bar(geo_summary, x='Place', y='Deaths', color='Deaths', color_continuous_scale='Teal')
    st.plotly_chart(fig_map, use_container_width=True)

# --- FOOTER ---
st.markdown(f""" 
<div class="footer">
    <p><b>Maternal Mortality Risk Profiler</b></p>
    <p>Submitted by: <b>John Cedrick B. Dela Corta</b> | Instructor: <b>Engr. Val Patrick Fabregas, MTA</b></p>
    <p>Data Source: <a href="https://psa.gov.ph/statistics/vital-statistics/report" target="_blank">PSA Vital Statistics Report 2021</a></p>
</div>
""", unsafe_allow_html=True)