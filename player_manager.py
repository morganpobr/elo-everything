from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

class Player:
    def __init__(self, name: str, initial_rating: int = 1500):
        self.name = name
        self.ratings: Dict[str, int] = {}  # competition_type -> rating
        self.competition_history: Dict[str, List[Dict]] = {}  # competition_type -> history

    def get_rating(self, competition_type: str) -> int:
        """Get rating for specific competition type, initialize if not exists"""
        return self.ratings.get(competition_type, 1500)

    def set_rating(self, competition_type: str, rating: int):
        """Set rating for specific competition type"""
        self.ratings[competition_type] = rating

    def add_competition_result(self, competition_type: str, competition_id: str, 
                             date: str, new_rating: int):
        """Add competition result to history"""
        if competition_type not in self.competition_history:
            self.competition_history[competition_type] = []
        
        self.competition_history[competition_type].append({
            "competition_id": competition_id,
            "date": date,
            "new_rating": new_rating
        })

    def to_dict(self):
        return {
            "name": self.name,
            "ratings": self.ratings,
            "competition_history": self.competition_history
        }

class PlayerManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.players_file = self.data_dir / "players.json"
        self.players: Dict[str, Player] = {}
        self.load_players()

    def load_players(self):
        if self.players_file.exists():
            with open(self.players_file, 'r') as f:
                data = json.load(f)
                for player_data in data:
                    player = Player(player_data["name"])
                    player.ratings = player_data["ratings"]
                    player.competition_history = player_data["competition_history"]
                    self.players[player.name] = player

    def save_players(self):
        with open(self.players_file, 'w') as f:
            json.dump([p.to_dict() for p in self.players.values()], f, indent=2)

    def get_or_create_player(self, name: str, competition_type: str) -> Player:
        if name not in self.players:
            self.players[name] = Player(name)
            self.save_players()
        return self.players[name]

    def update_player_rating(self, name: str, new_rating: int, competition_id: str, 
                           competition_date: str, competition_type: str):
        player = self.get_or_create_player(name, competition_type)
        player.set_rating(competition_type, new_rating)
        player.add_competition_result(competition_type, competition_id, 
                                    competition_date, new_rating)
        self.save_players()

    def get_player_rating(self, name: str, competition_type: str) -> Optional[int]:
        player = self.players.get(name)
        return player.get_rating(competition_type) if player else None

    def get_rating_list(self, competition_type: str) -> List[tuple]:
        """Get sorted rating list for a specific competition type"""
        rated_players = [
            (p.name, p.get_rating(competition_type))
            for p in self.players.values()
            if competition_type in p.ratings
        ]
        return sorted(rated_players, key=lambda x: x[1], reverse=True)
