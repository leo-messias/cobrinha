import pygame
import random
import sys

# Inicializa o Pygame
pygame.init() # Inicializa todos os módulos do pygame
pygame.mixer.init() # Inicializa o mixer para sons

# Dimensões da tela
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
DARK_GREEN = (0, 155, 0)
GRAY = (128, 128, 128)

# Direções
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Velocidade do jogo
INITIAL_FPS = 5

# Configuração da tela e fontes
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Jogo da Cobrinha')
clock = pygame.time.Clock()
font_small = pygame.font.Font(None, 24)
font_large = pygame.font.Font(None, 48)

def load_sound(filename):
    """Carrega um arquivo de som, tratando exceções de forma segura."""
    try:
        return pygame.mixer.Sound(filename)
    except (pygame.error, FileNotFoundError):
        print(f"Aviso: Arquivo de som '{filename}' não encontrado. O jogo rodará sem este som.")
        return None

# Carrega os sons
eat_sound = load_sound("new-notification-010-352755.mp3") # É recomendado usar .wav ou .ogg para efeitos sonoros curtos
game_over_sound = load_sound("large-underwater-explosion-190270.mp3")

# Carrega a música de fundo (crie um arquivo .mp3 ou .ogg e coloque na mesma pasta)
music_loaded = False
try:
    pygame.mixer.music.load("pop-happy-travel-tropical-365387.mp3")
    pygame.mixer.music.set_volume(0.5) # Ajusta o volume para 50%
    music_loaded = True
except (pygame.error, FileNotFoundError):
    print("Aviso: Arquivo de música 'background_music.mp3' não encontrado. O jogo rodará sem música.")

def draw_text(text, font, color, surface, x, y, center=False):
    """Função auxiliar para desenhar texto na tela."""
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    if center:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

