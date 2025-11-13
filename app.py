'''
Server code for Election Visualization Dashboard using Dash.
Usage: python3 app.py
'''

import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from plot import FIGS, ELECTION_YEARS 

year_options = []
plot_options = []
default_year = None
default_plot_id = "party_of_winner"

if ELECTION_YEARS and FIGS:
    year_options = [{'label': year, 'value': year} for year in ELECTION_YEARS]
    default_year = ELECTION_YEARS[-1]

    if default_year in FIGS:
        plot_options = [
            {'label': dp.title, 'value': dp_id} 
            for dp_id, dp in FIGS[default_year].items()
        ]
    
    if not any(opt['value'] == default_plot_id for opt in plot_options) and plot_options:
            default_plot_id = plot_options[0]['value']
        
else:
    print("Warning: No data found in plot.py. FIGS or ELECTION_YEARS is empty.")

app = dash.Dash(__name__)

# define HTML layout
app.layout = html.Div(children=[
    html.H1(
        "Election Viz",
        style={'textAlign': 'center', 'color': '#333', 'padding': '10px'}
    ),
    
    html.Div([
        html.Label("Select Year:"),
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
            options=plot_options,
            value=default_plot_id,
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

# callback to update graph based on BOTH dropdowns
@callback(
    Output('map-graph', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('plot-dropdown', 'value')]
)
def update_graph(selected_year, selected_plot_id):
    if selected_year in FIGS and selected_plot_id in FIGS[selected_year]:
        return FIGS[selected_year][selected_plot_id].fig
    
    # return empty figure if plot id not found
    return {}

if __name__ == '__main__':
    print("Starting the app...")
    app.run(debug=True)