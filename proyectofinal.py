import pygame
import random

# Inicialización de pygame
pygame.init()

# Dimensiones de la pantalla
WIDTH, HEIGHT = 400, 600
CELL_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = HEIGHT // CELL_SIZE
NEXT_WIDTH = 4

# Colores
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0)]
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Inicializar pantalla
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris Candy Crush")

# Reloj para controlar FPS
clock = pygame.time.Clock()

# Fuente para mostrar texto
font = pygame.font.SysFont("Arial", 20)

# Clase para manejar las piezas
class Piece:
    def __init__(self):
        self.blocks = [
            [  # Forma de T
                [(0, 0), (1, 0), (2, 0), (1, 1)],
                [(1, 0), (1, 1), (1, 2), (0, 1)],
                [(0, 1), (1, 1), (2, 1), (1, 0)],
                [(0, 1), (1, 0), (1, 1), (1, 2)]
            ],
            [  # Línea
                [(0, 0), (1, 0), (2, 0), (3, 0)],
                [(0, 0), (0, 1), (0, 2), (0, 3)]
            ],
            [  # Cuadrado (no rota)
                [(0, 0), (0, 1), (1, 0), (1, 1)]
            ]
        ]
        self.current_shape = random.choice(self.blocks)
        self.current_rotation = 0
        self.current = self.current_shape[self.current_rotation]
        self.colors = [random.choice(COLORS) for _ in self.current]
        self.x = GRID_WIDTH // 2 - 2
        self.y = 0

    def draw(self, offset_x=0, offset_y=0):
        for (dx, dy), color in zip(self.current, self.colors):
            rect = pygame.Rect((self.x + dx + offset_x) * CELL_SIZE, (self.y + dy + offset_y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)  # Dibujar borde negro

    def move(self, dx, dy, grid):
        if self.can_move(dx, dy, grid):
            self.x += dx
            self.y += dy

    def rotate(self, grid):
        next_rotation = (self.current_rotation + 1) % len(self.current_shape)
        next_state = self.current_shape[next_rotation]
        if self.can_transform(next_state, grid):
            self.current_rotation = next_rotation
            self.current = next_state

    def can_move(self, dx, dy, grid):
        for (block_x, block_y) in self.current:
            new_x = self.x + block_x + dx
            new_y = self.y + block_y + dy
            if not (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT):
                return False
            if grid[new_y][new_x] is not None:
                return False
        return True

    def can_transform(self, next_state, grid):
        for (block_x, block_y) in next_state:
            new_x = self.x + block_x
            new_y = self.y + block_y
            if not (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT):
                return False
            if grid[new_y][new_x] is not None:
                return False
        return True

    def freeze(self, grid):
        for (block_x, block_y), color in zip(self.current, self.colors):
            grid[self.y + block_y][self.x + block_x] = color

# Función para detectar y eliminar grupos
def remove_matches(grid):
    matches = set()

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x] is not None:
                color = grid[y][x]
                horizontal = find_line(grid, x, y, color, (1, 0))
                vertical = find_line(grid, x, y, color, (0, 1))

                if len(horizontal) >= 3:
                    if all(grid[y][px] == color for px, _ in horizontal):
                        matches.update(horizontal)

                if len(vertical) >= 3:
                    if all(grid[py][x] == color for _, py in vertical):
                        matches.update(vertical)

    if len(matches) >= 3:
        if len(matches) == 4:
            return remove_with_neighbors(grid, matches)
        elif len(matches) == 5:
            return remove_color(grid, matches)
        elif len(matches) >= 6:
            return clear_grid(grid)
        else:
            return remove_blocks(grid, matches)

    return False

# Encontrar líneas horizontales o verticales de colores conectados
def find_line(grid, x, y, color, direction):
    dx, dy = direction
    line = []

    while 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and grid[y][x] == color:
        line.append((x, y))
        x += dx
        y += dy

    return line