class Snake:
    """Classe que representa a cobra."""
    def __init__(self):
        self.reset()

    def get_head_position(self):
        return self.positions[0]

    def turn(self, point):
        # Impede que a cobra se mova na direção oposta
        if self.length > 1 and (point[0] * -1, point[1] * -1) == self.direction:
            return
        else:
            self.direction = point

    def move(self, score, obstacle_positions):
        cur = self.get_head_position()
        x, y = self.direction
        
        new_x = cur[0] + x
        new_y = cur[1] + y

        # A partir de 10 pontos, as paredes se tornam mortais
        if score >= 10:
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                return True # Fim de jogo
        else:
            # Antes de 10 pontos, a cobra atravessa as paredes (efeito "wrap-around")
            new_x %= GRID_WIDTH
            new_y %= GRID_HEIGHT
            
        new = (new_x, new_y)

        # Verifica colisão com o próprio corpo
        if len(self.positions) > 2 and new in self.positions:
            return True # Fim de jogo

        # Verifica colisão com obstáculos
        if new in obstacle_positions:
            return True # Fim de jogo

        self.positions.insert(0, new)
        if len(self.positions) > self.length:
            self.positions.pop()
        
        return False # O jogo continua

    def reset(self):
        self.length = 1
        self.positions = [((GRID_WIDTH // 2), (GRID_HEIGHT // 2))]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.score = 0

    def draw(self, surface):
        for p in self.positions:
            r = pygame.Rect((p[0] * GRID_SIZE, p[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(surface, GREEN, r)
            pygame.draw.rect(surface, DARK_GREEN, r, 1)

class Food:
    """Classe que representa a comida."""
    def __init__(self, lifetime=8000): # Tempo de vida em milissegundos (8 segundos)
        self.position = (0, 0)
        self.color = RED
        self.lifetime = lifetime
        self.spawn_time = 0
        self.randomize_position()

    def randomize_position(self):
        self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        self.spawn_time = pygame.time.get_ticks() # Registra o tempo de surgimento

    def is_expired(self):
        """Verifica se o tempo de vida da comida expirou."""
        return pygame.time.get_ticks() - self.spawn_time > self.lifetime

    def draw(self, surface):
        r = pygame.Rect((self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, self.color, r)


class Obstacle:
    """Classe que representa os obstáculos."""
    def __init__(self):
        self.positions = []
        self.color = GRAY

    def add_obstacle(self, invalid_positions):
        """Adiciona um novo obstáculo em uma posição válida."""
        while True:
            new_pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if new_pos not in invalid_positions:
                self.positions.append(new_pos)
                break

    def draw(self, surface):
        for pos in self.positions:
            r = pygame.Rect((pos[0] * GRID_SIZE, pos[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(surface, self.color, r)

    def reset(self):
        self.positions = []


def load_highscore():
    """Carrega o recorde de um arquivo."""
    try:
        with open("highscore.txt", "r") as f:
            return int(f.read())
    except (FileNotFoundError, ValueError):
        return 0

def save_highscore(score):
    """Salva o recorde em um arquivo."""
    with open("highscore.txt", "w") as f:
        f.write(str(score))
        
def draw_hud(surface, score, highscore):
    """Desenha a pontuação e o recorde na tela."""
    draw_text(f"Pontuação: {score}", font_small, WHITE, surface, 10, 10)
    highscore_text = f"Recorde: {highscore}"
    text_width, _ = font_small.size(highscore_text)
    draw_text(highscore_text, font_small, WHITE, surface, SCREEN_WIDTH - text_width - 10, 10)
def draw_border(surface):
    """Desenha uma borda vermelha para indicar que as paredes estão ativas."""
    pygame.draw.rect(surface, RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4) # 4 pixels de espessura

def game_over_screen(score, highscore):
    """Exibe a tela de fim de jogo e aguarda a entrada do usuário."""
    while True:
        screen.fill(BLACK)
        draw_text("Fim de Jogo", font_large, RED, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, center=True)
        draw_text(f"Sua pontuação: {score}", font_small, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20, center=True)
        draw_text(f"Recorde: {highscore}", font_small, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20, center=True)
        draw_text("Pressione 'R' para jogar novamente ou 'Q' para sair.", font_small, GRAY, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4, center=True)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    return # Reinicia o jogo

def pause_screen(music_enabled):
    """Exibe a tela de pausa e aguarda a entrada do usuário."""
    if music_enabled:
        pygame.mixer.music.pause()

    while True:
        screen.fill(BLACK)
        draw_text("Pausado", font_large, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, center=True)
        draw_text("Pressione 'P' para continuar ou 'Q' para sair.", font_small, GRAY, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, center=True)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_p:
                    if music_enabled:
                        pygame.mixer.music.unpause()
                    return  # Retorna ao jogo

def start_menu():
    """Exibe o menu inicial e aguarda o jogador."""
    music_on = True
    sfx_on = True
    while True:
        screen.fill(BLACK)
        draw_text("Jogo da Cobrinha", font_large, GREEN, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, center=True)
        draw_text("Pressione ENTER para começar", font_small, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, center=True)
        music_status_text = f"Música: {'Ligada' if music_on else 'Desligada'} (Pressione M)"
        draw_text(music_status_text, font_small, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40, center=True)
        sfx_status_text = f"Efeitos: {'Ligados' if sfx_on else 'Desligados'} (Pressione S)"
        draw_text(sfx_status_text, font_small, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 70, center=True)
        draw_text("Pressione Q para sair", font_small, GRAY, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4, center=True)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    return music_on, sfx_on # Começa o jogo e retorna os estados de áudio
                if event.key == pygame.K_m:
                    music_on = not music_on
                if event.key == pygame.K_s:
                    sfx_on = not sfx_on

def main():
    """Função principal do jogo."""
    music_enabled, sfx_enabled = start_menu()
    if music_loaded and music_enabled:
        pygame.mixer.music.play(loops=-1)
    snake = Snake()
    food = Food()
    obstacles = Obstacle()
    highscore = load_highscore()
    current_fps = INITIAL_FPS

    while True:
        # Manipulação de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    pause_screen(music_enabled)
                if event.key == pygame.K_m:
                    music_enabled = not music_enabled
                    if music_loaded and music_enabled:
                        pygame.mixer.music.play(loops=-1)
                    else:
                        pygame.mixer.music.stop()
                if event.key == pygame.K_s:
                    sfx_enabled = not sfx_enabled
                if event.key in (pygame.K_UP, pygame.K_w):
                    snake.turn(UP)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    snake.turn(DOWN)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    snake.turn(LEFT)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    snake.turn(RIGHT)

        # Verifica se a comida expirou
        if food.is_expired():
            food.randomize_position()
            # Garante que a nova comida não apareça em cima da cobra ou obstáculos
            while food.position in snake.positions or food.position in obstacles.positions:
                food.randomize_position()

        # Lógica do jogo
        game_over = snake.move(snake.score, obstacles.positions)
        if game_over:
            if sfx_enabled and game_over_sound:
                game_over_sound.play()
            if snake.score > highscore:
                highscore = snake.score
                save_highscore(highscore)
            game_over_screen(snake.score, highscore)
            # Reinicia o estado do jogo para uma nova partida
            snake.reset()
            food.randomize_position()
            obstacles.reset()
            current_fps = INITIAL_FPS

        if snake.get_head_position() == food.position:
            if sfx_enabled and eat_sound:
                eat_sound.play()
            snake.length += 1
            snake.score += 1

            # Aumenta a velocidade a partir de 20 pontos
            if snake.score >= 20:
                # A cada 5 pontos acima de 19, aumenta a velocidade
                speed_increments = (snake.score - 20) // 5
                current_fps = INITIAL_FPS + 1 + speed_increments

            # Adiciona obstáculos a partir de 30 pontos
            if snake.score >= 30:
                num_obstacles_should_have = 1 + (snake.score - 30) // 5
                if len(obstacles.positions) < num_obstacles_should_have:
                    # Posições inválidas incluem a cobra e a comida (que será movida)
                    invalid_pos = snake.positions + [food.position]
                    obstacles.add_obstacle(invalid_pos)

            food.randomize_position()
            # Garante que a comida não apareça em cima da cobra ou obstáculos
            while food.position in snake.positions or food.position in obstacles.positions:
                food.randomize_position()

        # Desenho na tela
        screen.fill(BLACK)

        if snake.score >= 10:
            draw_border(screen)

        snake.draw(screen)
        food.draw(screen)
        obstacles.draw(screen)
        draw_hud(screen, snake.score, highscore)
        pygame.display.update()
        
        # Controla a velocidade do jogo
        clock.tick(current_fps)

if __name__ == '__main__':
    main()
    