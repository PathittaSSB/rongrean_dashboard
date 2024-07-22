import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import json
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from urllib.request import urlopen
import requests

app = Dash(__name__)

# Load data
df = pd.read_csv("school_data.csv")
url = 'https://raw.githubusercontent.com/apisit/thailand.json/master/thailandWithName.json'
response = requests.get(url)
if response.status_code == 200:
    geojson = response.json()
    print("GeoJSON data loaded successfully")
else:
    print(f"Failed to retrieve the file: {response.status_code}")


province_coords = {}
for feature in geojson['features']:
    geometry = feature['geometry']
    properties = feature['properties']
    province_name = properties['name']
    
    if geometry['type'] == 'Polygon':
        coordinates = geometry['coordinates'][0]
        lats, lons = zip(*coordinates)  # Unzip coordinates into latitudes and longitudes
        centroid_lat = sum(lats) / len(lats)
        centroid_lon = sum(lons) / len(lons)
        province_coords[province_name] = [centroid_lat, centroid_lon]

df['latitude'] = df['province_english'].map(lambda x: province_coords.get(x, [None, None])[0])
df['longitude'] = df['province_english'].map(lambda x: province_coords.get(x, [None, None])[1])

def create_map(province=None):
    if province:
        dff = df[df['schools_province'] == province]
    else:
        dff = df

    fig = px.scatter_mapbox(
        dff,
        lat="latitude",
        lon="longitude",
        hover_name="schools_province",
        hover_data={"totalstd": True, "totalmale": True, "totalfemale": True, "latitude": False, "longitude": False},
        size="totalstd",
        color="totalstd",
        size_max=15,
        zoom=5,
        mapbox_style="carto-positron"
    )
    
    return fig

                                         
# App
app.layout = html.Div([
    html.H1("School Statistics in Thailand", style={'text-align': 'center'}),
    dcc.Dropdown(df.province_english.unique(), 'Narathiwat', id='dropdown-selection'),
    html.Div(id='output_container', children=[]),
    html.Br(),

    html.Div([
        dcc.Graph(id='map', style={'width': '60%'}),
        dcc.Graph(id='pie_chart', style={'width': '40%'}),
    ], style={'display': 'flex', 'justify-content': 'space-between'}),
    html.Br(),
    dcc.Graph(id='bar_chart', style={'width': '100%'})
])

@app.callback(
    [Output('output_container', 'children'),
     Output('bar_chart', 'figure'),
     Output('pie_chart', 'figure'),
     Output('map', 'figure')],
    [Input('dropdown-selection', 'value')]
)
def update_graphs(selected_province):
    container = f"The province chosen by user was: {selected_province}"

    dff = df[df["province_english"] == selected_province]

    
    colors = ['DarkTurquoise', 'RoyalBlue', 'MediumVioletRed']
    categories = ['Total', 'Male', 'Female']
    values = [dff['totalstd'].iloc[0], dff['totalmale'].iloc[0], dff['totalfemale'].iloc[0]]
    bar_fig = go.Figure()
    for i, (category, value, color) in enumerate(zip(categories, values, colors)):
        bar_fig.add_trace(go.Bar(
            x=[category],
            y=[value],
            name=category,
            marker_color=color
        ))
    bar_fig.update_layout(
        title=f'Amount of Graduated in {selected_province}',
        xaxis_title=f'{selected_province}',
        yaxis_title='จำนวน',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_color='black',
        showlegend=False
    )


    # Map
    map_fig = px.choropleth_mapbox(
        df,create_map(selected_province),
        color='province_english',
        featureidkey="properties.name",
        center={"lat": 13.30, "lon": 100.52}, 
        mapbox_style="carto-positron",
        zoom=4.35, opacity=1,
        labels={'province_english':'Province'}
    )

    map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    map_fig.add_traces(px.choropleth_mapbox(
        dff,
        geojson=geojson,
        locations='province_english',
        color='province_english',
        featureidkey="properties.name",
        center={"lat": 13.30, "lon": 100.52},
        mapbox_style="carto-positron",
        zoom=4.35, opacity=1,
        labels={'totalstd':'Province'}
    ).data)

    map_fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color= "black")

    # Pie chart
    select_data = df[df['province_english'] == selected_province]

    values = select_data[['totalmale', 'totalfemale']].values.flatten()
    labels = ['Total Male', 'Total Female']
    colors = ['RoyalBlue', 'MediumVioletRed']

    pie_fig = px.pie(
        labels=labels,
        values=values,
        color_discrete_sequence=colors
    )

    pie_fig.update_layout(
        title={'text': f'{selected_province} males and females comparison', 'x': 0.5, 'xanchor': 'center'},
        plot_bgcolor='White', paper_bgcolor='white', font_color= "black")

    return container, bar_fig, pie_fig, map_fig

if __name__ == '__main__':
    app.run_server(debug=True)