import pygame
import random
import math

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Z - Mobile Edition")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
YELLOW = (220, 220, 50)
CYAN = (0, 200, 200)
BROWN = (139, 69, 19)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)

# Fonts
font_small = pygame.font.SysFont(None, 24)
font_med = pygame.font.SysFont(None, 32)
font_large = pygame.font.SysFont(None, 48)

# Game States: 0: Menu, 1: Selection, 2: Gameplay, 3: Game Over, 4: Win
game_state = 0

# Global Variables
selected_map = "Jungle"
selected_character = "Commando"
player_hp = 200
max_player_hp = 200
gun_damage = 50
score = 0
game_time = 600.0  # 10 minutes in seconds

# Entities
player = None
zombies = []
axes = []
loots = []

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.radius = 20
        self.angle = 0

    def move(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += self.speed
        
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
            
        self.x += dx
        self.y += dy
        
        # Map Boundaries
        self.x = max(50, min(2950, self.x))
        self.y = max(50, min(2950, self.y))
        
        if dx != 0 or dy != 0:
            self.angle = math.atan2(dy, dx)

    def draw(self, surface, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        pygame.draw.circle(surface, CYAN, (int(sx), int(sy)), self.radius)
        hx = sx + math.cos(self.angle) * 25
        hy = sy + math.sin(self.angle) * 25
        pygame.draw.line(surface, BLACK, (sx, sy), (hx, hy), 6)

class Zombie:
    def __init__(self, x, y, z_type):
        self.x = x
        self.y = y
        self.z_type = z_type
        self.hp = 200 if z_type == "normal" else 500
        self.max_hp = self.hp
        self.speed = 2.5 if z_type == "normal" else 1.8
        self.radius = 18 if z_type == "normal" else 26
        self.attack_cooldown = 0

    def update(self, player_x, player_y):
        global player_hp
        dist = math.hypot(player_x - self.x, player_y - self.y)
        if dist > 5:
            angle = math.atan2(player_y - self.y, player_x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
            
        # 100m range axe throw
        if dist <= 300:
            self.attack_cooldown += 1
            if self.attack_cooldown >= 120:
                self.attack_cooldown = 0
                axes.append(ThrowingAxe(self.x, self.y, player_x, player_y))

    def draw(self, surface, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        color_z = GREEN if self.z_type == "normal" else DARK_GREEN
        pygame.draw.circle(surface, color_z, (int(sx), int(sy)), self.radius)
        
        bar_w = 40
        bar_h = 6
        fill = max(0, (self.hp / self.max_hp) * bar_w)
        pygame.draw.rect(surface, RED, (sx - bar_w/2, sy - self.radius - 12, bar_w, bar_h))
        pygame.draw.rect(surface, GREEN, (sx - bar_w/2, sy - self.radius - 12, fill, bar_h))

class ThrowingAxe:
    def __init__(self, x, y, tx, ty):
        self.x = x
        self.y = y
        angle = math.atan2(ty - y, tx - x)
        self.vx = math.cos(angle) * 7
        self.vy = math.sin(angle) * 7
        self.active = True

    def update(self, player_x, player_y):
        global player_hp
        self.x += self.vx
        self.y += self.vy
        if math.hypot(player_x - self.x, player_y - self.y) < 20:
            player_hp -= 25
            self.active = False

    def draw(self, surface, cam_x, cam_y):
        pygame.draw.circle(surface, BROWN, (int(self.x - cam_x), int(self.y - cam_y)), 6)

class Loot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, surface, cam_x, cam_y):
        pygame.draw.rect(surface, GREEN, (int(self.x - cam_x - 8), int(self.y - cam_y - 8), 16, 16))

def start_game():
    global player, zombies, loots, game_state, player_hp, max_player_hp, score, game_time, gun_damage
    game_state = 2
    max_player_hp = 200 if selected_character == "Commando" else 300
    player_hp = max_player_hp
    score = 0
    game_time = 600.0
    gun_damage = 50
    
    player = Player(1500, 1500)
    zombies.clear()
    axes.clear()
    loots.clear()
    
    for i in range(100):
        z_type = "normal" if i < 50 else "heavy"
        zombies.append(Zombie(random.randint(200, 2800), random.randint(200, 2800), z_type))
        
    for _ in range(25):
        loots.append(Loot(random.randint(200, 2800), random.randint(200, 2800)))

def run_game():
    global game_state, player_hp, score, gun_damage, game_time
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        screen.fill((20, 40, 20))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            if game_state == 0:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if WIDTH//2 - 150 <= mx <= WIDTH//2 + 150:
                        if 300 <= my <= 380:
                            game_state = 1
                        elif 420 <= my <= 500:
                            pygame.quit()
                            exit()
                            
            elif game_state == 1:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if WIDTH//2 - 200 <= mx <= WIDTH//2 + 200:
                        if 450 <= my <= 530:
                            start_game()
                            
            elif game_state == 2:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mx, my = event.pos
                        cam_x = player.x - WIDTH // 2
                        cam_y = player.y - HEIGHT // 2
                        target_wx = mx + cam_x
                        target_wy = my + cam_y
                        
                        for z in zombies[:]:
                            if math.hypot(z.x - target_wx, z.y - target_wy) < z.radius + 15:
                                z.hp -= gun_damage
                                if z.hp <= 0:
                                    zombies.remove(z)
                                    score += 50
                                    if len(zombies) == 0:
                                        game_state = 4
                                break
                                
            elif game_state in [3, 4]:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    game_state = 0

        if game_state == 0:
            screen.fill(DARK_GRAY)
            title = font_large.render("ZOMBIE Z: MOBILE SURVIVAL", True, YELLOW)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
            
            pygame.draw.rect(screen, RED, (WIDTH//2 - 150, 300, 300, 80))
            play_text = font_med.render("PLAY GAME", True, WHITE)
            screen.blit(play_text, (WIDTH//2 - play_text.get_width()//2, 325))
            
            pygame.draw.rect(screen, GRAY, (WIDTH//2 - 150, 420, 300, 80))
            exit_text = font_med.render("EXIT", True, WHITE)
            screen.blit(exit_text, (WIDTH//2 - exit_text.get_width()//2, 445))

        elif game_state == 1:
            screen.fill(DARK_GRAY)
            title = font_large.render("MAP & CHARACTER SELECT", True, YELLOW)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            
            map_txt = font_med.render("Map: Jungle (Unlocked) | Ice/Desert (Locked)", True, GREEN)
            screen.blit(map_txt, (WIDTH//2 - map_txt.get_width()//2, 220))
            
            char_txt = font_med.render("Character: Commando (HP 200) / Tank (HP 300)", True, CYAN)
            screen.blit(char_txt, (WIDTH//2 - char_txt.get_width()//2, 320))
            
            pygame.draw.rect(screen, (200, 120, 20), (WIDTH//2 - 200, 450, 400, 80))
            start_btn = font_large.render("START BATTLE", True, WHITE)
            screen.blit(start_btn, (WIDTH//2 - start_btn.get_width()//2, 470))

        elif game_state == 2:
            game_time -= dt
            if game_time <= 0 or player_hp <= 0:
                game_state = 3
                
            keys = pygame.key.get_pressed()
            player.move(keys)
            
            cam_x = player.x - WIDTH // 2
            cam_y = player.y - HEIGHT // 2
            
            for z in zombies:
                z.update(player.x, player.y)
                
            for axe in axes[:]:
                axe.update(player.x, player.y)
                if not axe.active:
                    axes.remove(axe)
                    
            for loot in loots[:]:
                if math.hypot(player.x - loot.x, player.y - loot.y) < 25:
                    player_hp = min(player_hp + 50, max_player_hp)
                    loots.remove(loot)

            if keys[pygame.K_u] and score >= 100:
                score -= 100
                gun_damage += 25

            screen.fill(GREEN)
            pygame.draw.rect(screen, BLUE, (-cam_x + 1400, -cam_y, 200, 3000))
            
            for loot in loots:
                loot.draw(screen, cam_x, cam_y)
            for z in zombies:
                z.draw(screen, cam_x, cam_y)
            for axe in axes:
                axe.draw(screen, cam_x, cam_y)
            player.draw(screen, cam_x, cam_y)

            hud_z = font_small.render(f"Zombies Left: {len(zombies)} | Score: {score}", True, YELLOW)
            hud_hp = font_small.render(f"HP: {player_hp}/{max_player_hp}", True, CYAN)
            hud_time = font_small.render(f"Zone Time: {int(game_time//60):02d}:{int(game_time%60):02d}", True, RED)
            hud_dmg = font_small.render(f"Gun Damage: {gun_damage} (Press U to Upgrade)", True, WHITE)
            
            screen.blit(hud_z, (20, 20))
            screen.blit(hud_hp, (20, 50))
            screen.blit(hud_time, (WIDTH - 200, 20))
            screen.blit(hud_dmg, (20, 80))

        elif game_state == 3:
            screen.fill(BLACK)
            over_txt = font_large.render("YOU DIED! ZOMBIES KILLED YOU.", True, RED)
            screen.blit(over_txt, (WIDTH//2 - over_txt.get_width()//2, HEIGHT//2 - 50))
            click_txt = font_med.render("Click anywhere to return to Main Menu", True, WHITE)
            screen.blit(click_txt, (WIDTH//2 - click_txt.get_width()//2, HEIGHT//2 + 20))

        elif game_state == 4:
            screen.fill(BLACK)
            win_txt = font_large.render("VICTORY! ALL ZOMBIES ELIMINATED.", True, GREEN)
            screen.blit(win_txt, (WIDTH//2 - win_txt.get_width()//2, HEIGHT//2 - 50))
            click_txt = font_med.render("Click anywhere to return to Main Menu", True, WHITE)
            screen.blit(click_txt, (WIDTH//2 - click_txt.get_width()//2, HEIGHT//2 + 20))

        pygame.display.flip()

if __name__ == "__main__":
    run_game()

