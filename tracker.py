import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

US_DATA_URL = (
"https://raw.githubusercontent.com/nytimes/covid-19-data/master/live/us.csv"
)
STATE_DATA_URL = (
"https://raw.githubusercontent.com/nytimes/covid-19-data/master/live/us-states.csv"
)
COUNTIES_DATA_URL = (
"https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/date.csv"
)

st.title("Live US Coronavirus Tracker")
st.markdown("This application is a Streamlit dashboard for tracking " +
    "COVID-19 cases live in the US.")
st.markdown("_Excludes US territories (American Samoa, Guam, Northern Mariana" +
" Islands, Puerto Rico, and Virgin Islands)._")

def load_state_data():
    data = pd.read_csv(STATE_DATA_URL)
    territories = ["District of Columbia", "Guam", "Northern Mariana Islands", "Puerto Rico", "Virgin Islands"]
    for i in territories:
        index = data[data['state'] == i].index
        data.drop(index, inplace=True)
    data.reset_index(drop=True, inplace=True)
    return data

state_data = load_state_data()
states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI',
    'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS',
    'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR',
    'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI',
    'WY']

st.header("Map of Cases by State")
fig = go.Figure(data=go.Choropleth(
    locations=states,
    z = state_data['cases'].astype(int),
    locationmode = 'USA-states',
    colorscale = 'Reds',
    colorbar_title = '# of Cases'
))
fig.update_layout(
    geo_scope='usa',
)
st.write(fig)
st.write('Updated: %s' % (state_data['date'][1]))

if st.checkbox("Show Raw State Data", False):
    st.subheader('Raw Data')
    st.write(state_data)

st.header("Map of Cases by County")
def load_county_data(today):
    url = COUNTIES_DATA_URL.replace("date", today)
    r = requests.get(url)
    if r.ok:
        data = pd.read_csv(url)
        today = datetime.now().strftime("%Y-%m-%d")
    else:
        today = (datetime.now() - timedelta(1)).strftime("%m-%d-%Y")
        url = COUNTIES_DATA_URL.replace("date", today)
        r = requests.get(url)
        if r.ok:
            data=pd.read_csv(url)
            today = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
        else:
            data = pd.read_csv("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/05-15-2020.csv")
            today = "2020-05-15"
    data.dropna(subset=['FIPS'], inplace=True)
    data.drop(['FIPS', 'Country_Region', 'Last_Update', 'Combined_Key', 'Active'], axis=1, inplace=True)
    data.rename(columns={'Admin2': 'County', 'Province_State': 'State', 'Confirmed': 'Cases', 'Long_': 'Long'}, inplace=True)
    data.dropna(subset=['County', 'Lat', 'Long'], inplace=True, how="any")
    return data, today

county_data, date_used = load_county_data(datetime.now().strftime("%m-%d-%Y"))
plot_data = county_data[['County', 'State', 'Lat', 'Long']].copy()
plot_data['Cases'] = np.sqrt(county_data['Cases'])
plot_data['Orig_cases'] = county_data['Cases']
plot_data['Color'] = county_data['Cases'].map(lambda x: [int(255*c) for c in plt.cm.Wistia(x/5000)])
midpoint = (np.average(county_data['Lat']), np.average(county_data['Long']))
map = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": 40,
        "longitude": -107,
        "zoom": 2,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
        'GridCellLayer',
        plot_data,
        get_position=['Long', 'Lat'],
        get_elevation='Cases',
        get_color='Color',
        auto_highlight=True,
        elevationScale=6000,
        pickable=True,
        extruded=True,
        material=True,
        cellSize=50000,
        coverage=.5,
        ),
    ],
    tooltip={
        "html": "<b>County: </b> {County} <br><b>State: </b> {State}<br><b>Cases: </b> {Orig_cases}",
    }
)
st.write(map)
st.write('Updated: %s' % date_used)

if st.checkbox("Show Raw County Data", False):
    st.subheader('Raw Data')
    st.write(county_data)
