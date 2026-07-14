class ScoreCalculator:
    @staticmethod
    def calculate_score(difficulty, moves, seconds):
        # Score = Difficulty * 1000 - Moves * 5 - Seconds * 2
        # Difficulty matches grid_size (3, 4, 5, 6)
        base = difficulty * 1000
        deductions = (moves * 5) + (seconds * 2)
        score = base - deductions
        return max(0, score)

    @staticmethod
    def calculate_stars(difficulty, score):
        # Estimate thresholds based on difficulty
        # Easy (3x3) max is around 3000. Hard (6x6) max is around 6000.
        max_estimated = difficulty * 1000
        
        # Percentage of max score
        percentage = (score / max_estimated) * 100 if max_estimated > 0 else 0
        
        if percentage >= 75:
            return 3
        elif percentage >= 45:
            return 2
        else:
            return 1
