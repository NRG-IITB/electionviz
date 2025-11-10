'''
Module for generating election visualizations using Plotly.
'''

from enum import Enum
import plotly.express as px
import json
import pandas as pd

GEOJSON_FILE_PATH = 'data/india_parliamentary_constituencies_2024.geojson'
ELECTION_DATA_FILE_PATH = 'data/2009-2024.json'
ELECTION_YEAR = '2024'
FIGS = {}

class ElectionDataProcessor:
    def __init__(self, election_data_path, geojson_path, election_year):
        self.ELECTION_YEAR = election_year
        self.geojson_data = self._load_data(geojson_path)
        self.raw_data = self._load_data(election_data_path)
        self.pc_df = self._prepare_dataframe()

    # helper function to get candidate details
    def _get_candidate_detail(self, pc_data, year, detail_key):
        try:
            winner_name = pc_data[year]['Result']['Winner']['Candidates']
            for candidate in pc_data[year]['Candidates']:
                if candidate['Candidate Name'] == winner_name:
                    return candidate.get(detail_key)
        except (KeyError, TypeError):
            return None
        return None
    
    # helper function to get NOTA vote share
    def _find_nota_vote_share(self, pc_year_data):
        for candidate in pc_year_data.get('Candidates', []):
            if candidate.get('Candidate Name') == 'NOTA':
                votes_data = candidate.get('% of Votes Secured')
                share = votes_data.get('Over Total Votes Polled In Constituency', 0)
                return share
        return 0

    # helper function to load (Geo)JSON data
    def _load_data(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise e

    def _prepare_dataframe(self):
        data_list = []
        for pc in self.raw_data:
            pc_year_data = pc.get(self.ELECTION_YEAR, {})
            result = pc_year_data.get('Result', {})
            voters = pc_year_data.get('Voters', {})
            electors = pc_year_data.get('Electors', {})

            entry = {
                'pc_id': pc['ID'],
                'pc_name': pc['Constituency'],
                'category': pc_year_data.get('Category'),
                'total_voter_turnout': voters.get('POLLING PERCENTAGE', {}).get('Total', 100) if voters else 100,
                'male_voter_turnout': (
                    voters.get('General').get('Men') * 100 / electors.get('General').get('Men') if voters else 100
                ),
                'female_voter_turnout': (
                    voters.get('General').get('Women') * 100 / electors.get('General').get('Women') if voters else 100
                ),
                'winner_party': result.get('Winner', {}).get('Party'),
                'margin': (
                    result.get('Margin', 0) * 100 / voters.get('Total').get('Total') if voters else 100
                ),
                'vote_share_of_winner': (
                    result.get('Winner', {}).get('Votes', 0) * 100 / voters.get('Total').get('Total') if voters else 100
                ),
                'gender_of_winner': self._get_candidate_detail(pc, self.ELECTION_YEAR, 'Gender'),
                'category_of_winner': self._get_candidate_detail(pc, self.ELECTION_YEAR, 'Category'),
                'nota_vote_share': self._find_nota_vote_share(pc_year_data)
            }
            data_list.append(entry)

        pc_df = pd.DataFrame(data_list)
        
        # avoid cluttering the party-wise plot with too many small parties
        seats_by_party = {}
        for party in pc_df['winner_party']:
            if party:
                seats_by_party[party] = seats_by_party.get(party, 0) + 1
        cleaned_party_list = []
        for party in pc_df['winner_party']:
            if party and seats_by_party.get(party, 0) <= 5 and party != 'IND':
                cleaned_party_list.append('Others')
            else:
                cleaned_party_list.append(party)
        pc_df['party_of_winner'] = cleaned_party_list # new column to hold processed party info

        return pc_df

# enum for different types of plots, used to determine plotting method
class PlotType(Enum):
    MAP_CATEGORICAL = "categorical"
    MAP_CONTINUOUS = "continuous"
    MAP_DISCRETE = "discrete"

# DataPoint class to encapsulate plot details and figure generation
class DataPoint():
    def __init__(self, id, title, legend_label, type, geojson_data):
        self.id = id
        self.title = title
        self.legend_label = legend_label
        self.type = type
        self.geojson_data = geojson_data
        self.fig = None        

    def plot_fig(self, df, column):
        try:
            common_args = {
                'data_frame': df,
                'geojson': self.geojson_data,
                'locations': 'pc_id',
                'featureidkey': 'properties.pc_id',
                'color': column,
                'hover_data': [column, 'pc_name'],
                'title': self.title, 
                'labels': {column: self.legend_label}
            }

            if self.type == PlotType.MAP_CATEGORICAL:
                fig = px.choropleth(
                    **common_args,
                    category_orders={column: sorted(list(set(df[column].dropna().tolist())))},
                    color_discrete_sequence=px.colors.qualitative.Light24,
                )
            elif self.type == PlotType.MAP_CONTINUOUS or self.type == PlotType.MAP_DISCRETE:
                fig = px.choropleth(
                    **common_args,
                    color_continuous_scale="YlGnBu",
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


# load data files and prepare DataFrame
data_processor = ElectionDataProcessor(
    ELECTION_DATA_FILE_PATH, 
    GEOJSON_FILE_PATH, 
    ELECTION_YEAR
)
pc_df = data_processor.pc_df

# create DataPoint instances for each plot and generate figures
plot_configs = [
    {"id": "total_voter_turnout", "title": "Total Voter Turnout", "legend_label": "Voter Turnout (%)", "type": PlotType.MAP_CONTINUOUS},
    {"id": "male_voter_turnout", "title": "Male Voter Turnout", "legend_label": "Voter Turnout (%)", "type": PlotType.MAP_CONTINUOUS},
    {"id": "female_voter_turnout", "title": "Female Voter Turnout", "legend_label": "Voter Turnout (%)", "type": PlotType.MAP_CONTINUOUS},
    {"id": "category", "title": "Seats by Reservation Category", "legend_label": "Category", "type": PlotType.MAP_CATEGORICAL},
    {"id": "gender_of_winner", "title": "Winners by Gender", "legend_label": "Gender", "type": PlotType.MAP_CATEGORICAL},
    {"id": "category_of_winner", "title": "Winners by Category", "legend_label": "Category", "type": PlotType.MAP_CATEGORICAL},
    {"id": "party_of_winner", "title": "Winners by Party", "legend_label": "Party", "type": PlotType.MAP_CATEGORICAL},
    {"id": "margin", "title": "Winning Margins", "legend_label": "Winning Margin (%)", "type": PlotType.MAP_CONTINUOUS},
    {"id": "vote_share_of_winner", "title": "Vote Share of Winner", "legend_label": "Vote share (%)", "type": PlotType.MAP_CONTINUOUS},
    {"id": "nota_vote_share", "title": "NOTA Vote Share", "legend_label": "Vote share (%)", "type": PlotType.MAP_CONTINUOUS},
]

for config in plot_configs:
    fig = DataPoint(**config, geojson_data=data_processor.geojson_data)
    fig.plot_fig(pc_df, config['id'])
    FIGS[config['id']] = fig

# if code is run as a script, print success message
if __name__ == '__main__':
    print('All figures generated successfully.')
    print('Import this module to access the FIGS dictionary.')