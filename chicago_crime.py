import pandas as pd
import folium
from folium import plugins
import streamlit as st
from streamlit_folium import folium_static
import altair as alt
from datetime import datetime
#from streamlit_folium import st_folium

st.set_page_config(layout='wide')

@st.cache_data
def write_intro():
    
    st.title("Chicago Crime Incident App")

    st.header("About the App")

    st.write("This app shows recently reported crime incidents in the City of Chicago.")

    st.header("Sourcing the Data")

    st.write("""
            The dataset **Crimes - 2001 to Present** from the Chicago
            Data Portal reflects reported crime incidents from in
            the City of Chicago from 2001 to Present.

            The data is extracted
            from the Chicago Police Department's CLEAR (Citizen Law
            Enforcement Analysis and Reporting) system.
            """
            )

write_intro()

## Date Prep and Cleaning
#API 2022 dataset:
@st.cache_data
def load_data(url):
    df = pd.read_json(url)
    return df

df = load_data("https://data.cityofchicago.org/resource/ijzp-q8t2.json")

@st.cache_data()
def clean_data(df):

    # Drop records with null values in the [Latitude] and [Longitude] columns
    df.dropna(axis=0, how='any', subset=['latitude','longitude'], inplace=True)

    # Identify Top 10 Crime Indicent Type
    top10_df = df.groupby(['primary_type']).count().sort_values(by=['id'], ascending=False).reset_index()

    # Create an empty list and store values
    top10_list = []

    for i in top10_df["primary_type"].head(10):
        top10_list.append(i)

    def new_df(df, val_list):
        new_df = pd.DataFrame()
        for i in val_list:
            new_df = pd.concat([new_df, df[(df['primary_type'] == i)]])
        return new_df

    # Create crime dataframe of top 10 crimes
    crime_df = new_df(df, top10_list)

    # Remake dataframe containing only necessary columns
    crime_df = crime_df[['date','primary_type','arrest','latitude','longitude']].copy()

    return crime_df

crime_df = clean_data(df)

# dict of crime_type and colors
crime_color = {'CRIMINAL TRESPASS':'red', 'KIDNAPPING':'blue', 'MOTOR VEHICLE THEFT':'green',
       'BATTERY':'purple', 'THEFT':'orange', 'BURGLARY':'darkred', 'OTHER OFFENSE':'lightred',
       'DECEPTIVE PRACTICE':'beige', 'CRIMINAL DAMAGE':'darkblue', 
       'ASSAULT':'darkgreen', 'ROBBERY':'cadetblue', 'NARCOTICS':'darkpurple', 'WEAPONS VIOLATION':'darkblue',
       'SEX OFFENSE':'pink', 'ARSON':'lightblue', 'CRIMINAL SEXUAL ASSAULT':'lightgreen',
       'OFFENSE INVOLVING CHILDREN':'gray', 'HOMICIDE':'black',
       'CONCEALED CARRY LICENSE VIOLATION':'lightgray','INTERFERENCE WITH PUBLIC OFFICER':'lightgray'}

@st.cache_data
def create_layers(color_dict):    
    ## Create a dictionary with mapped as keys (incident type) and values (color value for map)
    # empty list to populate layers with
    layers=[]

    # Create list of crimes to use in create_crime_cluster function
    for k in color_dict.keys():
        if k not in layers:
            layers.append(k)

    return layers

layers = create_layers(crime_color)

@st.cache_data
## Use list from previous function to create MarkerCluster layers
# Write a function that creates a list of marker clusters
def create_crime_cluster(layer):
    cluster_list = []
    for i in layer:
        cluster = plugins.MarkerCluster()
        cluster_list.append(cluster)
    return cluster_list

# Create a variable for the cluster_list generated from the create_crime_cluster function
cluster_list = create_crime_cluster(layers)

## Create the Map
# Chicago latitude and longitude values
lat = 41.85
long = -87.675

