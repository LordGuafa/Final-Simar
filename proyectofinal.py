import pygame
import random
import sys
from typing import List, Tuple
from enum import Enum

# Inicialización de Pygame
pygame.init()

# Constantes
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 6)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

class BlockType(Enum):
    NORMAL = "NORMAL"
    HORIZONTAL = "HORIZONTAL"  # Elimina toda la fila
    VERTICAL = "VERTICAL"      # Elimina toda la columna
    BOMB = "BOMB"             # Elimina en área 3x3

# Colores
COLORS = {
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'PURPLE': (255, 0, 255),
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'GRAY': (128, 128, 128)
}

class Block:
    def __init__(self, x: int, y: int, color: str, block_type: BlockType = BlockType.NORMAL):
        self.x = x
        self.y = y
        self.color = color
        self.block_type = block_type

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

class Piece:
    def __init__(self):
        self.blocks = []
        base_shapes = [
            [(0,0), (1,0), (0,1), (1,1)],  # Cuadrado
            [(0,0), (1,0), (2,0), (3,0)],  # Línea
            [(0,0), (1,0), (1,1), (2,1)],  # Z
            [(1,0), (2,0), (0,1), (1,1)],  # S
            [(1,0), (0,1), (1,1), (2,1)],  # T
            [(0,0), (0,1), (1,1), (2,1)],  # L
            [(2,0), (0,1), (1,1), (2,1)]   # J
        ]
        
        shape = random.choice(base_shapes)
        for pos in shape:
            color = random.choice(list(COLORS.keys())[:-3])
            self.blocks.append(Block(pos[0] + GRID_WIDTH//2 - 1, pos[1], color))

    def move(self, dx: int, dy: int, grid: List[List[Block]]) -> bool:
        for block in self.blocks:
            new_x = block.x + dx
            new_y = block.y + dy
            if not (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT):
                return False
            if new_y >= 0 and grid[new_y][new_x] is not None:
                return False
        
        for block in self.blocks:
            block.move(dx, dy)
        return True

    def rotate(self, grid: List[List[Block]]):
        min_x = min(block.x for block in self.blocks)
        max_x = max(block.x for block in self.blocks)
        min_y = min(block.y for block in self.blocks)
        center_x = (min_x + max_x) // 2
        center_y = min_y
        
        new_positions = []
        for block in self.blocks:
            rel_x = block.x - center_x
            rel_y = block.y - center_y
            new_x = center_x - rel_y
            new_y = center_y + rel_x
            
            if not (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT):
                return False
            if new_y >= 0 and grid[new_y][new_x] is not None:
                return False
            new_positions.append((new_x, new_y))
        
        for block, new_pos in zip(self.blocks, new_positions):
            block.x, block.y = new_pos
        return True

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Tetris Color Match')
        self.clock = pygame.time.Clock()
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = Piece()
        self.next_piece = Piece()
        self.paused = False
        self.game_over = False
        self.score = 0
        self.fall_time = 0
        self.fall_speed = 500
        self.font = pygame.font.Font(None, 36)

 # Crear botón de pausa
        self.pause_button = pygame.Rect(
            SCREEN_WIDTH - 100, 10, 90, 40
        )

    def draw_pause_button(self):
        # Dibujar fondo del botón
        pygame.draw.rect(self.screen, COLORS['GRAY'], self.pause_button)
        
        # Dibujar texto del botón
        pause_text = self.font.render('PAUSE', True, COLORS['BLACK'])
        text_rect = pause_text.get_rect(center=self.pause_button.center)
        self.screen.blit(pause_text, text_rect)

    def draw_pause_screen(self):
        # Crear superficie semitransparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(COLORS['BLACK'])
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0,0))
        
        # Texto de pausa
        pause_text = self.font.render('PAUSED', True, COLORS['WHITE'])
        text_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(pause_text, text_rect)
        
        # Instrucciones
        resume_text = self.font.render('Press P to Resume', True, COLORS['WHITE'])
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(resume_text, resume_rect)
        
    def create_special_block(self, x: int, y: int, color: str, match_length: int, is_vertical: bool) -> Block:
        if match_length >= 5:
            return Block(x, y, color, BlockType.BOMB)
        elif match_length == 4:
            if is_vertical:
                return Block(x, y, color, BlockType.VERTICAL)
            else:
                return Block(x, y, color, BlockType.HORIZONTAL)
        return Block(x, y, color, BlockType.NORMAL)

    def activate_special_block(self, x: int, y: int) -> set:
        block = self.grid[y][x]
        blocks_to_remove = set()
        
        if block.block_type == BlockType.HORIZONTAL:
            # Eliminar toda la fila
            for i in range(GRID_WIDTH):
                blocks_to_remove.add((y, i))
                
        elif block.block_type == BlockType.VERTICAL:
            # Eliminar toda la columna
            for i in range(GRID_HEIGHT):
                blocks_to_remove.add((i, x))
                
        elif block.block_type == BlockType.BOMB:
            # Eliminar área 3x3
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    new_y, new_x = y + dy, x + dx
                    if 0 <= new_y < GRID_HEIGHT and 0 <= new_x < GRID_WIDTH:
                        blocks_to_remove.add((new_y, new_x))
        
        return blocks_to_remove

    def draw_block(self, block: Block, x: int, y: int):
        pygame.draw.rect(self.screen, COLORS[block.color],
                        (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE-1, BLOCK_SIZE-1))
        
        # Dibujar indicadores de bloques especiales
        if block.block_type == BlockType.HORIZONTAL:
            pygame.draw.line(self.screen, COLORS['WHITE'],
                           (x * BLOCK_SIZE, y * BLOCK_SIZE + BLOCK_SIZE//2),
                           ((x + 1) * BLOCK_SIZE - 1, y * BLOCK_SIZE + BLOCK_SIZE//2), 2)
        elif block.block_type == BlockType.VERTICAL:
            pygame.draw.line(self.screen, COLORS['WHITE'],
                           (x * BLOCK_SIZE + BLOCK_SIZE//2, y * BLOCK_SIZE),
                           (x * BLOCK_SIZE + BLOCK_SIZE//2, (y + 1) * BLOCK_SIZE - 1), 2)
        elif block.block_type == BlockType.BOMB:
            pygame.draw.circle(self.screen, COLORS['WHITE'],
                             (x * BLOCK_SIZE + BLOCK_SIZE//2, y * BLOCK_SIZE + BLOCK_SIZE//2),
                             BLOCK_SIZE//4)

    def draw_grid(self):
        self.screen.fill(COLORS['BLACK'])
        self.screen.fill(COLORS['BLACK'])  
       
        
        # Dibujar el botón de pausa
        self.draw_pause_button()
        
        # Si el juego está pausado, dibujar la pantalla de pausa
        if self.paused:
            self.draw_pause_screen()
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(self.screen, COLORS['GRAY'],
                               (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)
                if self.grid[y][x]:
                    self.draw_block(self.grid[y][x], x, y)
        
        for block in self.current_piece.blocks:
            if block.y >= 0:
                self.draw_block(block, block.x, block.y)
        
        next_piece_text = self.font.render('Next:', True, COLORS['WHITE'])
        self.screen.blit(next_piece_text, (GRID_WIDTH * BLOCK_SIZE + 10, 10))
        for block in self.next_piece.blocks:
            self.draw_block(block, block.x - GRID_WIDTH//2 + GRID_WIDTH + 2, block.y + 2)
        
        score_text = self.font.render(f'Score: {self.score}', True, COLORS['WHITE'])
        self.screen.blit(score_text, (GRID_WIDTH * BLOCK_SIZE + 10, 100))

    def check_matches(self) -> int:
        matches = set()
        special_blocks = []
        score = 0
        color_matches = {}
        
        # Horizontal matches
        for y in range(GRID_HEIGHT):
            color_count = 1
            current_color = None
            start_x = 0
            
            for x in range(GRID_WIDTH):
                if self.grid[y][x] and self.grid[y][x].color == current_color and current_color is not None:
                    color_count += 1
                else:
                    if color_count >= 3:
                        # Track color matches for special removal
                        if current_color not in color_matches:
                            color_matches[current_color] = set()
                        
                        # Add match blocks to color tracking
                        for i in range(start_x, start_x + color_count):
                            color_matches[current_color].add((y, i))
                        
                        # Handle 4-block match
                        if color_count == 4:
                            # Remove match blocks and ALL adjacent blocks
                            for dy in [-1, 0, 1]:
                                for dx in [-1, 0, 1]:
                                    for i in range(start_x - 1, start_x + color_count + 1):
                                        new_y = y + dy
                                        new_x = i + dx
                                        if 0 <= new_y < GRID_HEIGHT and 0 <= new_x < GRID_WIDTH:
                                            matches.add((new_y, new_x))
                        
                        # Normal match process for 3+ blocks
                        for i in range(start_x, start_x + color_count):
                            if self.grid[y][i] and self.grid[y][i].block_type != BlockType.NORMAL:
                                matches.update(self.activate_special_block(i, y))
                            matches.add((y, i))
                        
                        score += color_count * 100
                    
                    color_count = 1
                    current_color = self.grid[y][x].color if self.grid[y][x] else None
                    start_x = x
            
            # Handle end of row match
            if color_count >= 3:
                if current_color not in color_matches:
                    color_matches[current_color] = set()
                
                for i in range(start_x, start_x + color_count):
                    color_matches[current_color].add((y, i))
                
                if color_count == 4:
                    # Remove match blocks and ALL adjacent blocks
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            for i in range(start_x - 1, start_x + color_count + 1):
                                new_y = y + dy
                                new_x = i + dx
                                if 0 <= new_y < GRID_HEIGHT and 0 <= new_x < GRID_WIDTH:
                                    matches.add((new_y, new_x))
                
                for i in range(start_x, start_x + color_count):
                    if self.grid[y][i] and self.grid[y][i].block_type != BlockType.NORMAL:
                        matches.update(self.activate_special_block(i, y))
                    matches.add((y, i))
                
                score += color_count * 100

        # Vertical matches (same logic)
        for x in range(GRID_WIDTH):
            color_count = 1
            current_color = None
            start_y = 0
            
            for y in range(GRID_HEIGHT):
                if self.grid[y][x] and self.grid[y][x].color == current_color and current_color is not None:
                    color_count += 1
                else:
                    if color_count >= 3:
                        # Track color matches for special removal
                        if current_color not in color_matches:
                            color_matches[current_color] = set()
                        
                        # Add match blocks to color tracking
                        for i in range(start_y, start_y + color_count):
                            color_matches[current_color].add((i, x))
                        
                        # Handle 4-block match
                        if color_count == 4:
                            # Remove match blocks and ALL adjacent blocks
                            for dy in [-1, 0, 1]:
                                for dx in [-1, 0, 1]:
                                    for i in range(start_y - 1, start_y + color_count + 1):
                                        new_y = i + dy
                                        new_x = x + dx
                                        if 0 <= new_y < GRID_HEIGHT and 0 <= new_x < GRID_WIDTH:
                                            matches.add((new_y, new_x))
                        
                        # Normal match process for 3+ blocks
                        for i in range(start_y, start_y + color_count):
                            if self.grid[i][x] and self.grid[i][x].block_type != BlockType.NORMAL:
                                matches.update(self.activate_special_block(x, i))
                            matches.add((i, x))
                        
                        score += color_count * 100
                    
                    color_count = 1
                    current_color = self.grid[y][x].color if self.grid[y][x] else None
                    start_y = y
            
            # Handle end of column match
            if color_count >= 3:
                if current_color not in color_matches:
                    color_matches[current_color] = set()
                
                for i in range(start_y, start_y + color_count):
                    color_matches[current_color].add((i, x))
                
                if color_count == 4:
                    # Remove match blocks and ALL adjacent blocks
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            for i in range(start_y - 1, start_y + color_count + 1):
                                new_y = i + dy
                                new_x = x + dx
                                if 0 <= new_y < GRID_HEIGHT and 0 <= new_x < GRID_WIDTH:
                                    matches.add((new_y, new_x))
                
                for i in range(start_y, start_y + color_count):
                    if self.grid[i][x] and self.grid[i][x].block_type != BlockType.NORMAL:
                        matches.update(self.activate_special_block(x, i))
                    matches.add((i, x))
                
                score += color_count * 100

        # Handle 5-block color matches - remove all blocks of that color
        for color, color_match_blocks in color_matches.items():
            if len(color_match_blocks) == 5:
                for y in range(GRID_HEIGHT):
                    for x in range(GRID_WIDTH):
                        if self.grid[y][x] and self.grid[y][x].color == color:
                            matches.add((y, x))

        # Handle 6+ block matches - clear entire board
        if any(len(color_match_blocks) >= 6 for color_match_blocks in color_matches.values()):
            matches = {(y, x) for y in range(GRID_HEIGHT) for x in range(GRID_WIDTH) if self.grid[y][x] is not None}

        # Remove matched blocks
        for y, x in matches:
            self.grid[y][x] = None
        
        # Make blocks fall
        if matches:
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT-2, -1, -1):
                    if self.grid[y][x] is not None:
                        current_y = y
                        while current_y + 1 < GRID_HEIGHT and self.grid[current_y + 1][x] is None:
                            self.grid[current_y + 1][x] = self.grid[current_y][x]
                            self.grid[current_y][x] = None
                            current_y += 1
        
        return score

    def run(self):
        while not self.game_over:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Verificar si se hizo clic en el botón de pausa
                    if self.pause_button.collidepoint(event.pos):
                        self.paused = not self.paused
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:  # También pausar con la tecla P
                        self.paused = not self.paused
                    
                    if not self.paused:  # Solo procesar teclas si no está pausado
                        if event.key == pygame.K_LEFT:
                            self.current_piece.move(-1, 0, self.grid)
                        elif event.key == pygame.K_RIGHT:
                            self.current_piece.move(1, 0, self.grid)
                        elif event.key == pygame.K_DOWN:
                            self.current_piece.move(0, 1, self.grid)
                        elif event.key == pygame.K_UP:
                            self.current_piece.rotate(self.grid)
            
            if not self.paused:  # Solo actualizar el juego si no está pausado
                # Caída automática
                if current_time - self.fall_time > self.fall_speed:
                    if not self.current_piece.move(0, 1, self.grid):
                        # Fijar la pieza en la cuadrícula
                        for block in self.current_piece.blocks:
                            if block.y >= 0:
                                self.grid[block.y][block.x] = block
                        
                        # Verificar coincidencias
                        self.score += self.check_matches()
                        
                        # Crear nueva pieza
                        self.current_piece = self.next_piece
                        self.next_piece = Piece()
                        
                        # Verificar game over
                        for block in self.current_piece.blocks:
                            if block.y >= 0 and self.grid[block.y][block.x] is not None:
                                self.game_over = True
                                break
                    
                    self.fall_time = current_time
            
            self.draw_grid()
            pygame.display.flip()
            self.clock.tick(60)
        
        # Pantalla de game over
        game_over_text = self.font.render('GAME OVER', True, COLORS['WHITE'])
        self.screen.blit(game_over_text, 
                        (SCREEN_WIDTH//2 - game_over_text.get_width()//2,
                         SCREEN_HEIGHT//2 - game_over_text.get_height()//2))
        pygame.display.flip()
        
        # Esperar antes de cerrar
        pygame.time.wait(2000)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()