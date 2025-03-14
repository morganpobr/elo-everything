# ELO Everything

A Python-based ELO rating system for processing competition results and maintaining player ratings. This system implements the chess-style 3-result ELO rating system (win/draw/loss) and supports both leaderboard-format competitions and direct matches.

## Features

- Process competition results in leaderboard format (e.g., golf tournaments, racing)
- Maintain persistent player ratings per competition type
- Store competition results in plaintext format
- Track player competition history
- Calculate ELO rating changes using the standard chess ELO formula
- Support ties and draws in both leaderboard and direct match formats

## Project Structure

- `elo_calculator.py`: Core ELO rating calculation logic
- `player_manager.py`: Player data management and rating tracking
- `competition_manager.py`: Competition processing and results storage
- `data/`: Directory for storing player and competition data
  - `players.json`: Player database
  - `competitions.json`: Competition database
  - `results/`: Plaintext competition results

## Usage Example

```python
from competition_manager import CompetitionManager

# Initialize the manager
manager = CompetitionManager()

# Create a new golf tournament
competition_id = manager.create_competition(
    name="Golf Tournament 2025",
    date="2025-03-13",
    competition_type="golf"  # Specify the competition type
)

# Add results with ranks and scores
# Format: (player_name, rank, score)
results = [
    ("Tiger Woods", 1, 68),    # -4 for the round
    ("Rory McIlroy", 2, 69),   # -3
    ("Jordan Spieth", 2, 69),  # Tied for 2nd
    ("Dustin Johnson", 4, 70)  # -2
]
manager.add_leaderboard_results(competition_id, results)

# Process the competition and update ELO ratings
manager.process_leaderboard_competition(competition_id)

# View updated golf ratings
player_manager = manager.player_manager
golf_ratings = player_manager.get_rating_list("golf")
for player, rating in golf_ratings:
    print(f"{player}: {rating}")
```

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
