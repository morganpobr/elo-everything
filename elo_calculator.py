class ELOCalculator:
    def __init__(self, k_factor=32):
        self.k_factor = k_factor

    def expected_score(self, rating_a, rating_b):
        """Calculate expected score for player A against player B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update_rating(self, rating, expected_score, actual_score):
        """Update a player's rating based on the expected and actual scores."""
        return rating + self.k_factor * (actual_score - expected_score)

    def process_match(self, rating_a, rating_b, result):
        """
        Process a match result and return new ratings for both players.
        result: 1 for win, 0.5 for draw, 0 for loss (from player A's perspective)
        """
        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = 1 - expected_a
        
        new_rating_a = self.update_rating(rating_a, expected_a, result)
        new_rating_b = self.update_rating(rating_b, expected_b, 1 - result)
        
        return round(new_rating_a), round(new_rating_b)
