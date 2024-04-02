import streamlit as st
import pandas as pd
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium


st.set_page_config(layout="wide")
## INSPO: https://github.com/zakariachowdhury/streamlit-map-dashboard/blob/main/streamlit_app.py | https://zakariachowdhury-streamlit-map-dashboard-streamlit-app-jofuyj.streamlit.app/
df = pd.read_csv("CSV/demo_pjangroup.csv")
geofile = "EUNUTS_ZERO.geojson"

def year_selector(df):
    year = st.sidebar.select_slider("Slide to select a year", sorted(df['year'].unique()))
    return year
    # return st.sidebar.select_slider("Welches Jahr soll ausgewählt werden?", sorted(df['year'].unique()))


def display_country(df, nation):
     nations = sorted(df['geo'].unique())
     nation_index = nations.index(nation) if nation and nation in nations else 0
     return st.sidebar.selectbox('Choose a state', nations, nation_index)


def display_map(year):
    # ______________________________________________________MAP_____________________________________________
    map = folium.Map(location=(53, 9), zoom_start=4, scrollWheelZoom=False, tiles='CartoDB positron')

    choropleth = folium.Choropleth(
        geo_data=geofile,
        data=df[(df["age"] == "TOTAL") & (df["sex"] == "T") & (df["year"] == year)],
        columns=('country_code', 'population'),
        fill_color ='BuPu',
        key_on='feature.properties.NUTS_ID',
        fill_opacity=1,
        line_opacity=0.8,
        highlight=True,
    )
    choropleth.geojson.add_to(map)


    df_indexed = df[(df["age"] == "TOTAL") & (df["sex"] == "T") & (df["year"] == year)].reset_index(drop=True)
    df_indexed = df_indexed.set_index('country_code')
    for feature in choropleth.geojson.data['features']:
        nation = feature['properties']['NUTS_ID']
        feature['properties']['en_name'] = (df_indexed.loc[nation, 'geo']) if nation in list(df_indexed.index) else ''
        feature['properties']['population'] = 'Population: ' + '{:,}'.format(df_indexed.loc[nation, 'population']) if nation in list(df_indexed.index) else ''


    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['en_name', 'population'], labels=False)
    )
    st_map = st_folium(map, width="100%", height=600)


    nation = ''
    if st_map['last_active_drawing']:
        nation = st_map['last_active_drawing']['properties']['en_name']
    return nation






#-https://medium.com/@enigma.pythonml/how-to-create-sankey-diagrams-from-data-frames-in-python-plotly-and-kaggles-titanic-data-1f7d56b28096---------
def display_sankey(df, year, nation):
    filtered_df = df[df["year"] == year]
    filtered_df = filtered_df.query('geo == @nation & sex != "T" & age != "Y_GE80" & age != "Y_GE75"').reset_index(drop=True)

    # Population Group to Gender
    df1 = filtered_df[filtered_df["age"] != "TOTAL"]
    df1 = df1.groupby(['age', 'sex'])['population'].max().reset_index()
    df1.columns = ['source', 'target', 'value']
    df1['target'] =df1['target'].map({'F':'Female', 'M': 'Male'})

    # Gender to total population
    df2 = filtered_df.groupby(['sex', 'geo'])['population'].max().reset_index()
    df2 = df2[df2["sex"] != "T"]
    df2.columns = ['source', 'target', 'value']
    df2['source'] =df2['source'].map({'F':'Female', 'M': 'Male'})

    def all_links_func(df1, df2):
        all_links = pd.concat([df1,df2], axis=0)
        return all_links

    all_links = all_links_func(df1, df2)
    unique_source_target = list(pd.unique(all_links[['source', 'target']].values.ravel('K')))
    mapping_dict = {k: v for v, k in enumerate(unique_source_target)}
    all_links['source'] = all_links['source'].map(mapping_dict)
    all_links['target'] = all_links['target'].map(mapping_dict)
    links_dict = all_links.to_dict(orient='list')

    fig = go.Figure(data=[go.Sankey(node = dict(
        pad = 15,
        thickness = 20,
        line = dict(color = "black", width = 0.5),
        label = unique_source_target,
    ),
    link = dict(source = links_dict["source"],
                target = links_dict["target"],
                value = links_dict["value"],))])

    fig.update_layout(title_text="Population based on Age Group and Gender",font_size=10, height=600)

    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


def display_metric(df, year, nation):
    # Population
    pop1 = df.query('geo == @nation & sex == "T" & year == @year & age == "TOTAL"').reset_index(drop=True)
    pop2 = df.query('geo == @nation & sex == "T" & year == @year-1 & age == "TOTAL"').reset_index(drop=True)
    true_pop=str(f'{pop1["population"][0]:,}')
    # Population
    fem_pop1 = df.query('geo == @nation & sex == "F" & year == @year & age == "TOTAL"').reset_index(drop=True)
    fem_pop2 = df.query('geo == @nation & sex == "F" & year == @year-1 & age == "TOTAL"').reset_index(drop=True)

    # Male Population
    male_pop1 = df.query('geo == @nation & sex == "M" & year == @year & age == "TOTAL"').reset_index(drop=True)
    male_pop2 = df.query('geo == @nation & sex == "M" & year == @year-1 & age == "TOTAL"').reset_index(drop=True)

    col4, col5, col6= st.columns(3)
    if year == 2014:
        col4.metric("Total Population", to_million(pop1["population"]), help=true_pop)
        col5.metric("Female Population", to_million(fem_pop1["population"]))
        col6.metric("Male Population", to_million(male_pop1["population"])) 
    else:
        col4.metric("Total Population", to_million(pop1["population"]), to_million(pop1["population"] - pop2["population"]) + " (" + str(year-1) + ")", help=true_pop) 
        col5.metric("Female Population", to_million(fem_pop1["population"]), to_million(fem_pop1["population"] - fem_pop2["population"]) + " (" + str(year-1) + ")") 
        col6.metric("Male Population", to_million(male_pop1["population"]), to_million(male_pop1["population"] - male_pop2["population"]) + " (" + str(year-1) + ")")


#___________________FUNCTIONS__________________________

def to_million(column):
    vz = (column.astype(float)/1000000).round(2).astype(str)[0]+ ' M'
    return vz

def main():
    st.title("Europe Population Overview")
    year = year_selector(df)
    col1, col2 = st.columns(2)
    with col1:
        nation = display_map(year)
    nation = display_country(df, nation)
    with col2:
        display_sankey(df, year, nation)
    display_metric(df, year, nation)
    
    

if __name__ == "__main__":
    main()