@st.cache_resource
def display_map(lat, long):
    # Create map object
    m = folium.Map(location=[lat, long], zoom_start=10, tiles='cartodbpositron')

    # Include additional basemap options
    carto = folium.TileLayer("cartodbpositron", show=True).add_to(m)
    openstreet = folium.TileLayer("openstreetmap", show=False).add_to(m)
    stamen = folium.TileLayer("stamentoner", show=False).add_to(m)
    #basemap_list = [carto]
    basemap_list = [carto, openstreet, stamen]

    # Instantiate a mark cluster for the incidents in the dataframe
    incidents = plugins.MarkerCluster(name="All Incidents").add_to(m)
    no_incidents = plugins.MarkerCluster(name="No Incidents").add_to(m)

    # Loop through the dataframe and add each data point to the mark cluster, color by crime incident type
    for lat, lng, label in zip(crime_df.latitude, crime_df.longitude, crime_df.primary_type):
        for k,v in crime_color.items():
            if label == k:
                if k not in layers:
                    layers.append(k)
                    folium.FeatureGroup(name=k).add_to(m)
                folium.Marker(
                    location=[lat,lng],
                    icon=folium.Icon(icon="info-sign",color=v),
                    popup=label,
                ).add_to(incidents)

    # Add layer select options
    all_incidents = []
    all_incidents.append(incidents)
    all_incidents.append(no_incidents)
    grouped_layer=[]
    grouped_layer.append(no_incidents)

    # Populate each marker cluster grouped by crime incident type
    x=0

    for i in layers:
        cluster_list[x] = plugins.MarkerCluster(name=i.title(), show=False).add_to(m)
        grouped_layer.append(cluster_list[x])
        for lat, lng, label in zip(crime_df.latitude, crime_df.longitude, crime_df.primary_type):
            if label == i:
                folium.Marker(location=[lat,lng], 
                              icon=folium.Icon(icon="info-sign",color=list(crime_color.values())[x]),
                              popup=label,
                             ).add_to(cluster_list[x])
        x = x+1

    plugins.GroupedLayerControl(
        groups={'<font size="4"><b>Basemap</b></font>': basemap_list,
                '<font size="4"><b>Incidents</b></font>': all_incidents,
                '<font size="4"><b>Crime Incident Type</b></font>': grouped_layer},
        exclusive_groups=True,
        collapsed=True,
    ).add_to(m)

    return m

chicago_map = display_map(lat, long)

@st.cache_data
def map_title():
    # Print map title
    st.write(
        """**Chicago Crime Incident Map**"""
        )

map_title()

# Display the map
st_data = folium_static(chicago_map, width=1200, height=600)

@st.cache_data
def write_disclaimer():
    st.write("""
            *Please see the
            [full dataset description](https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2)
            and legal disclaimer at the embedded link
            """
               )

    st.write("""

            The **visuals** in this application, processed and created by Mike Ivison, are for
            **_demonstrative purposes only_**.

            The intent of this application is to showcase
            my ability to develop an app from start-to-finish using entirely open-source
            tools. Any other use is without my (or the Chicago Police Department's) consent.
            """        
             )

write_disclaimer()

col1, col2 = st.columns(2)

with col1:
    tracked_val = st.selectbox("Before proceeding, select a crime to track:", crime_df['primary_type'].unique())

@st.cache_data
def write_process_title():
    st.header("Processing and Methodology")

write_process_title()

# Add a bar chart show crime count
alt_chart = (
    alt.Chart(crime_df, title="Most Recent Crime Count by Incident Type")
    .mark_bar()
    .encode(x=alt.Y('count(*):Q', title='Numer of Incidents'),
            y=alt.X('primary_type', title="Incident Type").sort('-x'),
            color=alt.condition(
                alt.datum.primary_type == tracked_val,
                alt.value('orange'),
                alt.value('steelblue'),
                )
            )
    .interactive().properties(width=900)
    )

st.altair_chart(alt_chart, use_container_width=False)

@st.cache_data
def write_process():
    st.write("1. Perform an API call to the dataset.")
    st.write(" * *Capture top 1000 rows of dataset*")
    st.write("2. Clean the Data:")
    st.write(" * *Using Python Pandas*")
    st.write("  * *Filter out null values for latitude and longitude*")

    st.caption("View the Dataframe:")
    
    st.dataframe(crime_df.sort_values(by='date', ascending=False), height=225)

    st.write("3. Analyze the Data:")
    st.write("  * *Use Altair for interactive charts*")
    st.write("  * *Use Python Folium for interactive maps*")
    st.write("4. Create a **Streamlit App** to Share the Data!")

    st.markdown("""
    <style>
    [data-testid="stMarkdownContainer"] ul{
        list-style-position: inside;
    }
    </style>
    """, unsafe_allow_html=True)

write_process()

st.header("""Analyzing the Data""")

# When do most crimes occur?

st.subheader("What Time of Day Do Most {} Incidents Take Place?".format(tracked_val.title()))

@st.cache_data
# Create a multi-series line chart from a new df with crimes grouped by hour
def create_date_df(df):
    df['hour'] = df['date'].dt.hour
    df = df.groupby(['primary_type','hour']).count().reset_index()

    return df

date_df = create_date_df(crime_df)

# Create data frame for total crime count
def crime_count_df(df):
    df['hour'] = df['date'].dt.hour
    df = df.groupby(['hour']).count().reset_index()
    df['primary_type'] = 'All Incidents'

    return df

crime_count_df = crime_count_df(crime_df)
#st.write(crime_count_df.head())

