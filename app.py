import streamlit as st
import pandas as pd
import folium
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium

## INSPO: https://github.com/zakariachowdhury/streamlit-map-dashboard/blob/main/streamlit_app.py | https://zakariachowdhury-streamlit-map-dashboard-streamlit-app-jofuyj.streamlit.app/
# df = pd.read_csv("CSV/NEWNUTS1POP.csv")
df = pd.read_csv("CSV/demo_pjangroup.csv")
geofile = "EUNUTS_ZERO.geojson"

# state_list = list(df['geo'].unique())
# state_list.sort()
# state_index = state_list.index(land) if land and land in state_list else 0
# st.write(state_list)

with st.sidebar:
    selected_year = st.selectbox("Welches Jahr soll ausgewählt werden?",
                sorted(df['year'].unique()))

    # land = st.selectbox("Welches Land soll ausgewählt werden?",
    #                       sorted(df['geo'].unique()))

# st.title("Statistical Atlas for: " + land)

def display_country(df, land):
     state_list = sorted(df['geo'].unique())
     state_index = state_list.index(land) if land and land in state_list else 0
     return st.sidebar.selectbox('Welches Land soll ausgewählt werden?', state_list, state_index)


#___________________FUNCTIONS__________________________

def to_million(column):
    vz = (column.astype(float)/1000000).round(2).astype(str)[0]+ ' M'
    return vz

st.header('Map of Country', divider='violet')

def display_map():
    # ______________________________________________________MAP_____________________________________________
    map = folium.Map(location=(51, 7), zoom_start=4, scrollWheelZoom=False, tiles='CartoDB positron')

    choropleth = folium.Choropleth(
        geo_data=geofile,
        data=df[df["year"] == selected_year],
        columns=('country_code', 'population'),
        key_on='feature.properties.NUTS_ID',
        line_opacity=0.8,
        highlight=True
    )
    choropleth.geojson.add_to(map)

    df_indexed = df[(df["age"] == "TOTAL") & (df["sex"] == "T") & (df["year"] == selected_year)].reset_index(drop=True)
    df_indexed = df_indexed.set_index('country_code')
    for feature in choropleth.geojson.data['features']:
        land = feature['properties']['NUTS_ID']
        feature['properties']['en_name'] = (df_indexed.loc[land, 'geo']) if land in list(df_indexed.index) else ''
        feature['properties']['population'] = 'Population: ' + '{:,}'.format(df_indexed.loc[land, 'population']) if land in list(df_indexed.index) else ''


    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['en_name', 'population'], labels=False)
    )
    st_map = st_folium(map, width=700, height=450)


    land = ''
    if st_map['last_active_drawing']:
        land = st_map['last_active_drawing']['properties']['en_name']
    return land

#-https://medium.com/@enigma.pythonml/how-to-create-sankey-diagrams-from-data-frames-in-python-plotly-and-kaggles-titanic-data-1f7d56b28096---------
def display_sankey(df, selected_year, land):
    filtered_df = df[df["year"] == selected_year]
    filtered_df = filtered_df.query('geo == @land & sex != "T" & age != "Y_GE80" & age != "Y_GE75"').reset_index(drop=True)

    # Bevölkerungsgruppe zu Gender
    df1 = filtered_df[filtered_df["age"] != "TOTAL"]
    df1 = df1.groupby(['age', 'sex'])['population'].max().reset_index()
    df1.columns = ['source', 'target', 'value']
    df1['target'] =df1['target'].map({'F':'Female', 'M': 'Male'})

    # Gender zu Gesamtbevölkerung
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

    fig.update_layout(title_text="Population based on Age Group and Gender",font_size=10,width=1000, height=600)

    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


# _______________________________________________________DATA__________________________________


def display_metric(df, selected_year, land):
    # Population
    pop1 = df.query('geo == @land & sex == "T" & year == @selected_year & age == "TOTAL"').reset_index(drop=True)
    pop2 = df.query('geo == @land & sex == "T" & year == @selected_year-1 & age == "TOTAL"').reset_index(drop=True)
    true_pop=str(f'{pop1["population"][0]:,}')
    # Population
    fem_pop1 = df.query('geo == @land & sex == "F" & year == @selected_year & age == "TOTAL"').reset_index(drop=True)
    fem_pop2 = df.query('geo == @land & sex == "F" & year == @selected_year-1 & age == "TOTAL"').reset_index(drop=True)

    # Male Population
    male_pop1 = df.query('geo == @land & sex == "M" & year == @selected_year & age == "TOTAL"').reset_index(drop=True)
    male_pop2 = df.query('geo == @land & sex == "M" & year == @selected_year-1 & age == "TOTAL"').reset_index(drop=True)

    col1, col2, col3= st.columns(3)
    if selected_year == 2014:
        col1.metric("Einwohner", to_million(pop1["population"]), help=true_pop)
        col2.metric("Einwohner F", to_million(fem_pop1["population"]))
        col3.metric("Einwohner M", to_million(male_pop1["population"])) 
    else:
        col1.metric("Einwohner", to_million(pop1["population"]), to_million(pop1["population"] - pop2["population"]) + " (" + str(selected_year-1) + ")", help=true_pop) 
        col2.metric("Einwohner F", to_million(fem_pop1["population"]), to_million(fem_pop1["population"] - fem_pop2["population"]) + " (" + str(selected_year-1) + ")") 
        col3.metric("Einwohner M", to_million(male_pop1["population"]), to_million(male_pop1["population"] - male_pop2["population"]) + " (" + str(selected_year-1) + ")")

def main():
    land = display_map()
    land = display_country(df, land)
    display_metric(df, selected_year, land)
    display_sankey(df, selected_year, land)
    


if __name__ == "__main__":
    main()