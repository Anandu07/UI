import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import requests
import json
from shapely.geometry import Point
import plotly.express as px
import pandas as pd

st.set_page_config(layout="wide")


@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/spain-provinces.geojson"
    response = requests.get(url)
    gdf = gpd.GeoDataFrame.from_features(json.loads(response.text)["features"])
    gdf.set_crs("EPSG:4326", inplace=True)
    return gdf

gdf = load_data()


if 'selected_district' not in st.session_state:
    st.session_state.selected_district = gdf['name'].iloc[0]
if 'click_position' not in st.session_state:
    st.session_state.click_position = None
if 'previous_selected_district' not in st.session_state:
    st.session_state.previous_selected_district = st.session_state.selected_district

# Function to create a base map centered and zoomed into the selected district
def create_map(gdf, selected_district_name):
    selected_district = gdf[gdf['name'] == selected_district_name]
    bounds = selected_district.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]  # Calculate center of selected district
    map = folium.Map(location=center, zoom_start=6)  # Adjusted zoom level for closer focus

    # Add districts to the map with style configurations
    folium.GeoJson(
        gdf,
        name="Districts",
        style_function=lambda x: {
            'fillColor': 'blue' if x['properties']['name'] != selected_district_name else 'red',
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.6 if x['properties']['name'] != selected_district_name else 0.9
        },
        tooltip=folium.GeoJsonTooltip(fields=['name'], labels=True, sticky=False),
        highlight_function=lambda x: {'weight': 3, 'color': 'yellow'}
    ).add_to(map)


    folium.LatLngPopup().add_to(map)
    
    return map


map = create_map(gdf, st.session_state.selected_district)
output = st_folium(map, width=1500, height=500)  


if output and output.get("last_clicked"):
    st.session_state.click_position = (output["last_clicked"]["lat"], output["last_clicked"]["lng"])


if st.session_state.click_position is not None:
    clicked_point = gpd.GeoDataFrame(
        [1], geometry=[Point(st.session_state.click_position[1], st.session_state.click_position[0])],
        crs="EPSG:4326"
    )
    clicked_district = gpd.sjoin(clicked_point, gdf, how="left", op="within")

    if not clicked_district.empty:
        new_selected_district = clicked_district.iloc[0]['name']
        if new_selected_district != st.session_state.selected_district:
            st.session_state.selected_district = new_selected_district
            st.experimental_rerun() 

st.session_state.previous_selected_district = st.session_state.selected_district

mobility_data = pd.read_csv("data/mobility_data_province.csv")
color_map = {
    'frequent': '#636EFA',
    'not_frequent': '#EF553B',
    'house': '#00CC96',
    'work/study': '#AB63FA',
    '<10': '#FFA15A',
    '10-15': '#19D3F3',
    '>15': '#FF6692',
    '25-45': '#B6E880',
    '45-65': '#FF97FF',
    '65-100': '#FECB52',
    'man': '#0079BF',
    'woman': '#FFB6C1'
}
selected_province = st.session_state.selected_district

st.markdown(f'The selected Province is <span style="color:red;">{st.session_state.selected_district}</span>', unsafe_allow_html=True)
province_data = mobility_data[mobility_data['province'] == selected_province]

print(province_data)

col1, col2, col3 = st.columns(3)

with col1:
    fig_no_of_trips = px.histogram(province_data, x='no_of_trips', title=f'No of Trips Distribution in {selected_province}',
                               color_discrete_sequence=[color_map['frequent']])
    st.plotly_chart(fig_no_of_trips)

with col2:
    fig_trip_kms = px.box(province_data, y='trip_kms', title=f'Trip Kms Distribution in {selected_province}',
                      color_discrete_sequence=[color_map['frequent']])
    st.plotly_chart(fig_trip_kms)

with col3:
    fig_frequency = px.bar(province_data, x='frequency', title=f'Frequency Distribution in {selected_province}',color_discrete_sequence=[color_map['frequent']])
    st.plotly_chart(fig_frequency)

col4, col5 , col6= st.columns(3)

with col4:
    # Bar plot for categorical variables
    fig_destination_place = px.bar(province_data, x='destination_place', title=f'Destination Place Distribution in {selected_province}',
                               color='destination_place', color_discrete_map=color_map)
    st.plotly_chart(fig_destination_place)
    
with col5:
    fig_age_bin = px.bar(province_data, x='age_bin', title=f'Age Bin Distribution in {selected_province}',
                     color='age_bin', color_discrete_map=color_map)
    st.plotly_chart(fig_age_bin)


with col6:
    fig_sex = px.bar(province_data, x='sex', title=f'Sex Distribution in {selected_province}',
                 color='sex', color_discrete_map=color_map)
    st.plotly_chart(fig_sex)

col7, col8 , col9= st.columns(3)

with col7:
    agg_data = province_data.groupby(['age_bin', 'sex']).agg({'trip_kms': 'mean'}).reset_index()
    fig_agg_sex_trip_kms = px.bar(agg_data, x='age_bin', y='trip_kms', color='sex', barmode='group', color_discrete_map=color_map,
                 title=f'Average Trip Kms by Age Group and Gender in {selected_province}')
    st.plotly_chart(fig_agg_sex_trip_kms)

with col8:
    agg_data_no_trips = province_data.groupby(['age_bin', 'sex']).agg({'no_of_trips': 'mean'}).reset_index()
    fig_agg_sex_trip_no = px.bar(agg_data_no_trips, x='age_bin', y='no_of_trips', color='sex', barmode='group', color_discrete_map=color_map,
                 title=f'Average number of Trips by Age Group and Gender in {selected_province}')
    st.plotly_chart(fig_agg_sex_trip_no)


with col9:
    agg_data_revenue_age = province_data.groupby(['age_bin', 'revenue']).agg({'no_of_trips': 'mean'}).reset_index()
    fig_agg_sex_trip_no = px.bar(agg_data_revenue_age, x='revenue', y='no_of_trips', color='age_bin', barmode='group', color_discrete_map=color_map,
                 title=f'Average number of Trips by Age Group and their Revenue in {selected_province}')
    st.plotly_chart(fig_agg_sex_trip_no)



col10, col11 , col12= st.columns(3)

with col10:
    agg_data_ = province_data.groupby(['age_bin', 'revenue']).agg({'trip_kms': 'mean'}).reset_index()
    fig_agg_sex_trip_kms = px.bar(agg_data_, x='revenue', y='trip_kms', color='age_bin', barmode='group', color_discrete_map=color_map,
                 title=f'Average Trip Kms by Age Group and their Revenue in {selected_province}')
    st.plotly_chart(fig_agg_sex_trip_kms)

with col11:
    agg_data_no_trips = province_data.groupby(['sex','revenue']).agg({'no_of_trips': 'mean'}).reset_index()
    fig_agg_sex_trip_no = px.bar(agg_data_no_trips, x='sex', y='no_of_trips', color='sex', barmode='group', color_discrete_map=color_map,
                 title=f'Average number of Trips by Age Group and Gender in {selected_province}')
    st.plotly_chart(fig_agg_sex_trip_no)


with col12:
    agg_data_revenue_age = province_data.groupby(['age_bin', 'revenue']).agg({'no_of_trips': 'mean'}).reset_index()
    fig_agg_sex_trip_no = px.bar(agg_data_revenue_age, x='age_bin', y='no_of_trips', color='revenue', barmode='group', color_discrete_map=color_map,
                 title=f'Average number of Trips by Age Group and their Revenue in {selected_province}')
    st.plotly_chart(fig_agg_sex_trip_no)





