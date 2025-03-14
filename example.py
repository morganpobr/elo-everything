from competition_manager import CompetitionManager

def main():
    # Initialize the competition manager
    manager = CompetitionManager()

    # Example 1: Golf Tournament with scores
    golf_id = manager.create_competition(
        name="After March Madness Golf 2025",
        date="2025-03-20",
        competition_type="golf"
    )

    # Golf results: (player_name, rank, score)
    # Lower score is better, and ties are possible
    golf_results = [
        ("Tiger Woods", 1, 68),      # -4 for the round
        ("Rory McIlroy", 2, 69),     # -3
        ("Jordan Spieth", 2, 69),    # -3 (tied with Rory)
        ("Dustin Johnson", 4, 70),   # -2
        ("Brooks Koepka", 5, 72), 
        ("Morgan O'Brien", 6, 78)
    ]

    # Add and process the golf results
    manager.add_leaderboard_results(golf_id, golf_results)
    manager.process_leaderboard_competition(golf_id)

    # Example 2: Chess Tournament with direct matches
    chess_id = manager.create_competition(
        name="Spring Chess Classic 2025",
        date="2025-03-13",
        competition_type="chess",
        format_type="direct_matches"
    )

    # Add some chess matches (1 = win, 0.5 = draw, 0 = loss)
    chess_matches = [
        ("Magnus Carlsen", "Hikaru Nakamura", 1),    # Carlsen wins
        ("Fabiano Caruana", "Wesley So", 0.5),       # Draw
        ("Magnus Carlsen", "Wesley So", 0),          # Carlsen loses
        ("Hikaru Nakamura", "Fabiano Caruana", 0.5)  # Draw
    ]

    # Add and process the chess matches
    for player_a, player_b, result in chess_matches:
        manager.add_direct_match(chess_id, player_a, player_b, result)
    manager.process_direct_matches(chess_id)

    # Display results for both tournaments
    print("\nGolf Tournament Results:")
    print(manager.get_competition_results(golf_id))
    print("\nGolf ELO Ratings:")
    golf_ratings = manager.player_manager.get_rating_list("golf")
    for player, rating in golf_ratings:
        print(f"{player}: {rating}")

    print("\nChess Tournament Results:")
    print(manager.get_competition_results(chess_id))
    print("\nChess ELO Ratings:")
    chess_ratings = manager.player_manager.get_rating_list("chess")
    for player, rating in chess_ratings:
        print(f"{player}: {rating}")

if __name__ == "__main__":
    main()
