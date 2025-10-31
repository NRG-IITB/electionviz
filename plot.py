'''
Module for generating election visualizations using Plotly.
'''

from enum import Enum
import plotly.express as px
import json
import pandas as pd

# global constants and variables
GEOJSON_FILE_PATH = 'data/india_parliamentary_constituencies_2024.geojson'
ELECTION_DATA_FILE_PATH = 'data/2024.json'
GEOJSON_DATA = None
ELECTION_DATA = None
FIGS = {} 

# enum for different types of plots, used to determine plotting method
class PlotType(Enum):
    MAP_CATEGORICAL = "categorical"
    MAP_CONTINUOUS = "continuous"
    MAP_DISCRETE = "discrete"

# DataPoint class to encapsulate plot details and figure generation
class DataPoint():
    def __init__(self, id: str, title: str, legend_label: str, type: PlotType):
        self.id = id
        self.title = title
        self.legend_label = legend_label
        self.type = type
        self.fig = dict
    
    def plot_fig(self, df, column):
        try:
            if self.type == PlotType.MAP_CATEGORICAL:
                fig = px.choropleth(
                    df,
                    geojson=GEOJSON_DATA,
                    locations='pc_id',
                    featureidkey='properties.pc_id',
                    color=column,
                    category_orders={column: sorted(list(set(df[column].tolist())))},
                    color_discrete_sequence=px.colors.qualitative.Light24,
                    hover_data=[column, 'pc_name'],
                    title=self.title, 
                    labels={column: self.legend_label}
                )
            elif self.type == PlotType.MAP_CONTINUOUS or self.type == PlotType.MAP_DISCRETE:
                fig = px.choropleth(
                    df,
                    geojson=GEOJSON_DATA,
                    locations='pc_id',
                    featureidkey='properties.pc_id',
                    color=column,
                    color_continuous_scale="YlGnBu",
                    hover_data=[column, 'pc_name'],
                    title=self.title, 
                    labels={column: self.legend_label}
                )
            else:
                raise ValueError("Invalid PlotType")

            fig.update_geos(
                visible=False, # only display India map area
                center={"lat": 22.0, "lon": 78.0}, # center on India
                projection_scale=5.0 # default zoom
            )
            fig.update_layout(height=700)

            self.fig = fig.to_dict()
        except Exception as e:
            print(f"An error occurred during figure plotting: {e}")
            raise e

# helper function to load (Geo)JSON data
def load_data(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"An error occurred during data loading: {e}")
        raise e
    return data

# load data files
GEOJSON_DATA = load_data(GEOJSON_FILE_PATH)
ELECTION_DATA = load_data(ELECTION_DATA_FILE_PATH)

# Parse election data and prepare DataFrame for plotting
pc_ids = [pc['ID'] for pc in ELECTION_DATA]
pc_names = [pc['Constituency'] for pc in ELECTION_DATA]
total_voter_turnout = [pc['Voters']['POLLING PERCENTAGE']['Total'] if pc['Voters'] else 100 for pc in ELECTION_DATA]
male_voter_turnout = [pc['Voters']['General']['Men']*100/pc['Electors']['General']['Men'] if pc['Voters'] else 100 for pc in ELECTION_DATA]
female_voter_turnout = [pc['Voters']['General']['Women']*100/pc['Electors']['General']['Women'] if pc['Voters'] else 100 for pc in ELECTION_DATA]
categories = [pc['Category'] for pc in ELECTION_DATA]
winners = [pc['Result']['Winner']['Party'] for pc in ELECTION_DATA]
margins = [pc['Result']['Margin']*100/pc['Voters']['Total']['Total'] if pc['Voters'] else 100 for pc in ELECTION_DATA]
gender_of_winners = []
for pc in ELECTION_DATA:
    winner = pc['Result']['Winner']['Candidates']
    for candidate in pc['Candidates']:
        if candidate['Candidate Name'] == winner:
            gender_of_winners.append(candidate['Gender'])
            break
