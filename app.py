'''
Server code for Election Visualization Dashboard using Dash.
Usage: python3 app.py
'''

import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from plot import FIGS, ELECTION_YEARS, TREND_FIGS
import os

# read DEBUG_MODE from env-vars, True by default
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'True').lower() in ('1', 'true', 'yes')

year_options = []
default_year = None

if ELECTION_YEARS and FIGS:
    year_options = [{'label': year, 'value': year} for year in ELECTION_YEARS]
    default_year = ELECTION_YEARS[-1]      
else:
    print("Warning: No data found in plot.py. FIGS or ELECTION_YEARS is empty.")

# extract options for the trend dropdown
trend_options = [{'label': fig['layout']['title']['text'].replace('Trend: ', ''), 'value': key} 
                 for key, fig in TREND_FIGS.items()]
default_trend = trend_options[0]['value'] if trend_options else None

# TailwindCSS for styling, fallback to no styling if remote loading fails
try:
    app = dash.Dash(__name__, external_scripts=['https://cdn.tailwindcss.com'])
except:
    app = dash.Dash(__name__)

app.title = "ElectionViz"

# define HTML layout
app.layout = html.Div(className="min-h-screen bg-slate-50 font-sans p-4 md:p-8", children=[
    html.H1(
        "Indian General Election Visualization Dashboard (2009-2024)",
        className="text-3xl md:text-4xl font-extrabold text-center text-slate-800 mb-8 drop-shadow-sm"
    ),
    
    dcc.Tabs(id="view-tabs", value='tab-maps', className="max-w-7xl mx-auto", colors={"border": "#cbd5e1", "primary": "#2563eb", "background": "#f1f5f9"}, children=[
        # tab for constituency maps
        dcc.Tab(label='Constituency Maps', value='tab-maps', className="text-slate-600 font-medium text-lg", selected_className="bg-white text-blue-600 font-bold border-t-2 border-blue-600", children=[
            html.Div(className="bg-white p-6 rounded-b-xl shadow-lg border border-slate-200", children=[
                html.Div(className="grid md:grid-cols-2 gap-6 mb-6 max-w-5xl mx-auto", children=[
                    html.Div([
                        html.Label("Select Year:", className="block text-sm font-bold text-slate-700 mb-2 uppercase tracking-wide"),
                        dcc.Dropdown(
                            id='year-dropdown',
                            options=year_options,
                            value=default_year,
                            clearable=False,
                            className="text-slate-800"
                        ),
                    ]),
                    
                    html.Div([
                        html.Label("Select Data Point to Visualize:", className="block text-sm font-bold text-slate-700 mb-2 uppercase tracking-wide"),
                        dcc.Dropdown(
                            id='plot-dropdown',
                            options=[],
                            value=None,
                            clearable=False,
                            className="text-slate-800"
                        ),
                    ]),
                ]),
                
                # display map graph with loading component
                dcc.Loading(
                    id="loading-map",
                    type="default",
                    color="#2563eb",
                    children=dcc.Graph(
                        id='map-graph', 
                        className="w-full h-[75vh] border border-slate-200 rounded-lg shadow-inner bg-slate-50", 
                        config={'displayModeBar': False}
                    )
                )
            ])
        ]),

        # tab for national trends
        dcc.Tab(label='National Trends', value='tab-trends', className="text-slate-600 font-medium text-lg", selected_className="bg-white text-blue-600 font-bold border-t-2 border-blue-600", children=[
             html.Div(className="bg-white p-6 rounded-b-xl shadow-lg border border-slate-200", children=[
                html.Div(className="max-w-3xl mx-auto mb-8", children=[
                    html.Label("Select Metric for Trend Analysis:", className="block text-sm font-bold text-slate-700 mb-2 text-center uppercase tracking-wide"),
                    dcc.Dropdown(
                        id='trend-dropdown',
                        options=trend_options,
                        value=default_trend,
                        clearable=False,
                        className="text-slate-800 shadow-sm"
                    ),
                ]),
                
                # display trend graph with loading component
                dcc.Loading(
                    id="loading-trend",
                    type="default",
                    color="#2563eb",
                    children=dcc.Graph(
                        id='trend-graph', 
                        className="w-full h-[60vh] border border-slate-200 rounded-lg shadow-inner bg-slate-50 p-2", 
                        config={'displayModeBar': False}
                    )
                )
            ])
        ])
    ])
])

@callback(
    Output('plot-dropdown', 'options'),
    Output('plot-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_map_options(selected_year):
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
def update_map_graph(selected_year, selected_plot_id):
    if not selected_year or not selected_plot_id:
        return {}
    year_key = selected_year
    if year_key in FIGS and selected_plot_id in FIGS[year_key]:
        return FIGS[year_key][selected_plot_id].fig
    
    return {}

@callback(
    Output('trend-graph', 'figure'),
    Input('trend-dropdown', 'value')
)
def update_trend_graph(selected_metric):
    if selected_metric in TREND_FIGS:
        return TREND_FIGS[selected_metric]
    return {}

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE)