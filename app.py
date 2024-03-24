import streamlit as st
import pandas as pd
import folium
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium

# df = pd.read_csv("CSV/NEWNUTS1POP.csv")
df = pd.read_csv("CSV/demo_pjangroup.csv")
geofile = "EUNUTS_ZERO.geojson"

with st.sidebar:
    option = st.selectbox("Welches Jahr soll ausgewählt werden?",
                    sorted(df['year'].unique()))

    land = st.selectbox("Welches Land soll ausgewählt werden?",
                            sorted(df['geo'].unique()))

st.title("Population " + land)

#___________________FUNCTIONS__________________________

def to_million(column):
    vz = (column.astype(float)/1000000).round(2).astype(str)[0]+ ' M'
    return vz


# ______________________________________________________MAP_____________________________________________
map = folium.Map(location=(51, 7), zoom_start=4, scrollWheelZoom=False, tiles='CartoDB positron')

choropleth = folium.Choropleth(
     geo_data=geofile,
     data=df[df["year"] == option],
     columns=('country_code', 'population'),
     key_on='feature.properties.NUTS_ID',
     line_opacity=0.8,
    highlight=True
)
choropleth.geojson.add_to(map)

df_indexed = df[(df["age"] == "TOTAL") & (df["sex"] == "T") & (df["year"] == option)].reset_index(drop=True)
df_indexed = df_indexed.set_index('country_code')
for feature in choropleth.geojson.data['features']:
     state_name = feature['properties']['NUTS_ID']
     feature['properties']['en_name'] = (df_indexed.loc[state_name, 'geo']) if state_name in list(df_indexed.index) else ''
     feature['properties']['population'] = 'Population: ' + '{:,}'.format(df_indexed.loc[state_name, 'population']) if state_name in list(df_indexed.index) else ''


choropleth.geojson.add_child(
     folium.features.GeoJsonTooltip(['en_name', 'population'], labels=False)
 )
st_map = st_folium(map, width=700, height=450)

#----------------------------------------------------------------------------------------------------------------------------

ff = df[df["year"] == option]
ff = ff[ff["geo"] == land]
ff = ff[ff["sex"] != "T"]
ff = ff[ff["age"] != "Y_GE80"]
ff = ff[ff["age"] != "Y_GE75"]

# Bevölkerungsgruppe zu Gender
ef1 = ff[ff["age"] != "TOTAL"]
ef1 = ef1.groupby(['age', 'sex'])['population'].max().reset_index()
ef1.columns = ['source', 'target', 'value']
ef1['target'] =ef1['target'].map({'F':'Female', 'M': 'Male'})

# Gender zu Gesamtbevölkerung
ef2 = ff.groupby(['sex', 'geo'])['population'].max().reset_index()
ef2 = ef2[ef2["sex"] != "T"]
ef2.columns = ['source', 'target', 'value']
ef2['source'] =ef2['source'].map({'F':'Female', 'M': 'Male'})

def new_func(ef1, ef2):
    all_links = pd.concat([ef1,ef2], axis=0)
    return all_links

all_links = new_func(ef1, ef2)
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


# ____________________________________________________________DATA__________________________________



# Population
pop1 = df.query('geo == @land & sex == "T" & year == @option & age == "TOTAL"').reset_index(drop=True)
pop2 = df.query('geo == @land & sex == "T" & year == @option-1 & age == "TOTAL"').reset_index(drop=True)
true_pop=str(f'{pop1["population"][0]:,}')
# Population
fem_pop1 = df.query('geo == @land & sex == "F" & year == @option & age == "TOTAL"').reset_index(drop=True)
fem_pop2 = df.query('geo == @land & sex == "F" & year == @option-1 & age == "TOTAL"').reset_index(drop=True)

# Male Population
male_pop1 = df.query('geo == @land & sex == "M" & year == @option & age == "TOTAL"').reset_index(drop=True)
male_pop2 = df.query('geo == @land & sex == "M" & year == @option-1 & age == "TOTAL"').reset_index(drop=True)

col1, col2, col3= st.columns(3)
if option == 2014:
    col1.metric("Einwohner", to_million(pop1["population"]), help=true_pop)
    col2.metric("Einwohner F", to_million(fem_pop1["population"]))
    col3.metric("Einwohner M", to_million(male_pop1["population"])) 
else:
    col1.metric("Einwohner", to_million(pop1["population"]), to_million(pop1["population"] - pop2["population"]) + " (" + str(option-1) + ")", help=true_pop) 
    col2.metric("Einwohner F", to_million(fem_pop1["population"]), to_million(fem_pop1["population"] - fem_pop2["population"]) + " (" + str(option-1) + ")") 
    col3.metric("Einwohner M", to_million(male_pop1["population"]), to_million(male_pop1["population"] - male_pop2["population"]) + " (" + str(option-1) + ")")