category_of_winners = []
for pc in ELECTION_DATA:
    winner = pc['Result']['Winner']['Candidates']
    for candidate in pc['Candidates']:
        if candidate['Candidate Name'] == winner:
            category_of_winners.append(candidate['Category'])
            break
party_of_winners = [pc['Result']['Winner']['Party'] for pc in ELECTION_DATA]
party_wins = {}
for w in party_of_winners:
    if w in party_wins:
        party_wins[w] += 1
    else:
        party_wins[w] = 1
# avoid cluttering the party-wise plot with too many small parties
for i in range(len(party_of_winners)):
    if party_wins[party_of_winners[i]] <= 5 and party_of_winners[i] != 'IND':
        party_of_winners[i] = 'Others'

pc_df = pd.DataFrame({'pc_id': pc_ids, 'pc_name': pc_names, 'total_voter_turnout': total_voter_turnout, 'category': categories, 'winner_party': winners, 'margin': margins, 'male_voter_turnout': male_voter_turnout, 'female_voter_turnout': female_voter_turnout, 'gender_of_winner': gender_of_winners, 'category_of_winner': category_of_winners, 'party_of_winner': party_of_winners})

# manually create DataPoint instances for each plot and generate figures

voter_turnout_fig = DataPoint(id="total_voter_turnout", title="Total Voter Turnout", legend_label="Voter Turnout (%)", type=PlotType.MAP_CONTINUOUS)
voter_turnout_fig.plot_fig(pc_df, 'total_voter_turnout')
FIGS['total_voter_turnout'] = voter_turnout_fig

male_voter_turnout_fig = DataPoint(id="male_voter_turnout", title="Male Voter Turnout", legend_label="Voter Turnout (%)", type=PlotType.MAP_CONTINUOUS)
male_voter_turnout_fig.plot_fig(pc_df, 'male_voter_turnout')
FIGS['male_voter_turnout'] = male_voter_turnout_fig

female_voter_turnout_fig = DataPoint(id="female_voter_turnout", title="Female Voter Turnout", legend_label="Voter Turnout (%)", type=PlotType.MAP_CONTINUOUS)
female_voter_turnout_fig.plot_fig(pc_df, 'female_voter_turnout')
FIGS['female_voter_turnout'] = female_voter_turnout_fig

category_fig = DataPoint(id="category", title="Seats by Reservation Category", legend_label="Category", type=PlotType.MAP_CATEGORICAL)
category_fig.plot_fig(pc_df, 'category')
FIGS['category'] = category_fig

margins_fig = DataPoint(id="margin", title="Winning Margins", legend_label="Winning Margin (%)", type=PlotType.MAP_CONTINUOUS)
margins_fig.plot_fig(pc_df, 'margin')
FIGS['margin'] = margins_fig

winner_by_gender_fig = DataPoint(id="gender_of_winner", title="Winners by Gender", legend_label="Gender", type=PlotType.MAP_CATEGORICAL)
winner_by_gender_fig.plot_fig(pc_df, 'gender_of_winner')
FIGS['gender_of_winner'] = winner_by_gender_fig

winner_by_category_fig = DataPoint(id="category_of_winner", title="Winners by Category", legend_label="Category", type=PlotType.MAP_CATEGORICAL)
winner_by_category_fig.plot_fig(pc_df, 'category_of_winner')
FIGS['category_of_winner'] = winner_by_category_fig

winner_by_party_fig = DataPoint(id="party_of_winner", title="Winners by Party", legend_label="Party", type=PlotType.MAP_CATEGORICAL)
winner_by_party_fig.plot_fig(pc_df, 'party_of_winner')
FIGS['party_of_winner'] = winner_by_party_fig


# if code is run as a script, print success message
if __name__ == '__main__':
    print('All figures generated successfully.')
    print('Import this module to access the FIGS dictionary.')