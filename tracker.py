import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px
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
US_HIST_DATA_URL = (
"https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv"
)
STATE_HIST_DATA_URL = (
"https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"
)
COUNTIES_HIST_DATA_URL = (
"https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
)
COUNTY_LIST_URL = (
"https://raw.githubusercontent.com/nytimes/covid-19-data/master/live/us-counties.csv"
)

st.title("Live US Coronavirus Tracker")
st.markdown("This application is a Streamlit dashboard for tracking " +
    "COVID-19 cases live in the US.*")
st.markdown("_*Excludes US territories (American Samoa, Guam, Northern Mariana" +
" Islands, Puerto Rico, and Virgin Islands)._")
st.markdown("![Hits](http://tangykiwi.pythonanywhere.com/count/tag.svg?url=https%3A%2F%2Fus-covid-tracker.herokuapp.com)" +
    "  ![visitors](https://kiwi-view-counter.glitch.me/badge?page_id=TangyKiwi.us-covid-tracker)")

territories = ["District of Columbia", "Guam", "Northern Mariana Islands", "Puerto Rico", "Virgin Islands"]
@st.cache()
def load_state_data():
    data = pd.read_csv(STATE_DATA_URL)
    for i in territories:
        index = data[data['state'] == i].index
        data.drop(index, inplace=True)
    data.drop(['confirmed_cases', 'confirmed_deaths', 'probable_cases', 'probable_deaths'], axis=1, inplace=True)
    data.reset_index(drop=True, inplace=True)
    return data

state_data = load_state_data()
states = [('AA', 'Select'),
    ('AK', 'Alaska'), ('AL', 'Alabama'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
    ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'),
    ('DE', 'Delaware'), ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'),
    ('ID', 'Idaho'), ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'),
    ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'),
    ('MD', 'Maryland'), ('MA', 'Massachusetts'), ('MI', 'Michigan'),
    ('MN', 'Minnesota'), ('MS', 'Mississippi'), ('MO', 'Missouri'),
    ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'), ('NH', 'New Hampshire'),
    ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
    ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'),
    ('OK', 'Oklahoma'), ('OR', 'Oregon'), ('PA', 'Pennsylvania'),
    ('RI', 'Rhode Island'), ('SC', 'South Carolina'), ('SD', 'South Dakota'),
    ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'),
    ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
    ('WI', 'Wisconsin'), ('WY', 'Wyoming')
]

@st.cache()
def load_county_list():
    data = pd.read_csv(COUNTY_LIST_URL)
    data.drop(['date', 'cases', 'deaths', 'confirmed_cases', 'confirmed_deaths', 'probable_cases', 'probable_deaths'], axis=1, inplace=True)
    data.reset_index(drop=True, inplace=True)
    return data

county_list = load_county_list()

st.header("Map of Cases by State")
fig = go.Figure(data=go.Choropleth(
    locations=list(dict(states).keys())[1:],
    z=state_data['cases'].astype(int),
    locationmode='USA-states',
    colorscale='Reds',
    colorbar_title='# of Cases'
))
fig.update_layout(
    geo_scope='usa',
)
st.write(fig)
st.markdown('Updated: %s' % (state_data['date'][1]) + " ([NYT](https://github.com/nytimes/covid-19-data/blob/master/live/us-states.csv))")

if st.checkbox("Show Raw State Data", False):
    st.subheader('Raw Data')
    st.write(state_data)

st.header("Map of Cases by County")
@st.cache()
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
            data = pd.read_csv(url)
            today = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
        else:
            data = pd.read_csv("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/07-14-2020.csv")
            today = "2020-07-14"
    data.dropna(subset=['FIPS'], inplace=True)
    data.drop(['FIPS', 'Country_Region', 'Last_Update', 'Combined_Key', 'Active', 'Incidence_Rate', 'Case-Fatality_Ratio'], axis=1, inplace=True)
    data.rename(columns={'Admin2': 'county', 'Province_State': 'state', 'Lat': 'lat', 'Long_': 'long', 'Confirmed': 'cases', 'Deaths': 'deaths', 'Recovered': 'recovered'}, inplace=True)
    data.dropna(subset=['county', 'lat', 'long'], inplace=True, how="any")
    return data, today

county_data, date_used = load_county_data(datetime.now().strftime("%m-%d-%Y"))
plot_data = county_data[['county', 'state', 'lat', 'long']].copy()
plot_data['Cases'] = np.sqrt(county_data['cases'])
plot_data['Orig_cases'] = county_data['cases']
plot_data['Color'] = county_data['cases'].map(lambda x: [int(255*c) for c in plt.cm.Wistia(x/5000)])
midpoint = (np.average(county_data['lat']), np.average(county_data['long']))
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
        get_position=['long', 'lat'],
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
        "html": "<b>County: </b> {county} <br><b>State: </b> {state}<br><b>Cases: </b> {Orig_cases}",
    }
)
st.write(map)
st.markdown('Updated: %s' % date_used + " ([Johns Hopkins](https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_daily_reports))")

