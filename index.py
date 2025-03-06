import pygame
import sys
import time
import random
from enum import Enum

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 700
LINE_WIDTH = 15
BOARD_SIZE = 3
CELL_SIZE = 150
BOARD_PADDING = 75
X_COLOR = (229, 62, 62)  # Red for X
O_COLOR = (49, 130, 206)  # Blue for O
BG_COLOR = (162, 155, 254)  # Purple background
GRID_COLOR = (255, 255, 255)  # White grid
TEXT_COLOR = (44, 44, 44)  # Dark text
HIGHLIGHT_COLOR = (198, 246, 213)  # Light green for winning cells
BUTTON_COLOR = (110, 72, 170)  # Purple gradient for button
BUTTON_HOVER_COLOR = (157, 80, 187)  # Lighter purple for hover

# Game settings
FPS = 60


class Difficulty(Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2
    IMPOSSIBLE = 3


class Player(Enum):
    HUMAN = 'X'
    COMPUTER = 'O'


class GameState(Enum):
    PLAYING = 0
    HUMAN_WIN = 1
    COMPUTER_WIN = 2
    DRAW = 3


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False


class Dropdown:
    def __init__(self, x, y, width, height, options, initial_option, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_option = initial_option
        self.is_open = False
        self.label = label
        self.option_rects = []
        self.create_option_rects()

    def create_option_rects(self):
        self.option_rects = []
        for i, _ in enumerate(self.options):
            option_rect = pygame.Rect(
                self.rect.x, 
                self.rect.y + (i + 1) * self.rect.height,
                self.rect.width,
                self.rect.height
            )
            self.option_rects.append(option_rect)

    def draw(self, screen, font):
        # Draw the label
        label_surf = font.render(f"{self.label}: ", True, TEXT_COLOR)
        label_rect = label_surf.get_rect(midright=(self.rect.left - 10, self.rect.centery))
        screen.blit(label_surf, label_rect)
        
        # Draw the main dropdown button
        pygame.draw.rect(screen, (255, 255, 255), self.rect, border_radius=5)
        pygame.draw.rect(screen, (160, 174, 192), self.rect, 2, border_radius=5)  # Border
        
        # Draw the selected option text
        text_surf = font.render(self.selected_option, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
        # Draw dropdown arrow
        arrow_points = [
            (self.rect.right - 20, self.rect.centery - 5),
            (self.rect.right - 10, self.rect.centery + 5),
            (self.rect.right - 30, self.rect.centery + 5)
        ]
        pygame.draw.polygon(screen, (160, 174, 192), arrow_points)
        
        # Draw the dropdown list if open
        if self.is_open:
            for i, option in enumerate(self.options):
                rect = self.option_rects[i]
                pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=5)
                pygame.draw.rect(screen, (160, 174, 192), rect, 2, border_radius=5)  # Border
                
                option_surf = font.render(option, True, TEXT_COLOR)
                option_rect = option_surf.get_rect(center=rect.center)
                screen.blit(option_surf, option_rect)

    def handle_event(self, event, pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(pos):
                self.is_open = not self.is_open
                return True
            
            if self.is_open:
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(pos):
                        self.selected_option = self.options[i]
                        self.is_open = False
                        return True
                        
                # Click outside closes the dropdown
                self.is_open = False
                
        return False


class TicTacToe:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tic Tac Toe vs Computer")
        self.clock = pygame.time.Clock()
        
        # Load fonts
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.status_font = pygame.font.SysFont('Arial', 24, bold=True)
        self.cell_font = pygame.font.SysFont('Arial', 72, bold=True)
        self.button_font = pygame.font.SysFont('Arial', 24, bold=True)
        self.stats_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.stats_label_font = pygame.font.SysFont('Arial', 18)
        
        # Create buttons and dropdowns
        self.reset_button = Button(
            WIDTH // 4 - 80, 
            BOARD_PADDING + CELL_SIZE * 3 + 50, 
            160, 
            50, 
            "New Game", 
            BUTTON_COLOR, 
            BUTTON_HOVER_COLOR
        )
        
        self.undo_button = Button(
            3 * WIDTH // 4 - 80, 
            BOARD_PADDING + CELL_SIZE * 3 + 50, 
            160, 
            50, 
            "Undo Move", 
            BUTTON_COLOR, 
            BUTTON_HOVER_COLOR
        )
        
        self.difficulty_dropdown = Dropdown(
            WIDTH // 4 + 40,
            40,
            140,
            30,
            ["Easy", "Medium", "Hard", "Impossible"],
            "Medium",
            "Difficulty"
        )
        
        self.player_dropdown = Dropdown(
            3 * WIDTH // 4 + 40,
            40,
            140,
            30,
            ["You", "Computer"],
            "You",
            "First Player"
        )
        
        # Game statistics
        self.stats = {
            'wins': 0,
            'draws': 0,
            'losses': 0
        }
        
        self.initialize_game()

    def initialize_game(self):
        # Game board (empty string means empty cell)
        self.board = [''] * 9
        self.current_player = Player.HUMAN if self.player_dropdown.selected_option == "You" else Player.COMPUTER
        self.game_state = GameState.PLAYING
        self.winning_cells = []
        self.move_history = []
        
        # If computer goes first, make its move
        if self.current_player == Player.COMPUTER:
            self.computer_move()

    def draw_board(self):
        # Fill background
        self.screen.fill(BG_COLOR)
        
        # Draw title
        title_surf = self.title_font.render("Tic Tac Toe", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 25))
        self.screen.blit(title_surf, title_rect)
        
        # Draw game status
        status_text = self.get_status_text()
        status_surf = self.status_font.render(status_text, True, TEXT_COLOR)
        status_rect = status_surf.get_rect(center=(WIDTH // 2, 80))
        status_bg_rect = pygame.Rect(
            status_rect.left - 15, 
            status_rect.top - 5, 
            status_rect.width + 30, 
            status_rect.height + 10
        )
        status_bg_color = self.get_status_bg_color()
        pygame.draw.rect(self.screen, status_bg_color, status_bg_rect, border_radius=10)
        self.screen.blit(status_surf, status_rect)
        
        # Draw grid lines
        # Vertical lines
        pygame.draw.line(
            self.screen, 
            GRID_COLOR, 
            (BOARD_PADDING + CELL_SIZE, BOARD_PADDING), 
            (BOARD_PADDING + CELL_SIZE, BOARD_PADDING + 3 * CELL_SIZE), 
            LINE_WIDTH
        )
        pygame.draw.line(
            self.screen, 
            GRID_COLOR, 
            (BOARD_PADDING + 2 * CELL_SIZE, BOARD_PADDING), 
            (BOARD_PADDING + 2 * CELL_SIZE, BOARD_PADDING + 3 * CELL_SIZE), 
            LINE_WIDTH
        )
        
        # Horizontal lines
        pygame.draw.line(
            self.screen, 
            GRID_COLOR, 
            (BOARD_PADDING, BOARD_PADDING + CELL_SIZE), 
            (BOARD_PADDING + 3 * CELL_SIZE, BOARD_PADDING + CELL_SIZE), 
            LINE_WIDTH
        )
        pygame.draw.line(
            self.screen, 
            GRID_COLOR, 
            (BOARD_PADDING, BOARD_PADDING + 2 * CELL_SIZE), 
            (BOARD_PADDING + 3 * CELL_SIZE, BOARD_PADDING + 2 * CELL_SIZE), 
            LINE_WIDTH
        )
        
        # Draw X's and O's
        for row in range(3):
            for col in range(3):
                index = row * 3 + col
                x = BOARD_PADDING + col * CELL_SIZE + CELL_SIZE // 2
                y = BOARD_PADDING + row * CELL_SIZE + CELL_SIZE // 2
                
                # Highlight winning cells
                if index in self.winning_cells:
                    cell_rect = pygame.Rect(
                        BOARD_PADDING + col * CELL_SIZE + LINE_WIDTH // 2,
                        BOARD_PADDING + row * CELL_SIZE + LINE_WIDTH // 2,
                        CELL_SIZE - LINE_WIDTH,
                        CELL_SIZE - LINE_WIDTH
                    )
                    pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, cell_rect, border_radius=15)
                
                if self.board[index] == Player.HUMAN.value:
                    self.draw_x(x, y)
                elif self.board[index] == Player.COMPUTER.value:
                    self.draw_o(x, y)
        
        # Draw buttons
        self.reset_button.draw(self.screen, self.button_font)
        self.undo_button.draw(self.screen, self.button_font)
        
        # Draw dropdowns
        self.difficulty_dropdown.draw(self.screen, self.button_font)
        self.player_dropdown.draw(self.screen, self.button_font)
        
        # Draw stats
        self.draw_stats()
        
        # Draw footer
        footer_text = "You (X) vs Computer (O)"
        footer_surf = self.stats_label_font.render(footer_text, True, (74, 85, 104))
        footer_rect = footer_surf.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        self.screen.blit(footer_surf, footer_rect)
    
    def draw_x(self, x, y):
        # Draw an X at the specified position
        x_size = CELL_SIZE // 2 - 20
        pygame.draw.line(
            self.screen, 
            X_COLOR, 
            (x - x_size, y - x_size), 
            (x + x_size, y + x_size), 
            LINE_WIDTH
        )
        pygame.draw.line(
            self.screen, 
            X_COLOR, 
            (x + x_size, y - x_size), 
            (x - x_size, y + x_size), 
            LINE_WIDTH
        )
    
    def draw_o(self, x, y):
        # Draw an O at the specified position
        o_radius = CELL_SIZE // 2 - 20
        pygame.draw.circle(
            self.screen, 
            O_COLOR, 
            (x, y), 
            o_radius, 
            LINE_WIDTH
        )
    
    def draw_stats(self):
        # Background for stats
        stats_bg_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT - 150, 400, 100)
        pygame.draw.rect(self.screen, (248, 249, 250), stats_bg_rect, border_radius=10)
        
        # Draw stats
        # Wins
        wins_val_surf = self.stats_font.render(str(self.stats['wins']), True, TEXT_COLOR)
        wins_val_rect = wins_val_surf.get_rect(center=(WIDTH // 4, HEIGHT - 100))
        self.screen.blit(wins_val_surf, wins_val_rect)
        
        wins_label_surf = self.stats_label_font.render("Wins", True, (74, 85, 104))
        wins_label_rect = wins_label_surf.get_rect(center=(WIDTH // 4, HEIGHT - 75))
        self.screen.blit(wins_label_surf, wins_label_rect)
        
        # Draws
        draws_val_surf = self.stats_font.render(str(self.stats['draws']), True, TEXT_COLOR)
        draws_val_rect = draws_val_surf.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        self.screen.blit(draws_val_surf, draws_val_rect)
        
        draws_label_surf = self.stats_label_font.render("Draws", True, (74, 85, 104))
        draws_label_rect = draws_label_surf.get_rect(center=(WIDTH // 2, HEIGHT - 75))
        self.screen.blit(draws_label_surf, draws_label_rect)
        
        # Losses
        losses_val_surf = self.stats_font.render(str(self.stats['losses']), True, TEXT_COLOR)
        losses_val_rect = losses_val_surf.get_rect(center=(3 * WIDTH // 4, HEIGHT - 100))
        self.screen.blit(losses_val_surf, losses_val_rect)
        
        losses_label_surf = self.stats_label_font.render("Losses", True, (74, 85, 104))
        losses_label_rect = losses_label_surf.get_rect(center=(3 * WIDTH // 4, HEIGHT - 75))
        self.screen.blit(losses_label_surf, losses_label_rect)
        
    def get_status_text(self):
        if self.game_state == GameState.HUMAN_WIN:
            return "You win! 🎉"
        elif self.game_state == GameState.COMPUTER_WIN:
            return "Computer wins! 😢"
        elif self.game_state == GameState.DRAW:
            return "Game ended in a draw! 🤝"
        else:
            if self.current_player == Player.HUMAN:
                return "Your turn (X)"
            else:
                return "Computer's turn (O)"
    
    def get_status_bg_color(self):
        if self.game_state == GameState.HUMAN_WIN:
            return (198, 246, 213)  # Green for win
        elif self.game_state == GameState.COMPUTER_WIN:
            return (254, 215, 215)  # Red for loss
        elif self.game_state == GameState.DRAW:
            return (254, 252, 191)  # Yellow for draw
        else:
            if self.current_player == Player.HUMAN:
                return (230, 255, 250)  # Light cyan for human turn
            else:
                return (235, 244, 255)  # Light blue for computer turn
    
    def handle_click(self, pos):
        if self.game_state != GameState.PLAYING:
            return False
            
        if self.current_player != Player.HUMAN:
            return False
        
        # Check if click is on the board
        for row in range(3):
            for col in range(3):
                cell_rect = pygame.Rect(
                    BOARD_PADDING + col * CELL_SIZE,
                    BOARD_PADDING + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                
                if cell_rect.collidepoint(pos):
                    index = row * 3 + col
                    if self.board[index] == '':
                        self.make_move(index)
                        return True
        
        return False
    
    def make_move(self, index):
        # Save current state for undo
        self.save_game_state()
        
        # Apply the move
        self.board[index] = self.current_player.value
        
        # Check for win or draw
        if self.check_win():
            if self.current_player == Player.HUMAN:
                self.game_state = GameState.HUMAN_WIN
                self.stats['wins'] += 1
            else:
                self.game_state = GameState.COMPUTER_WIN
                self.stats['losses'] += 1
            return
        
        if self.check_draw():
            self.game_state = GameState.DRAW
            self.stats['draws'] += 1
            return
        
        # Switch player
        self.current_player = Player.COMPUTER if self.current_player == Player.HUMAN else Player.HUMAN
        
        # If it's computer's turn now, make its move
        if self.current_player == Player.COMPUTER:
            pygame.display.flip()  # Update the display to show human's move
            time.sleep(0.8)  # Add a slight delay for better UX
            self.computer_move()
    
    def save_game_state(self):
        self.move_history.append({
            'board': self.board.copy(),
            'player': self.current_player,
            'game_state': self.game_state
        })
    
    def undo_move(self):
        if not self.move_history:
            return False
        
        # Restore previous state
        prev_state = self.move_history.pop()
        self.board = prev_state['board']
        self.current_player = prev_state['player']
        self.game_state = prev_state['game_state']
        self.winning_cells = []  # Clear winning highlights
        
        return True
    
    def check_win(self):
        # Define winning combinations
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]             # Diagonals
        ]
        
        for combo in winning_combinations:
            a, b, c = combo
            if self.board[a] and self.board[a] == self.board[b] and self.board[a] == self.board[c]:
                self.winning_cells = combo
                return True
                
        return False
    
    def check_win_for_player(self, player):
        # Define winning combinations
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]             # Diagonals
        ]
        
        for combo in winning_combinations:
            a, b, c = combo
            if self.board[a] == player and self.board[b] == player and self.board[c] == player:
                return True
                
        return False
    
    def check_draw(self):
        return '' not in self.board
    
    def computer_move(self):
        # Save current state for undo
        self.save_game_state()
        
        difficulty = self.get_difficulty()
        cell_index = None
        
        if difficulty == Difficulty.EASY:
            cell_index = self.get_random_move()
        elif difficulty == Difficulty.MEDIUM:
            if random.random() < 0.7:
                cell_index = self.get_smart_move()
            else:
                cell_index = self.get_random_move()
        elif difficulty == Difficulty.HARD:
            if random.random() < 0.9:
                cell_index = self.get_smart_move()
            else:
                cell_index = self.get_random_move()
        else:  # IMPOSSIBLE
            cell_index = self.get_minimax_move()
        
        self.board[cell_index] = Player.COMPUTER.value
        
        # Check for win or draw
        if self.check_win():
            self.game_state = GameState.COMPUTER_WIN
            self.stats['losses'] += 1
            return
        
        if self.check_draw():
            self.game_state = GameState.DRAW
            self.stats['draws'] += 1
            return
        
        # Switch back to human
        self.current_player = Player.HUMAN
    
    def get_difficulty(self):
        difficulty_option = self.difficulty_dropdown.selected_option
        if difficulty_option == "Easy":
            return Difficulty.EASY
        elif difficulty_option == "Medium":
            return Difficulty.MEDIUM
        elif difficulty_option == "Hard":
            return Difficulty.HARD
        else:  # "Impossible"
            return Difficulty.IMPOSSIBLE
    
    def get_random_move(self):
        empty_cells = [i for i, cell in enumerate(self.board) if cell == '']
        return random.choice(empty_cells)
    
    def get_smart_move(self):
        # Check if computer can win
        for i in range(9):
            if self.board[i] == '':
                self.board[i] = Player.COMPUTER.value
                if self.check_win_for_player(Player.COMPUTER.value):
                    self.board[i] = ''  # Reset for actual move
                    return i
                self.board[i] = ''  # Reset
        
        # Check if need to block human
        for i in range(9):
            if self.board[i] == '':
                self.board[i] = Player.HUMAN.value
                if self.check_win_for_player(Player.HUMAN.value):
                    self.board[i] = ''  # Reset for actual move
                    return i
                self.board[i] = ''  # Reset
        
        # Take center if available
        if self.board[4] == '':
            return 4
        
        # Take corners if available
        corners = [0, 2, 6, 8]
        empty_corners = [corner for corner in corners if self.board[corner] == '']
        if empty_corners:
            return random.choice(empty_corners)
        
        # Take any available spot
        return self.get_random_move()
    
    def get_minimax_move(self):
        best_score = float('-inf')
        best_move = None
        
        for i in range(9):
            if self.board[i] == '':
                self.board[i] = Player.COMPUTER.value
                score = self.minimax(self.board, 0, False)
                self.board[i] = ''
                
                if score > best_score:
                    best_score = score
                    best_move = i
        
        return best_move
    
    def minimax(self, board, depth, is_maximizing):
        # Check terminal states
        if self.check_win_for_player(Player.COMPUTER.value):
            return 10 - depth
        
        if self.check_win_for_player(Player.HUMAN.value):
            return depth - 10
        
        if '' not in board:
            return 0
        
        if is_maximizing:
            best_score = float('-inf')
            for i in range(9):
                if board[i] == '':
                    board[i] = Player.COMPUTER.value
                    score = self.minimax(board, depth + 1, False)
                    board[i] = ''
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == '':
                    board[i] = Player.HUMAN.value
                    score = self.minimax(board, depth + 1, True)
                    board[i] = ''
                    best_score = min(score, best_score)
            return best_score
    
    def run(self):
        running = True
        
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle dropdown events (must be checked first)
                dropdown_changed = False
                if self.difficulty_dropdown.handle_event(event, mouse_pos):
                    dropdown_changed = True
                
                if self.player_dropdown.handle_event(event, mouse_pos):
                    dropdown_changed = True
                
                if dropdown_changed:
                    self.initialize_game()
                    continue
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        # Check for button clicks
                        if self.reset_button.is_clicked(mouse_pos, event):
                            self.initialize_game()
                        elif self.undo_button.is_clicked(mouse_pos, event):
                            if self.move_history:
                                self.undo_move()
                        else:
                            # Check for board clicks
                            self.handle_click(mouse_pos)
            
            # Update button hover states
            self.reset_button.check_hover(mouse_pos)
            self.undo_button.check_hover(mouse_pos)
            
            # Draw everything
            self.draw_board()
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


# Run the game
if __name__ == "__main__":
    game = TicTacToe()
    game.run()
