"""
Module for interacting with the MongoDB database.
Provides an ORM-like interface for election data.
"""

from pymongo import MongoClient
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
import json

# config
MONGO_URL = "mongodb://127.0.0.1:27017/"
DB_NAME = "electionviz"
CONSTITUENCY_COLLECTION = "constituencies"

# Pydantic Models for ORM-like data structuring
class Candidate(BaseModel):
    name: str = Field(..., alias="Candidate Name")
    party: str = Field(..., alias="Party")
    votes: int = Field(..., alias="Votes")

class Result(BaseModel):
    winner: Candidate = Field(..., alias="Winner")
    runner_up: Optional[Candidate] = Field(None, alias="Runner-Up")
    margin: int = Field(..., alias="Margin")

class ElectionYearData(BaseModel):
    category: Optional[str] = Field(None, alias="Category")
    result: Result = Field(..., alias="Result")
    candidates: List[Candidate] = Field(..., alias="Candidates")
    electors: Dict[str, Any] = Field(..., alias="Electors")
    voters: Dict[str, Any] = Field(..., alias="Voters")
    votes_meta: Dict[str, Any] = Field(..., alias="Votes")

class Constituency(BaseModel):
    id: str = Field(..., alias="ID")
    name: str = Field(..., alias="Constituency")
    state_ut: str = Field(..., alias="State_UT")
    election_data: Dict[str, ElectionYearData] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)

# DB connection and operations
class MongoDBConnection:
    """Manages MongoDB connection."""
    def __init__(self, url=MONGO_URL, db_name=DB_NAME):
        self.client = MongoClient(url)
        self.db = self.client[db_name]

    def get_collection(self, collection_name):
        return self.db[collection_name]

class ElectionDB:
    def __init__(self):
        self.conn = MongoDBConnection()
        self.constituencies = self.conn.get_collection(CONSTITUENCY_COLLECTION)

    # function to get constituency by ID
    def get_constituency_by_id(self, pc_id: str) -> Optional[Constituency]:
        data = self.constituencies.find_one({"ID": pc_id})
        if data:
            election_data = {year: ElectionYearData.model_validate(e_data) for year, e_data in data.items() if year.isdigit()}
            data['election_data'] = election_data
            return Constituency.model_validate(data)
        return None

    # function to get all constituencies
    def get_all_constituencies(self):
        for data in self.constituencies.find():
            yield Constituency.model_validate(data)

    # function to get data for specific years
    def get_data_for_years(self, years: List[str]):
        for data in self.constituencies.find():
            filtered_data = {
                "ID": data["ID"],
                "Constituency": data["Constituency"],
                "State_UT": data["State_UT"],
            }
            for year in years:
                if year in data:
                    filtered_data[year] = data[year]
            yield filtered_data


if __name__ == '__main__':
    ELECTION_DATA_FILE_PATH = 'data/2009-2024.json'
    db = ElectionDB()

    # check if the collection is empty
    if db.constituencies.count_documents({}) == 0:
        print("Database collection is empty. Populating from JSON file...")
        try:
            with open(ELECTION_DATA_FILE_PATH, 'r') as f:
                all_data = json.load(f)
                if all_data:
                    db.constituencies.insert_many(all_data)
                    print(f"Successfully inserted {len(all_data)} documents.")
        except FileNotFoundError:
            print(f"Error: Data file not found at {ELECTION_DATA_FILE_PATH}")
        except Exception as e:
            print(f"An error occurred during database population: {e}")
    else:
        print("Database already contains data.")

    # verify connection and data presence
    if db.constituencies.count_documents({}) > 0:
        print("Successfully connected to the database and verified data presence.")
    else:
        print("Warning: Database is empty after execution. Please check for errors.")