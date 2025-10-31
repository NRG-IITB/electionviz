'''
Server code for Election Visualization Dashboard using Dash.
Usage: python3 app.py
'''

import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from plot import FIGS

# get list of available plots for dropdown
plot_options = [{'label': dp.title, 'value': dp_id} for dp_id, dp in FIGS.items()]

# default plot is "Winners by Party" for now
default_plot_id = FIGS["party_of_winner"].id

app = dash.Dash(__name__)

# define HTML layout
app.layout = html.Div(children=[
    html.H1(
        "Election Viz",
        style={'textAlign': 'center', 'color': '#333', 'padding': '10px'}
    ),
    
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

# callback to update graph based on dropdown selection
@callback(
    Output('map-graph', 'figure'),
    [Input('plot-dropdown', 'value')]
)
def update_graph(selected_plot_id):
    if selected_plot_id in FIGS:
        return FIGS[selected_plot_id].fig
    
    # return empty figure if plot id not found
    return {}

if __name__ == '__main__':
    print("Starting the app...")
    app.run(debug=True)