# Eliminar bloques normales
def remove_blocks(grid, matches):
    for x, y in matches:
        grid[y][x] = None
    return True

# Eliminar bloques junto con los vecinos
def remove_with_neighbors(grid, matches):
    neighbors = set()
    for x, y in matches:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                neighbors.add((nx, ny))
    matches.update(neighbors)
    return remove_blocks(grid, matches)

# Eliminar todos los bloques del mismo color
def remove_color(grid, matches):
    color = grid[next(iter(matches))[1]][next(iter(matches))[0]]
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x] == color:
                grid[y][x] = None
    return True

# Limpiar el tablero completo
def clear_grid(grid):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            grid[y][x] = None
    return True

# Aplicar gravedad para llenar huecos
def apply_gravity(grid):
    for x in range(GRID_WIDTH):
        column = [grid[y][x] for y in range(GRID_HEIGHT) if grid[y][x] is not None]
        column = [None] * (GRID_HEIGHT - len(column)) + column
        for y in range(GRID_HEIGHT):
            grid[y][x] = column[y]

# Crear la cuadrícula vacía
def create_grid():
    return [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def draw_grid(grid):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x] is not None:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, grid[y][x], rect)
                pygame.draw.rect(screen, BLACK, rect, 1)  # Dibujar borde negro
            else:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, WHITE, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)  # Dibujar cuadrícula

def main():
    grid = create_grid()
    current_piece = Piece()
    next_piece = Piece()
    score = 0
    running = True
    drop_time = 500
    last_drop = pygame.time.get_ticks()

    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.move(-1, 0, grid)
                elif event.key == pygame.K_RIGHT:
                    current_piece.move(1, 0, grid)
                elif event.key == pygame.K_DOWN:
                    current_piece.move(0, 1, grid)
                elif event.key == pygame.K_UP:
                    current_piece.rotate(grid)

        # Manejo de caída automática
        if pygame.time.get_ticks() - last_drop > drop_time:
            if current_piece.can_move(0, 1, grid):
                current_piece.move(0, 1, grid)
            else:
                current_piece.freeze(grid)

                # Verificar condición de derrota
                for block_x, block_y in current_piece.current:
                    if current_piece.y + block_y <= 0:
                        running = False

                while remove_matches(grid):
                    apply_gravity(grid)
                    score += 10
                current_piece = next_piece
                next_piece = Piece()
            last_drop = pygame.time.get_ticks()

        # Dibujar la cuadrícula
        draw_grid(grid)

        # Dibujar la pieza actual
        current_piece.draw()

        # Dibujar la siguiente pieza en su área
        next_piece_text = font.render("Next:", True, BLACK)
        screen.blit(next_piece_text, (GRID_WIDTH * CELL_SIZE + 10, 50))
        pygame.draw.rect(
            screen,
            BLACK,
            pygame.Rect(
                GRID_WIDTH * CELL_SIZE + 10,
                80,
                NEXT_WIDTH * CELL_SIZE,
                NEXT_WIDTH * CELL_SIZE,
            ),
            2,
        )
        next_piece_offset_x = GRID_WIDTH + 1.5
        next_piece_offset_y = 4
        next_piece.draw(offset_x=next_piece_offset_x, offset_y=next_piece_offset_y)

        # Dibujar el puntaje
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (WIDTH - 120, 10))

        # Actualizar la pantalla
        pygame.display.flip()

        # Control de FPS
        clock.tick(30)

    # Mostrar mensaje de fin de juego
    screen.fill(WHITE)
    game_over_text = font.render("Game Over", True, BLACK)
    final_score_text = font.render(f"Final Score: {score}", True, BLACK)
    screen.blit(game_over_text, (WIDTH // 2 - 50, HEIGHT // 2 - 30))
    screen.blit(final_score_text, (WIDTH // 2 - 50, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(3000)

if __name__ == "__main__":
    main()
