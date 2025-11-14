'''
Module for generating election visualizations using Plotly.
'''

from enum import Enum
import plotly.express as px
import json
import pandas as pd

GEOJSON_FILE_PATH = 'data/india_parliamentary_constituencies_2024.geojson'
ELECTION_DATA_FILE_PATH = 'data/2009-2024.json'
ELECTION_YEARS = ['2009', '2019', '2024'] # skip 2014 for now
FIGS = {}

class ElectionDataProcessor:
    def __init__(self, election_data_path, geojson_path):
        self.geojson_data = self._load_data(geojson_path)
        self.raw_data = self._load_data(election_data_path)
        self.pc_df = self._prepare_dataframe()

    # helper function to get candidate details
    def _get_candidate_detail(self, pc_data, year, detail_key):
        try:
            year_data = pc_data.get(year, {})
            if not year_data: return None

            winner_name = year_data['Result']['Winner']['Candidates']
            for candidate in year_data['Candidates']:
                if candidate['Candidate Name'] == winner_name:
                    return candidate.get(detail_key)
        except (KeyError, TypeError, AttributeError): # handle cases where Result, Winner, or Candidates is missing
            return None
        return None
    
    # helper function to get NOTA vote share
    def _find_nota_vote_share(self, pc_year_data):
        try:
            for candidate in pc_year_data.get('Candidates', []):
                if candidate.get('Candidate Name') == 'NOTA':
                    votes_data = candidate.get('% of Votes Secured') or {} # '% of Votes Secured' can be None if winner was unopposed
                    share = votes_data.get('Over Total Votes Polled In Constituency', 0)
                    return share
        except (KeyError, TypeError, AttributeError):
            return 0 # return 0 if data is corrupted or missing
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
            for year in ELECTION_YEARS:
                pc_year_data = pc.get(year, {})
                if not pc_year_data:
                    continue # skip if no data for this year
                
                # default to {} to prevent errors on None/null
                result = pc_year_data.get('Result', {}) or {}
                voters = pc_year_data.get('Voters') # can be None if winner was unopposed
                electors = pc_year_data.get('Electors') or {}
                voters_general = voters.get('General', {}) if voters else {}
                electors_general = electors.get('General', {}) or {}
                voters_total_dict = voters.get('Total', {}) if voters else {}
                
                # default to 0 if None
                men_voters = voters_general.get('Men') or 0
                men_electors = electors_general.get('Men') or 1 # use 1 to avoid div/0
                
                women_voters = voters_general.get('Women') or 0
                women_electors = electors_general.get('Women') or 1
                
                margin_val = result.get('Margin') or 0
                total_polled = voters_total_dict.get('Total') or 0
                
                winner_votes = (result.get('Winner', {}) or {}).get('Votes') or 0
                
                polling_percent = 0
                if voters and voters.get('POLLING PERCENTAGE'):
                    polling_percent = voters.get('POLLING PERCENTAGE').get('Total', 0)

                entry = {
                    'year': year,
                    'pc_id': pc['ID'],
                    'pc_name': pc['Constituency'],
                    'category': pc_year_data.get('Category'),
                    
                    'total_voter_turnout': polling_percent,
                    
                    'male_voter_turnout': (men_voters * 100 / men_electors) 
                        if men_electors > 0 else 0,
                        
                    'female_voter_turnout': (women_voters * 100 / women_electors) 
                        if women_electors > 0 else 0,
                        
                    'winner_party': (result.get('Winner', {}) or {}).get('Party'),
                    
                    'margin': (margin_val * 100 / total_polled) 
                        if total_polled > 0 else 0,
                        
                    'vote_share_of_winner': (winner_votes * 100 / total_polled) 
                        if total_polled > 0 else 0,
                        
                    'gender_of_winner': self._get_candidate_detail(pc, year, 'Gender'),
                    'category_of_winner': self._get_candidate_detail(pc, year, 'Category'),
                    'nota_vote_share': self._find_nota_vote_share(pc_year_data)
                }
                data_list.append(entry)

        pc_df = pd.DataFrame(data_list)
        if pc_df.empty:
            return pc_df

        seats_by_party_per_year = {}
        for year in ELECTION_YEARS:
            seats_by_party_per_year[year] = {}
        for _, row in pc_df.iterrows():
            party = row['winner_party']
            year = row['year']
            if party:
                current_counts = seats_by_party_per_year[year]
                current_counts[party] = current_counts.get(party, 0) + 1     
        cleaned_party_list = []
        for _, row in pc_df.iterrows():
            party = row['winner_party']
            year = row['year']
            party_count = seats_by_party_per_year[year].get(party, 0)
            
            if party and party_count <= 5 and party != 'IND':
                cleaned_party_list.append('Others')
            else:
                cleaned_party_list.append(party)
        pc_df['party_of_winner'] = cleaned_party_list 
        pc_df.set_index(['year', 'pc_id'], inplace=True)
        pc_df.sort_index(inplace=True)

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
    GEOJSON_FILE_PATH
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

if not pc_df.empty:
    for year in ELECTION_YEARS:
        FIGS[year] = {}
        
        # check if year exists in the index
        if year not in pc_df.index.get_level_values('year'):
            print(f"No data for year {year}, skipping.")
            continue
            
        year_df = pc_df.loc[year].reset_index()
        for config in plot_configs:
            config_with_year = config.copy()
            config_with_year['title'] = f"{config['title']}"
            
            fig = DataPoint(**config_with_year, geojson_data=data_processor.geojson_data)
            
            # check for missing data
            if config['id'] not in year_df.columns or year_df[config['id']].isnull().all():
                print(f"Warning: Column '{config['id']}' not found or is all null for {year}. Skipping this plot.")
                continue

            fig.plot_fig(year_df, config['id'])
            FIGS[year][config['id']] = fig

# if code is run as a script, print success message
if __name__ == '__main__':
    print('All figures generated successfully.')
    print('Import this module to access the FIGS dictionary (nested by year + "all_years").')