'''
Proof-of-Concept script to parse existing geojson data and display it in a web app.
Usage: python3 app.py
'''

import dash
from dash import dcc, html
import plotly.express as px
import json
import pandas as pd

# obtained from https://raw.githubusercontent.com/civictech-India/INDIA-GEO-JSON-Datasets/refs/heads/main/india_pc_2019.json
GEOJSON_FILE_PATH = 'data/india_pc_2019.json' 

# static data column for now
DATA_COLUMN = 'Election Phase'

# parse geojson file and generate map before starting the server, reduces client-side load time
try:
    # get the geojson data
    with open(GEOJSON_FILE_PATH, 'r') as f:
        geojson_data = json.load(f)

    # check that geojson data exists
    if geojson_data and 'features' in geojson_data:
        features_with_geometry = []
        
        for feature in geojson_data['features']:            
            if feature.get('geometry'):
                features_with_geometry.append(feature)

        # extract relevant data and create dataframe
        pc_ids = [feature['properties']['pc_id'] for feature in features_with_geometry]
        pc_names = [feature['properties']['pc_name'] for feature in features_with_geometry]
        states = [feature['properties']['st_name'] for feature in features_with_geometry]
        phases = [str(feature['properties']['2019_election_phase']) for feature in features_with_geometry]
        pc_df = pd.DataFrame({'pc_id': pc_ids, 'pc_name': pc_names, 'st_name': states, DATA_COLUMN: phases})
        
        # create the map figure
        fig = px.choropleth(
            pc_df,
            geojson=geojson_data,
            locations='pc_id',
            featureidkey='properties.pc_id',
            color=DATA_COLUMN,
            category_orders={DATA_COLUMN: sorted(list(set(pc_df[DATA_COLUMN].tolist())), key=int)}, # sort phases numerically
            hover_data=['st_name', 'pc_name'],
            title="Election phases (2019)"
        )

        fig.update_geos(
            visible=False, # only display India map area
            center={"lat": 22.0, "lon": 78.0}, # center on India
            projection_scale=5.0 # default zoom
        )
        fig.update_layout(height=700)
        
        FIGURE = fig.to_dict() # render figure once and store as dict

# handle errors
except FileNotFoundError:
    print(f"ERROR: {GEOJSON_FILE_PATH} not found")
except Exception as e:
    print(f"An error occurred during data loading or figure generation: {e}")
    raise e 

app = dash.Dash(__name__)

# define HTML layout
app.layout = html.Div(children=[
    html.H1(
        "Election Viz",
        style={'textAlign': 'center', 'color': '#333', 'padding': '10px'}
    ),
    
    dcc.Graph(id='map-graph', style={'border': '1px solid black'}, figure=FIGURE, config={'displayModeBar': False})
])

if __name__ == '__main__':
    app.run(debug=True)
