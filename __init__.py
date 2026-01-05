import os
import random
from typing import Dict, Any

from google.adk.agents.llm_agent import Agent

# ============================================================
# 🔐 API KEY CONFIGURATION (HARDCODED — LOCAL TESTING ONLY)
# ============================================================
API_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE"

# Optional fallback (do NOT remove)
if not API_KEY:
    raise ValueError("Gemini API key is missing. Please paste it in the code.")

# ============================================================
# GAME STATE & LOGIC (Deterministic, Persistent)
# ============================================================
class GameEngine:
    def __init__(self):
        self.round_count = 0
        self.max_rounds = 3
        self.user_score = 0
        self.bot_score = 0
        self.user_bomb_used = False
        self.bot_bomb_used = False
        self.game_over = False
        self.history = []

    def get_bot_move(self) -> str:
        options = ["rock", "paper", "scissors"]
        if not self.bot_bomb_used and random.random() < 0.1:
            return "bomb"
        return random.choice(options)

    def resolve_round(self, user_move: str) -> Dict[str, Any]:
        if self.game_over:
            return {"status": "error", "message": "Game is already over."}

        raw_input = user_move
        user_move = user_move.lower().strip()
        valid_moves = ["rock", "paper", "scissors", "bomb"]

        bot_move = self.get_bot_move()
        round_winner = "draw"
        message = ""

        self.round_count += 1

        if user_move not in valid_moves:
            round_winner = "bot"
            message = f"Invalid move '{raw_input}'. Round wasted."
        else:
            if user_move == "bomb":
                if self.user_bomb_used:
                    user_move = "invalid_bomb"
                    round_winner = "bot"
                    message = "You already used your bomb! Round wasted."
                else:
                    self.user_bomb_used = True

        if bot_move == "bomb":
            self.bot_bomb_used = True

        if not message:
            if user_move == bot_move:
                message = "Clash of wills!"
            elif user_move == "bomb":
                round_winner = "user"
                message = "BOOM! User bomb destroys everything."
            elif bot_move == "bomb":
                round_winner = "bot"
                message = "BOOM! Bot bomb destroys everything."
            elif (
                (user_move == "rock" and bot_move == "scissors") or
                (user_move == "scissors" and bot_move == "paper") or
                (user_move == "paper" and bot_move == "rock")
            ):
                round_winner = "user"
                message = "Clean hit."
            else:
                round_winner = "bot"
                message = "Bot counters effectively."

        if round_winner == "user":
            self.user_score += 1
        elif round_winner == "bot":
            self.bot_score += 1

        if self.round_count >= self.max_rounds:
            self.game_over = True

        result = {
            "round_number": self.round_count,
            "user_move_played": user_move,
            "bot_move_played": bot_move,
            "round_winner": round_winner,
            "current_score": f"User: {self.user_score} - Bot: {self.bot_score}",
            "game_over": self.game_over,
            "system_note": message
        }

        self.history.append(result)
        return result


# Persistent state
game = GameEngine()

# ============================================================
# TOOL (Explicit – required by Google ADK)
# ============================================================
def play_turn(user_move: str) -> Dict[str, Any]:
    return game.resolve_round(user_move)

# ============================================================
# AGENT CONFIGURATION (Google ADK)
# ============================================================
system_instruction = """
You are the AI Referee for Rock-Paper-Scissors-Plus.

RULES (max 5 lines):
1) Best of 3 rounds.
2) Moves: rock, paper, scissors.
3) Bomb beats all (once per player).
4) Bomb vs bomb is a draw.
5) Invalid input wastes the round.

BEHAVIOR:
- Always call play_turn when a move is given.
- Never calculate results yourself.
- Narrate using the tool output only.
- Stop when game_over is true.
"""

root_agent = Agent(
    name="rps_plus_referee",
    model="gemini-2.5-flash",
    instruction=system_instruction,
    tools=[play_turn],
)
