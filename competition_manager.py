from datetime import datetime
import json
from pathlib import Path
from elo_calculator import ELOCalculator
from player_manager import PlayerManager
from typing import List, Dict, Union, Tuple

class CompetitionResult:
    def __init__(self, player_name: str, rank: int, score: Union[float, None] = None):
        self.player_name = player_name
        self.rank = rank  # Lower is better (1st place = 1)
        self.score = score  # Optional score (e.g., golf strokes)

    def to_dict(self):
        return {
            "player_name": self.player_name,
            "rank": self.rank,
            "score": self.score
        }

    @staticmethod
    def from_dict(data):
        return CompetitionResult(data["player_name"], data["rank"], data.get("score"))

class DirectMatch:
    def __init__(self, player_a: str, player_b: str, result: float):
        self.player_a = player_a
        self.player_b = player_b
        self.result = result  # 1 for A wins, 0.5 for draw, 0 for B wins

    def to_dict(self):
        return {
            "player_a": self.player_a,
            "player_b": self.player_b,
            "result": self.result
        }

    @staticmethod
    def from_dict(data):
        return DirectMatch(data["player_a"], data["player_b"], data["result"])

class Competition:
    def __init__(self, competition_id: str, name: str, date: str, competition_type: str, format_type: str = "leaderboard"):
        self.competition_id = competition_id
        self.name = name
        self.date = date
        self.competition_type = competition_type  # e.g., "golf", "soccer", "chess"
        self.format_type = format_type  # "leaderboard" or "direct_matches"
        self.results: List[Union[CompetitionResult, DirectMatch]] = []
        self.processed = False

    def to_dict(self):
        return {
            "competition_id": self.competition_id,
            "name": self.name,
            "date": self.date,
            "competition_type": self.competition_type,
            "format_type": self.format_type,
            "results": [r.to_dict() for r in self.results],
            "processed": self.processed
        }

class CompetitionManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.competitions_file = self.data_dir / "competitions.json"
        self.results_dir = self.data_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.competitions: Dict[str, Competition] = {}
        self.elo_calculator = ELOCalculator()
        self.player_manager = PlayerManager(data_dir)
        self.load_competitions()

    def load_competitions(self):
        if self.competitions_file.exists():
            with open(self.competitions_file, 'r') as f:
                data = json.load(f)
                for comp_data in data:
                    competition = Competition(
                        comp_data["competition_id"],
                        comp_data["name"],
                        comp_data["date"],
                        comp_data["competition_type"],
                        comp_data["format_type"]
                    )
                    if competition.format_type == "leaderboard":
                        competition.results = [CompetitionResult.from_dict(r) for r in comp_data["results"]]
                    else:
                        competition.results = [DirectMatch.from_dict(r) for r in comp_data["results"]]
                    competition.processed = comp_data["processed"]
                    self.competitions[competition.competition_id] = competition

    def save_competitions(self):
        with open(self.competitions_file, 'w') as f:
            json.dump([c.to_dict() for c in self.competitions.values()], f, indent=2)

    def create_competition(self, name: str, date: str, competition_type: str, format_type: str = "leaderboard") -> str:
        competition_id = f"{competition_type}_{name.lower().replace(' ', '_')}_{date}"
        competition = Competition(competition_id, name, date, competition_type, format_type)
        self.competitions[competition_id] = competition
        self.save_competitions()
        return competition_id

    def add_leaderboard_results(self, competition_id: str, results: List[Tuple[str, int, Union[float, None]]]):
        """
        Add results for a leaderboard-format competition.
        results: List of tuples (player_name, rank, score)
        Score is optional and can be None
        """
        if competition_id not in self.competitions:
            raise ValueError("Competition not found")
            
        competition = self.competitions[competition_id]
        if competition.processed:
            raise ValueError("Competition already processed")
            
        competition.results = [CompetitionResult(name, rank, score) for name, rank, score in results]
        
        # Save results to plaintext file
        results_file = self.results_dir / f"{competition_id}_results.txt"
        with open(results_file, 'w') as f:
            f.write(f"Competition: {competition.name}\n")
            f.write(f"Type: {competition.competition_type}\n")
            f.write(f"Date: {competition.date}\n")
            f.write("Rankings:\n")
            
            # Group players by rank to handle ties
            rank_groups = {}
            for result in competition.results:
                if result.rank not in rank_groups:
                    rank_groups[result.rank] = []
                rank_groups[result.rank].append(result)
            
            for rank in sorted(rank_groups.keys()):
                players = rank_groups[rank]
                for player in players:
                    score_str = f" (Score: {player.score})" if player.score is not None else ""
                    f.write(f"{rank}. {player.player_name}{score_str}\n")

        self.save_competitions()

    def add_direct_match(self, competition_id: str, player_a: str, player_b: str, result: float):
        """Add a direct match result (1 for A wins, 0.5 for draw, 0 for B wins)"""
        if competition_id not in self.competitions:
            raise ValueError("Competition not found")
            
        competition = self.competitions[competition_id]
        if competition.format_type != "direct_matches":
            raise ValueError("Competition is not a direct match format")
            
        if competition.processed:
            raise ValueError("Competition already processed")
            
        match = DirectMatch(player_a, player_b, result)
        competition.results.append(match)
        
        # Save match to plaintext file
        results_file = self.results_dir / f"{competition_id}_results.txt"
        with open(results_file, 'a') as f:
            result_str = "won against" if result == 1 else "drew with" if result == 0.5 else "lost to"
            f.write(f"{player_a} {result_str} {player_b}\n")
            
        self.save_competitions()

    def determine_match_result(self, competition_id: str, player_a_rank: int, player_b_rank: int, 
                             player_a_score: Union[float, None], player_b_score: Union[float, None]) -> float:
        """Determine match result between two players based on rank and score"""
        if player_a_rank == player_b_rank:
            return 0.5  # Tie
        elif player_a_score is not None and player_b_score is not None:
            # For golf, lower score is better
            if self.competitions[competition_id].competition_type == "golf":
                return 1.0 if player_a_score < player_b_score else 0.0
            # For most other sports, higher score is better
            return 1.0 if player_a_score > player_b_score else 0.0
        # If no scores available, use ranks
        return 1.0 if player_a_rank < player_b_rank else 0.0

    def process_leaderboard_competition(self, competition_id: str):
        """Process all head-to-head matches implied by a leaderboard competition."""
        competition = self.competitions[competition_id]
        if competition.processed:
            return
            
        # Store initial ratings for all players
        initial_ratings = {
            result.player_name: self.player_manager.get_or_create_player(
                result.player_name, competition.competition_type
            ).get_rating(competition.competition_type)
            for result in competition.results
        }

        # Process each implied head-to-head match
        total_rating_changes = {player: 0 for player in initial_ratings}
        for i, player_a_result in enumerate(competition.results):
            for player_b_result in competition.results[i+1:]:
                result = self.determine_match_result(
                    competition_id,
                    player_a_result.rank, player_b_result.rank,
                    player_a_result.score, player_b_result.score
                )
                
                rating_change_a, rating_change_b = self.elo_calculator.process_match(
                    initial_ratings[player_a_result.player_name],
                    initial_ratings[player_b_result.player_name],
                    result
                )
                
                # Calculate rating changes from initial ratings
                change_a = rating_change_a - initial_ratings[player_a_result.player_name]
                change_b = rating_change_b - initial_ratings[player_b_result.player_name]
                
                # Accumulate changes
                total_rating_changes[player_a_result.player_name] += change_a
                total_rating_changes[player_b_result.player_name] += change_b

        # Apply total rating changes to initial ratings
        final_ratings = {
            player: initial_ratings[player] + total_rating_changes[player]
            for player in initial_ratings
        }

        # Update all players' final ratings
        for player_name, final_rating in final_ratings.items():
            self.player_manager.update_player_rating(
                player_name,
                final_rating,
                competition_id,
                competition.date,
                competition.competition_type
            )

        competition.processed = True
        self.save_competitions()

    def process_direct_matches(self, competition_id: str):
        """Process a competition consisting of direct matches."""
        competition = self.competitions[competition_id]
        if competition.processed:
            return

        # Store initial ratings for all players
        players = set()
        for match in competition.results:
            players.add(match.player_a)
            players.add(match.player_b)
            
        initial_ratings = {
            player: self.player_manager.get_or_create_player(
                player, competition.competition_type
            ).get_rating(competition.competition_type)
            for player in players
        }

        # Process each match using initial ratings
        final_ratings = initial_ratings.copy()
        for match in competition.results:
            new_rating_a, new_rating_b = self.elo_calculator.process_match(
                initial_ratings[match.player_a],
                initial_ratings[match.player_b],
                match.result
            )
            final_ratings[match.player_a] = new_rating_a
            final_ratings[match.player_b] = new_rating_b

        # Update all players' final ratings
        for player, rating in final_ratings.items():
            self.player_manager.update_player_rating(
                player,
                rating,
                competition_id,
                competition.date,
                competition.competition_type
            )

        competition.processed = True
        self.save_competitions()

    def get_competition_results(self, competition_id: str) -> str:
        """Get the plaintext results for a competition."""
        results_file = self.results_dir / f"{competition_id}_results.txt"
        if results_file.exists():
            with open(results_file, 'r') as f:
                return f.read()
        return None

    def reprocess_competitions(self, competition_type: str = None):
        """
        Reprocess all competitions for a given type (or all types) in chronological order.
        This resets all player ratings to their initial values and processes competitions by date.
        """
        # Reset all player ratings
        for player in self.player_manager.players.values():
            if competition_type:
                if competition_type in player.ratings:
                    player.ratings[competition_type] = 1500
                    player.competition_history[competition_type] = []
            else:
                player.ratings = {ct: 1500 for ct in player.ratings.keys()}
                player.competition_history = {ct: [] for ct in player.competition_history.keys()}
        
        # Get competitions to reprocess
        competitions = []
        for comp in self.competitions.values():
            if not competition_type or comp.competition_type == competition_type:
                comp.processed = False
                competitions.append(comp)
        
        # Sort by date and reprocess
        competitions.sort(key=lambda x: x.date)
        for comp in competitions:
            if comp.format_type == "leaderboard":
                self.process_leaderboard_competition(comp.competition_id)
            else:
                self.process_direct_matches(comp.competition_id)
        
        # Save updated player data
        self.player_manager.save_players()