# Create data frame to count tracked_val
def tracked_val_df(df):
    df = df[df['primary_type'] == tracked_val].copy()
    df = df.groupby('hour').count().reset_index()
    df['primary_type'] = tracked_val.title() + " Incidents"

    return df

tracked_val_df = tracked_val_df(crime_df)

# Create a line chart to show all incident crime count
alt_chart_all = (
    alt.Chart(crime_count_df, title="Incident Occurences by Hour")
    .mark_line(point=True)
    .encode(x=alt.X('hour', title="Time of Day").scale(domain=(0,24)),
            y= alt.Y('date', title="# of Incidents"),
            color=alt.value('steelblue'),
            shape=alt.Shape('primary_type',
##                            legend={"title": '',
##                                    "type": "symbol",
##                                    "titleColor":"steelblue",
##                                    "labelColor":"orange",
##                                    "symbolOpacity":1,
##                                    "symbolFillColor":"orange",
##                                    "symbolStrokeWidth": 0,
##                                    "symbolSize": 100},
                            title=""),
            )
    .interactive().properties(width=900)
    )

# Create a line chart to show tracked value crime count
alt_chart_tracked = (
    alt.Chart(tracked_val_df, title="{} Occurences by Hour".format(tracked_val.title()))
    .mark_line(point=True)
    .encode(x=alt.X('hour').scale(domain=(0,24)),
            y= 'date',
            color=alt.value('orange'),
            shape = alt.Shape('primary_type',
                              title="")
            )
    .interactive().properties(width=900)
    )

# Add the two line charts together into one chart
st.altair_chart(alt_chart_all + alt_chart_tracked, use_container_width=False)

### What crimes result in arrests?

st.subheader("How Many {} Incidents Resulted in an Arrest?".format(tracked_val.title()))

# Add a bar chart show crime count
alt_chart = (
    alt.Chart(crime_df[(crime_df['arrest'] == True)], title="Number of Arrests by Incident Type")
    .mark_bar()
    .encode(x=alt.Y('primary_type', title="Incident Type", axis=alt.Axis(labelAngle=-45)).sort('-y'),
            y=alt.X('count(*):Q', title='Numer of Arrests'),
            color=alt.condition(
                alt.datum.primary_type == tracked_val,
                alt.value('orange'),
                alt.value('steelblue'),
                )
            )
    .interactive().properties(width=750)
    )

st.altair_chart(alt_chart, use_container_width=False)

st.subheader("Ratio of Arrest vs. Non-Arrest for {} Incidents".format(tracked_val.title()))

crime_sel_df = crime_df[crime_df.primary_type == tracked_val]

crime_sel_df['arrest'] = crime_sel_df['arrest'].astype(int)

incident_count = crime_sel_df['arrest'].value_counts().reset_index()
incident_count.loc[incident_count['arrest'] == 0, 'arrest'] = "No Arrest"
incident_count.loc[incident_count['arrest'] == 1, 'arrest'] = "Arrest"

#st.write(incident_count.head())

alt_chart = (alt.Chart(incident_count)
             .mark_bar(width=70)
             .encode(x=alt.Y('arrest', title="Incident Type: {}".format(tracked_val).title(), axis=alt.Axis(labelAngle=0)),
                     y=alt.X('count', title="Total Count"),
                     color=alt.condition(
                        alt.datum.arrest == "Arrest",
                        alt.value('orange'),
                        alt.value('steelblue'),
                        )
                     ).properties(width=400)
             )

incident_count['label'] = False # create new column
incident_count.loc[incident_count['arrest'] == 'arrest', 'label'] = True # choose value to label in the new column

text = alt.Chart(incident_count.query("arrest == 'Arrest'")).mark_text(
    baseline='bottom',
    color='white',
    dx=0,
    fontSize = 15,
    yOffset = -5,
    fontWeight='bold',
    ).encode(
        x=alt.Y('arrest'),
        y=alt.X('count'),
        text='label:N'
        ).transform_calculate(
            label=alt.datum.count + " arrests"
            )

st.altair_chart(alt_chart + text, use_container_width=False)    

# Show other stats
st.subheader("""Conclusions""")

# Create line graph showing reports by hour
st.write("What are some trends that you observed?")

st.write("For instance, while developing the app, I noticed:")

st.write(" * *Weapons Violations* tended to have a **low** number of incidents, but a **high** percentage of arrests per incident count.")
st.write(" * *Theft*, on the other hand, tended to have a **high** number of incidents, but a **low** percentange of arrests.")
st.write(" * Most crimes are reported to occur from hours 16-24 (4pm to Midnight).")

st.write("Can you identify any crimes that are reported to occur at other times of the day?")

st.write("The dataset is **updated daily** and shows the **most recent 1,000 crime incidents**, so it always shows the most recent snapshot of crime incident activity.")

st.write("Check in from time to time to observe any trends of time!")
         










