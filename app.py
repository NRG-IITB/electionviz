'''
Server code for Election Visualization Dashboard using Dash.
Usage: python3 app.py
'''

import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from plot import FIGS, ELECTION_YEARS 

year_options = []
default_year = None

if ELECTION_YEARS and FIGS:
    year_options = [{'label': year, 'value': year} for year in ELECTION_YEARS]
    default_year = ELECTION_YEARS[-1]      
else:
    print("Warning: No data found in plot.py. FIGS or ELECTION_YEARS is empty.")

app = dash.Dash(__name__)

# define HTML layout
app.layout = html.Div(children=[
    html.H1(
        "Indian General Election Results (2009-2024)",
        style={'textAlign': 'center', 'color': '#333', 'padding': '10px'}
    ),
    
    html.Div([
        html.Label("Select Year:", style={'font-weight': 'bold'}),
        dcc.Dropdown(
            id='year-dropdown',
            options=year_options,
            value=default_year,
            clearable=False,
            style={'width': '80%', 'margin': '10px auto'}
        ),
    ], style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Select Data Point to Visualize:"),
        dcc.Dropdown(
            id='plot-dropdown',
            options=[],
            value=None,
            clearable=False,
            style={'width': '80%', 'margin': '10px auto'}
        ),
    ], style={'textAlign': 'center'}),
    
    dcc.Graph(
        id='map-graph', 
        style={
            'border': '1px solid lightgray', 
            'margin': '20px auto', 
            'width': '95%'
        }, 
        config={'displayModeBar': False}
    )
])

@callback(
    Output('plot-dropdown', 'options'),
    Output('plot-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_plot_options(selected_year):
    if not selected_year:
        return [], None
    
    year_key = selected_year
    default_plot_id = "total_voter_turnout" 
    available_figs = FIGS.get(year_key, {})
    
    if not available_figs:
        return [], None
    
    # create dropdown options from the available plots
    plot_options = [
        {'label': dp.title, 'value': dp_id} 
        for dp_id, dp in available_figs.items()
    ]
    
    # check if the preferred default exists, otherwise pick the first out of available plots
    if default_plot_id not in available_figs:
        if plot_options:
            default_plot_id = plot_options[0]['value']
        else:
            default_plot_id = None
            
    return plot_options, default_plot_id

@callback(
    Output('map-graph', 'figure'),
    Input('year-dropdown', 'value'),
    Input('plot-dropdown', 'value')
)
def update_graph(selected_year, selected_plot_id):
    if not selected_year or not selected_plot_id:
        return {}
    year_key = selected_year
    if year_key in FIGS and selected_plot_id in FIGS[year_key]:
        return FIGS[year_key][selected_plot_id].fig
    
    # return empty figure if plot id not found
    return {}

if __name__ == '__main__':
    print("Starting the app...")
    app.run(debug=True)