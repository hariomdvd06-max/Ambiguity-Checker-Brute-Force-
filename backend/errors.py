class GrammarValidationError(Exception):
    def __init__(self, message, reason, solution):
        self.message = message
        self.reason = reason
        self.solution = solution
        super().__init__(f"\nERROR: {message}\nReason: {reason}\nSolution: {solution}\n")

class ParsingError(Exception):
    def __init__(self, message, reason, solution):
        self.message = message
        self.reason = reason
        self.solution = solution
        super().__init__(f"\nERROR: {message}\nReason: {reason}\nSolution: {solution}\n")