if st.checkbox("Show Raw County Data", False):
    st.subheader('Raw Data')
    st.write(county_data)

@st.cache()
def load_us_hist_data():
    return pd.read_csv(US_HIST_DATA_URL)

@st.cache()
def load_state_hist_data():
    data = pd.read_csv(STATE_HIST_DATA_URL)
    for i in territories:
        index = data[data['state'] == i].index
        data.drop(index, inplace=True)
    data.drop(['fips'], axis=1, inplace=True)
    data.reset_index(drop=True, inplace=True)
    return data

@st.cache()
def load_county_hist_data():
    data = pd.read_csv(COUNTIES_HIST_DATA_URL)
    return data

def draw_hist_graphs(data, title1, title2):
    fig = go.Figure(go.Scatter(x=data['date'], y=data['cases'], line=dict(color='red')))
    fig.update_layout(
        title=title1,
        xaxis_title="Date",
        yaxis_title="Cases"
    )
    fig.update_xaxes(rangeslider_visible=True)
    st.write(fig)
    fig2 = go.Figure(go.Scatter(x=data['date'], y=data['deaths'], line=dict(color='darkgray')))
    fig2.update_layout(
        title=title2,
        xaxis_title='Date',
        yaxis_title='Deaths'
    )
    fig2.update_xaxes(rangeslider_visible=True)
    st.write(fig2)

st.header("Historical Graph of Cases & Deaths")
area_select = st.selectbox('View', ['US', 'State', 'County'])
if area_select == 'US':
    us_hist_data = load_us_hist_data()
    draw_hist_graphs(us_hist_data, "US Cases", "US Deaths")
    if st.checkbox("Show Raw Historical US Data", False):
        st.subheader('Raw Data')
        st.write(us_hist_data)
elif area_select == 'State':
    state_select = st.selectbox('State', list(dict(states).values()))
    state_hist_data = load_state_hist_data()
    if state_select != 'Select':
        selected_data = state_hist_data[(state_hist_data['state'] == state_select)]
        selected_data.drop(['state'], axis=1, inplace=True)
        selected_data.reset_index(drop=True, inplace=True)
        draw_hist_graphs(selected_data, state_select + " Cases", state_select + " Deaths")
        if st.checkbox("Show Raw Historical State Data", False):
            st.subheader(state_select + ' Raw Data')
            st.write(selected_data)
elif area_select == 'County':
    county_hist_data = load_county_hist_data()
    state_select = st.selectbox('State', list(dict(states).values()))
    if state_select != 'Select':
        county_select_list = ["Select"]
        for i in range(len(county_list['state'])):
            if county_list['state'][i] == state_select:
                county_select_list.append(county_list['county'][i])
        county_select = st.selectbox('County', county_select_list)
        if county_select != 'Select':
            fips = -1
            for i in range(len(county_list['county'])):
                if county_list['county'][i] == county_select and county_list['state'][i] == state_select:
                    fips = county_list['fips'][i]
                    break
            if county_select == 'New York City':
                selected_data = county_hist_data[(county_hist_data['county'] == 'New York City')]
            else:
                selected_data = county_hist_data[(county_hist_data['fips'] == fips)]
            selected_data.drop(['county'], axis=1, inplace=True)
            selected_data.drop(['state'], axis=1, inplace=True)
            selected_data.drop(['fips'], axis=1, inplace=True)
            selected_data.reset_index(drop=True, inplace=True)
            draw_hist_graphs(selected_data, county_select + " Cases", county_select + " Deaths")
            if st.checkbox("Show Raw Historical County Data", False):
                st.subheader(county_select + ' Raw Data')
                st.write(selected_data)
