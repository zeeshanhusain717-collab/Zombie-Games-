import pygame
import random
import math

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Z - Mobile Survival Edition")
clock = pygame.time.Clock()

# Colors (Mobile Optimized Tactical Theme)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 80, 0)
RED = (210, 50, 50)
ORANGE = (235, 130, 20)
BLUE = (40, 90, 220)
YELLOW = (240, 220, 50)
CYAN = (0, 210, 210)
BROWN = (130, 65, 20)
GRAY = (110, 110, 110)
DARK_GRAY = (25, 25, 30)
GOLD = (255, 215, 0)
PURPLE = (140, 50, 180)
PINK = (255, 105, 180)

# Safe Fonts
font_small = pygame.font.Font(None, 24)
font_med = pygame.font.Font(None, 30)
font_large = pygame.font.Font(None, 44)

# Game States: 
# 0: Menu, 1: Base Camp Hub, 2: Loadout/Shop/Select, 3: Gameplay, 4: Game Over, 5: Victory
game_state = 0

# --- Persistent RPG, Economy & Tactical Loadout System ---
player_coins = 1000
current_day = 1
max_days = 60
cycle_count = 1
daily_target_zombies = 15
zombies_killed_today = 0
mission_claimed = False

# Characters: Nova (Lady - Speed), Alpha (Gent 1 - Tank/HP), Viper (Gent 2 - Damage)
selected_character = "Nova"
char_levels = {"Nova": 1, "Alpha": 1, "Viper": 1}

# Armor Jacket (Level 1 to 10)
armor_level = 1

# 6 Guns (3 Close-range, 3 Long-range)
guns_data = [
    {"name": "Combat Pistol", "type": "Close", "base_dmg": 25, "range": 300},
    {"name": "Tactical SMG", "type": "Close", "base_dmg": 40, "range": 350},
    {"name": "Assault Shotgun", "type": "Close", "base_dmg": 65, "range": 280},
    {"name": "Scout Rifle", "type": "Long", "base_dmg": 50, "range": 550},
    {"name": "Marksman DMR", "type": "Long", "base_dmg": 85, "range": 650},
    {"name": "Sniper Elite", "type": "Long", "base_dmg": 120, "range": 800}
]
gun_levels = {g["name"]: 1 for g in guns_data}
equipped_guns = [0, 3] # Player takes 2 guns into battle

selected_map = "Jungle"
unlocked_maps = ["Jungle"]

base_player_hp = 200
player_hp = 200
armor_shield = 50
score = 0
game_time = 600.0
status_msg = ""

# Entities
player = None
zombies = []
axes = []
loots = []
popups = []

# Mobile Virtual Joystick & Touch UI Rects
joy_base = (160, HEIGHT - 160)
joy_radius = 75
joy_knob = [160, HEIGHT - 160]
joy_active = False

fire_btn_rect = pygame.Rect(WIDTH - 210, HEIGHT - 210, 130, 130)
upgrade_btn_rect = pygame.Rect(WIDTH - 210, HEIGHT - 310, 130, 70)
dash_btn_rect = pygame.Rect(WIDTH - 360, HEIGHT - 210, 120, 120)

class DamagePopup:
    def __init__(self, x, y, text, color=ORANGE):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.timer = 30

    def update(self):
        self.y -= 1.5
        self.timer -= 1

    def draw(self, surface, cam_x, cam_y):
        txt = font_small.render(self.text, True, self.color)
        surface.blit(txt, (int(self.x - cam_x), int(self.y - cam_y)))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        c_lvl = char_levels[selected_character]
        if selected_character == "Nova":
            self.base_speed = 6.0 + (c_lvl * 0.4)
        elif selected_character == "Alpha":
            self.base_speed = 4.5 + (c_lvl * 0.2)
        else:
            self.base_speed = 5.2 + (c_lvl * 0.3)
        
        self.speed = self.base_speed
        self.radius = 22
        self.angle = 0
        self.dash_cooldown = 0

    def dash(self):
        if selected_character == "Nova" and self.dash_cooldown <= 0:
            self.speed = 14.0
            self.dash_cooldown = 120  # Syntax error free
            popups.append(DamagePopup(self.x, self.y - 30, "SPEED DASH!", CYAN))

    def move(self, dx, dy):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
            if self.dash_cooldown == 90:
                self.speed = self.base_speed

        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = max(50, min(2950, self.x))
        self.y = max(50, min(2950, self.y))
        if dx != 0 or dy != 0:
            self.angle = math.atan2(dy, dx)

    def draw(self, surface, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        body_col = PINK if selected_character == "Nova" else (BLUE if selected_character == "Alpha" else GOLD)
        pygame.draw.circle(surface, body_col, (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(sx), int(sy)), self.radius, 2)
        hx = sx + math.cos(self.angle) * 28
        hy = sy + math.sin(self.angle) * 28
        pygame.draw.line(surface, BLACK, (sx, sy), (hx, hy), 7)

class Zombie:
    def __init__(self, x, y, z_class):
        self.x = x
        self.y = y
        self.z_class = z_class  # 1 to 6 (10 to 60 damage)
        damage_map = {1: 10, 2: 20, 3: 30, 4: 40, 5: 50, 6: 60}
        self.damage = damage_map[z_class]
        
        hp_multiplier = 1.0 + (cycle_count - 1) * 0.3
        self.hp = int((150 * z_class) * hp_multiplier)
        self.max_hp = self.hp
        self.speed = max(1.2, 3.0 - (z_class * 0.25)) * (1.0 + (cycle_count - 1) * 0.1)
        self.radius = 18 + (z_class * 2)
        self.attack_cooldown = random.randint(0, 40)

    def update(self, player_x, player_y):
        dist = math.hypot(player_x - self.x, player_y - self.y)
        if dist > 22:
            angle = math.atan2(player_y - self.y, player_x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

        if dist <= 350:
            self.attack_cooldown += 1
            if self.attack_cooldown >= max(35, 100 - (self.z_class * 8)):
                self.attack_cooldown = 0
                axes.append(ThrowingAxe(self.x, self.y, player_x, player_y, self.damage))

    def draw(self, surface, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if -50 <= sx <= WIDTH + 50 and -50 <= sy <= HEIGHT + 50:
            colors = {1: (100, 180, 100), 2: (60, 140, 60), 3: (40, 100, 40), 
                      4: (180, 100, 40), 5: (180, 50, 50), 6: (120, 20, 120)}
            z_col = colors.get(self.z_class, GREEN)
            pygame.draw.circle(surface, z_col, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(surface, BLACK, (int(sx), int(sy)), self.radius, 2)

            bar_w = 40
            bar_h = 5
            fill = max(0, (self.hp / self.max_hp) * bar_w)
            pygame.draw.rect(surface, RED, (sx - bar_w / 2, sy - self.radius - 12, bar_w, bar_h))
            pygame.draw.rect(surface, YELLOW, (sx - bar_w / 2, sy - self.radius - 12, fill, bar_h))

class ThrowingAxe:
    def __init__(self, x, y, tx, ty, damage):
        self.x = x
        self.y = y
        self.damage = damage
        angle = math.atan2(ty - y, tx - x)
        self.vx = math.cos(angle) * 7.5
        self.vy = math.sin(angle) * 7.5
        self.active = True

    def update(self, player_x, player_y):
        global player_hp, armor_shield
        self.x += self.vx
        self.y += self.vy
        if math.hypot(player_x - self.x, player_y - self.y) < 22:
            incoming = self.damage
            if selected_character == "Alpha":
                incoming = int(incoming * 0.8)
            
            if armor_shield > 0:
                if armor_shield >= incoming:
                    armor_shield -= incoming
                    incoming = 0
                else:
                    incoming -= armor_shield
                    armor_shield = 0
            
            if incoming > 0:
                player_hp -= incoming
            
            popups.append(DamagePopup(player_x, player_y - 20, f"-{self.damage}", RED))
            self.active = False
        elif not (0 <= self.x <= 3000 and 0 <= self.y <= 3000):
            self.active = False

    def draw(self, surface, cam_x, cam_y):
        pygame.draw.circle(surface, BROWN, (int(self.x - cam_x), int(self.y - cam_y)), 7)

class Loot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        pygame.draw.rect(surface, WHITE, (sx - 10, sy - 10, 20, 20))
        pygame.draw.rect(surface, RED, (sx - 2, sy - 8, 4, 16))
        pygame.draw.rect(surface, RED, (sx - 8, sy - 2, 16, 4))

def shoot_nearest_zombie():
    global score, game_state, player_coins, zombies_killed_today
    if not zombies or not player:
        return
    nearest = None
    min_dist = 600
    
    total_gun_dmg = 0
    for g_idx in equipped_guns:
        g = guns_data[g_idx]
        lvl = gun_levels[g["name"]]
        total_gun_dmg += g["base_dmg"] * (1 + (lvl - 1) * 0.5)
    
    if selected_character == "Viper":
        total_gun_dmg = int(total_gun_dmg * 1.3)

    for z in zombies:
        d = math.hypot(z.x - player.x, z.y - player.y)
        if d < min_dist:
            min_dist = d
            nearest = z

    if nearest:
        player.angle = math.atan2(nearest.y - player.y, nearest.x - player.x)
        nearest.hp -= int(total_gun_dmg)
        popups.append(DamagePopup(nearest.x, nearest.y - 25, f"-{int(total_gun_dmg)}"))
        if nearest.hp <= 0:
            zombies.remove(nearest)
            score += 50
            player_coins += 20
            zombies_killed_today += 1
            if len(zombies) == 0:
                game_state = 5

def start_game():
    global player, zombies, loots, axes, popups, game_state, player_hp, max_player_hp, score, game_time, armor_shield
    game_state = 3
    
    c_lvl = char_levels[selected_character]
    max_player_hp = 200 + (c_lvl * 25) if selected_character != "Alpha" else 300 + (c_lvl * 40)
    player_hp = max_player_hp
    armor_shield = armor_level * 50
    score = 0
    game_time = 600.0

    player = Player(1500, 1500)
    zombies.clear()
    axes.clear()
    loots.clear()
    popups.clear()

    zombie_count = 60 + (current_day * 3)
    for i in range(zombie_count):
        z_class = random.choices([1, 2, 3, 4, 5, 6], weights=[35, 25, 20, 10, 7, 3])[0]
        zx = random.randint(200, 2800)
        zy = random.randint(200, 2800)
        if math.hypot(zx - 1500, zy - 1500) < 250:
            zx += 350
        zombies.append(Zombie(zx, zy, z_class))

    for _ in range(25):
        loots.append(Loot(random.randint(200, 2800), random.randint(200, 2800)))

def run_game():
    global game_state, player_hp, score, game_time, selected_character, status_msg
    global player_coins, current_day, max_days, cycle_count, zombies_killed_today, mission_claimed
    global unlocked_maps, selected_map, joy_active, joy_knob, armor_level, armor_shield, equipped_guns
    running = True

    camp_start_btn = pygame.Rect(WIDTH // 2 - 220, HEIGHT - 130, 440, 65)
    claim_btn_rect = pygame.Rect(WIDTH // 2 - 220, HEIGHT - 210, 440, 50)
    
    jungle_rect = pygame.Rect(50, 160, 300, 50)
    frozen_rect = pygame.Rect(50, 220, 300, 50)
    metro_rect = pygame.Rect(50, 280, 300, 50)

    nova_rect = pygame.Rect(WIDTH - 380, 160, 330, 45)
    alpha_rect = pygame.Rect(WIDTH - 380, 215, 330, 45)
    viper_rect = pygame.Rect(WIDTH - 380, 270, 330, 45)
    start_battle_btn = pygame.Rect(WIDTH // 2 - 200, 540, 400, 70)

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if game_state == 0:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if WIDTH // 2 - 160 <= mx <= WIDTH // 2 + 160:
                        if 310 <= my <= 390:
                            game_state = 1
                        elif 430 <= my <= 510:
                            pygame.quit()
                            return

            elif game_state == 1:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if camp_start_btn.collidepoint(mx, my):
                        game_state = 2
                    elif claim_btn_rect.collidepoint(mx, my):
                        if not mission_claimed and zombies_killed_today >= daily_target_zombies:
                            player_coins += 350
                            mission_claimed = True
                            status_msg = "Mission Reward Claimed (+350 🪙)!"
                    elif pygame.Rect(50, 200, 340, 50).collidepoint(mx, my):
                        cost = armor_level * 100
                        if armor_level < 10 and player_coins >= cost:
                            player_coins -= cost
                            armor_level += 1
                            armor_shield = armor_level * 50
                            status_msg = f"Armor upgraded to Level {armor_level}!"
                    elif pygame.Rect(50, 260, 340, 50).collidepoint(mx, my):
                        c_lvl = char_levels[selected_character]
                        cost = c_lvl * 150
                        if c_lvl < 10 and player_coins >= cost:
                            player_coins -= cost
                            char_levels[selected_character] += 1
                            status_msg = f"{selected_character} upgraded to Level {char_levels[selected_character]}!"
                    elif pygame.Rect(50, 320, 340, 50).collidepoint(mx, my):
                        g_name = guns_data[equipped_guns[0]]["name"]
                        g_lvl = gun_levels[g_name]
                        cost = g_lvl * 120
                        if g_lvl < 10 and player_coins >= cost:
                            player_coins -= cost
                            gun_levels[g_name] += 1
                            status_msg = f"{g_name} upgraded to Level {gun_levels[g_name]}!"

            elif game_state == 2:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if jungle_rect.collidepoint(mx, my):
                        selected_map = "Jungle"
                    elif frozen_rect.collidepoint(mx, my):
                        if "Frozen Wasteland" in unlocked_maps:
                            selected_map = "Frozen Wasteland"
                        else:
                            status_msg = "Locked! Reach Day 10."
                    elif metro_rect.collidepoint(mx, my):
                        if "Ruined Metropolis" in unlocked_maps:
                            selected_map = "Ruined Metropolis"
                        else:
                            status_msg = "Locked! Reach Day 25."
                    elif nova_rect.collidepoint(mx, my):
                        selected_character = "Nova"
                    elif alpha_rect.collidepoint(mx, my):
                        selected_character = "Alpha"
                    elif viper_rect.collidepoint(mx, my):
                        selected_character = "Viper"
                    elif pygame.Rect(WIDTH - 380, 370, 160, 40).collidepoint(mx, my):
                        equipped_guns[0] = (equipped_guns[0] + 1) % len(guns_data)
                    elif pygame.Rect(WIDTH - 200, 370, 160, 40).collidepoint(mx, my):
                        equipped_guns[1] = (equipped_guns[1] + 1) % len(guns_data)
                    elif start_battle_btn.collidepoint(mx, my):
                        start_game()

            elif game_state == 3:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if math.hypot(mx - joy_base[0], my - joy_base[1]) <= joy_radius + 40:
                        joy_active = True
                    elif fire_btn_rect.collidepoint(mx, my):
                        shoot_nearest_zombie()
                    elif dash_btn_rect.collidepoint(mx, my):
                        if player:
                            player.dash()
                    elif upgrade_btn_rect.collidepoint(mx, my):
                        if score >= 100 and player_coins >= 50:
                            score -= 100
                            player_coins -= 50
                            popups.append(DamagePopup(player.x, player.y - 35, "FIELD BOOST!", GOLD))
                    else:
                        cam_x = player.x - WIDTH // 2
                        cam_y = player.y - HEIGHT // 2
                        twx, twy = mx + cam_x, my + cam_y
                        for z in zombies[:]:
                            if math.hypot(z.x - twx, z.y - twy) < z.radius + 25:
                                player.angle = math.atan2(z.y - player.y, z.x - player.x)
                                shoot_nearest_zombie()
                                break

                elif event.type == pygame.MOUSEMOTION and joy_active:
                    mx, my = event.pos
                    dx, dy = mx - joy_base[0], my - joy_base[1]
                    dist = math.hypot(dx, dy)
                    if dist > joy_radius:
                        dx = (dx / dist) * joy_radius
                        dy = (dy / dist) * joy_radius
                    joy_knob = [joy_base[0] + dx, joy_base[1] + dy]

                elif event.type == pygame.MOUSEBUTTONUP:
                    joy_active = False
                    joy_knob = [joy_base[0], joy_base[1]]

            elif game_state in [4, 5]:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if game_state == 5:
                        current_day += 1
                        zombies_killed_today = 0
                        mission_claimed = False
                        if current_day >= 10 and "Frozen Wasteland" not in unlocked_maps:
                            unlocked_maps.append("Frozen Wasteland")
                        if current_day >= 25 and "Ruined Metropolis" not in unlocked_maps:
                            unlocked_maps.append("Ruined Metropolis")

                        if current_day > max_days:
                            current_day = 1
                            cycle_count += 1
                    game_state = 1

        # --- RENDERING ---
        if game_state == 0:
            screen.fill(DARK_GRAY)
            title = font_large.render("ZOMBIE Z: BATTLEGROUND ELITE", True, ORANGE)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 160))

            pygame.draw.rect(screen, RED, (WIDTH // 2 - 160, 310, 320, 80), border_radius=12)
            screen.blit(font_med.render("PLAY GAME", True, WHITE), (WIDTH // 2 - 80, 335))

            pygame.draw.rect(screen, GRAY, (WIDTH // 2 - 160, 430, 320, 80), border_radius=12)
            screen.blit(font_med.render("EXIT", True, WHITE), (WIDTH // 2 - 35, 455))

        elif game_state == 1:
            screen.fill(DARK_GRAY)
            title = font_large.render(f"CYCLE {cycle_count} | DAY {current_day} / {max_days}", True, GOLD)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

            quotes = [
                "Diary: 'The fog whispers of an endless war. Stay armed.'",
                "Diary: 'Armor saves flesh, but discipline saves the soul.'",
                "Diary: '6 guns, 3 survivors, and millions of the dead.'"
            ]
            q_txt = font_small.render(quotes[(current_day - 1) % len(quotes)], True, CYAN)
            screen.blit(q_txt, (WIDTH // 2 - q_txt.get_width() // 2, 70))

            coins_txt = font_med.render(f"Coins: {player_coins} 🪙", True, YELLOW)
            screen.blit(coins_txt, (50, 110))

            shop_title = font_med.render("ARMORY & GEAR UPGRADES (Lv 1-10)", True, CYAN)
            screen.blit(shop_title, (50, 160))

            armor_colors = {1: GRAY, 2: GREEN, 3: BLUE, 4: CYAN, 5: PURPLE, 6: ORANGE, 7: GOLD, 8: RED, 9: PINK, 10: WHITE}
            j_col = armor_colors.get(armor_level, GRAY)
            pygame.draw.rect(screen, j_col, (50, 200, 340, 50), border_radius=10)
            screen.blit(font_small.render(f"Jacket Armor [Lv {armor_level}/10] Cost: {armor_level*100}", True, BLACK if armor_level==10 else WHITE), (65, 215))

            c_lvl = char_levels[selected_character]
            pygame.draw.rect(screen, BLUE, (50, 260, 340, 50), border_radius=10)
            screen.blit(font_small.render(f"{selected_character} [Lv {c_lvl}/10] Cost: {c_lvl*150}", True, WHITE), (65, 275))

            g_name = guns_data[equipped_guns[0]]["name"]
            g_lvl = gun_levels[g_name]
            pygame.draw.rect(screen, BLUE, (50, 320, 340, 50), border_radius=10)
            screen.blit(font_small.render(f"{g_name} [Lv {g_lvl}/10] Cost: {g_lvl*120}", True, WHITE), (65, 335))

            mission_box = pygame.Rect(WIDTH - 500, 160, 420, 220)
            pygame.draw.rect(screen, (40, 40, 50), mission_box, border_radius=15)
            pygame.draw.rect(screen, ORANGE, mission_box, 2, border_radius=15)
            
            screen.blit(font_med.render("DAILY COMBAT MISSION", True, ORANGE), (mission_box.x + 20, mission_box.y + 15))
            m_desc = font_small.render(f"Eliminate {daily_target_zombies} zombies today.", True, WHITE)
            m_prog = font_small.render(f"Progress: {zombies_killed_today} / {daily_target_zombies}", True, YELLOW)
            screen.blit(m_desc, (mission_box.x + 20, mission_box.y + 60))
            screen.blit(m_prog, (mission_box.x + 20, mission_box.y + 95))

            claim_col = GREEN if (zombies_killed_today >= daily_target_zombies and not mission_claimed) else GRAY
            pygame.draw.rect(screen, claim_col, claim_btn_rect, border_radius=10)
            claim_text = "Claim Reward (+350 🪙)" if not mission_claimed else "Reward Claimed"
            c_txt = font_small.render(claim_text, True, WHITE)
            screen.blit(c_txt, (claim_btn_rect.centerx - c_txt.get_width() // 2, claim_btn_rect.centery - c_txt.get_height() // 2))

            status_txt = font_small.render(status_msg, True, YELLOW)
            screen.blit(status_txt, (WIDTH // 2 - status_txt.get_width() // 2, HEIGHT - 200))

            pygame.draw.rect(screen, RED, camp_start_btn, border_radius=14)
            start_txt = font_large.render("DEPLOY TO BATTLE", True, WHITE)
            screen.blit(start_txt, (camp_start_btn.centerx - start_txt.get_width() // 2, camp_start_btn.centery - start_txt.get_height() // 2))

        elif game_state == 2:
            screen.fill(DARK_GRAY)
            title = font_large.render("LOADOUT & MAP SELECTION", True, YELLOW)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

            pygame.draw.rect(screen, GREEN if selected_map=="Jungle" else GRAY, jungle_rect, border_radius=8)
            screen.blit(font_small.render("Map: Jungle (Unlocked)", True, WHITE), (jungle_rect.x+15, jungle_rect.y+15))

            f_col = GREEN if selected_map=="Frozen Wasteland" else (BLUE if "Frozen Wasteland" in unlocked_maps else DARK_GRAY)
            pygame.draw.rect(screen, f_col, frozen_rect, border_radius=8)
            f_txt = "Frozen Wasteland (Unlocked)" if "Frozen Wasteland" in unlocked_maps else "Frozen (Locked @ Day 10)"
            screen.blit(font_small.render(f_txt, True, WHITE), (frozen_rect.x+15, frozen_rect.y+15))

            m_col = GREEN if selected_map=="Ruined Metropolis" else (PURPLE if "Ruined Metropolis" in unlocked_maps else DARK_GRAY)
            pygame.draw.rect(screen, m_col, metro_rect, border_radius=8)
            m_txt = "Ruined Metropolis (Unlocked)" if "Ruined Metropolis" in unlocked_maps else "Metropolis (Locked @ Day 25)"
            screen.blit(font_small.render(m_txt, True, WHITE), (metro_rect.x+15, metro_rect.y+15))

            pygame.draw.rect(screen, PINK if selected_character=="Nova" else GRAY, nova_rect, border_radius=8)
            screen.blit(font_small.render("Nova (Lady) - Super Speed Dash", True, WHITE), (nova_rect.x+15, nova_rect.y+12))

            pygame.draw.rect(screen, BLUE if selected_character=="Alpha" else GRAY, alpha_rect, border_radius=8)
            screen.blit(font_small.render("Alpha (Gent 1) - High HP & Tank", True, WHITE), (alpha_rect.x+15, alpha_rect.y+12))

            pygame.draw.rect(screen, GOLD if selected_character=="Viper" else GRAY, viper_rect, border_radius=8)
            screen.blit(font_small.render("Viper (Gent 2) - Deadly Gun Dmg", True, WHITE), (viper_rect.x+15, viper_rect.y+12))

            gun_loadout_title = font_med.render("DUAL GUN LOADOUT (Pick 2)", True, CYAN)
            screen.blit(gun_loadout_title, (WIDTH - 380, 330))

            pygame.draw.rect(screen, ORANGE, (WIDTH - 380, 370, 160, 40), border_radius=6)
            screen.blit(font_small.render(guns_data[equipped_guns[0]]["name"], True, WHITE), (WIDTH - 370, 380))

            pygame.draw.rect(screen, ORANGE, (WIDTH - 200, 370, 160, 40), border_radius=6)
            screen.blit(font_small.render(guns_data[equipped_guns[1]]["name"], True, WHITE), (WIDTH - 190, 380))

            st = font_med.render(status_msg, True, YELLOW)
            screen.blit(st, (WIDTH // 2 - st.get_width() // 2, 470))

            pygame.draw.rect(screen, RED, start_battle_btn, border_radius=14)
            b_txt = font_large.render("ENTER COMBAT", True, WHITE)
            screen.blit(b_txt, (start_battle_btn.centerx - b_txt.get_width() // 2, start_battle_btn.centery - b_txt.get_height() // 2))

        elif game_state == 3:
            game_time -= dt
            if game_time <= 0 or player_hp <= 0:
                game_state = 4

            dx, dy = 0, 0
            if joy_active:
                dx = (joy_knob[0] - joy_base[0]) / joy_radius
                dy = (joy_knob[1] - joy_base[1]) / joy_radius
            else:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_w]: dy -= 1
                if keys[pygame.K_s]: dy += 1
                if keys[pygame.K_a]: dx -= 1
                if keys[pygame.K_d]: dx += 1

            player.move(dx, dy)

            cam_x = player.x - WIDTH // 2
            cam_y = player.y - HEIGHT // 2

            for z in zombies:
                z.update(player.x, player.y)

            for axe in axes[:]:
                axe.update(player.x, player.y)
                if not axe.active:
                    axes.remove(axe)

            for loot in loots[:]:
                if math.hypot(player.x - loot.x, player.y - loot.y) < 30:
                    player_hp = min(player_hp + 50, max_player_hp)
                    popups.append(DamagePopup(player.x, player.y - 25, "+50 HP", GREEN))
                    loots.remove(loot)

            for p in popups[:]:
                p.update()
                if p.timer <= 0:
                    popups.remove(p)

            if selected_map == "Jungle":
                screen.fill((45, 130, 45))
                pygame.draw.rect(screen, BLUE, (-cam_x + 1350, -cam_y, 180, 3000))
            elif selected_map == "Frozen Wasteland":
                screen.fill((160, 180, 200))
                pygame.draw.rect(screen, (120, 150, 180), (-cam_x + 1200, -cam_y, 300, 3000))
            else:
                screen.fill((60, 60, 70))
                pygame.draw.rect(screen, (30, 30, 35), (-cam_x + 1000, -cam_y, 400, 3000))

            pygame.draw.rect(screen, RED, (-cam_x, -cam_y, 3000, 3000), 8)

            for loot in loots:
                loot.draw(screen, cam_x, cam_y)
            for z in zombies:
                z.draw(screen, cam_x, cam_y)
            for axe in axes:
                axe.draw(screen, cam_x, cam_y)
            player.draw(screen, cam_x, cam_y)
            for p in popups:
                p.draw(screen, cam_x, cam_y)

            pygame.draw.circle(screen, (255, 255, 255), joy_base, joy_radius, 3)
            pygame.draw.circle(screen, CYAN, (int(joy_knob[0]), int(joy_knob[1])), 30)

            pygame.draw.rect(screen, RED, fire_btn_rect, border_radius=65)
            pygame.draw.rect(screen, WHITE, fire_btn_rect, 3, border_radius=65)
            f_txt = font_med.render("FIRE", True, WHITE)
            screen.blit(f_txt, (fire_btn_rect.centerx - f_txt.get_width() // 2, fire_btn_rect.centery - f_txt.get_height() // 2))

            if selected_character == "Nova":
                pygame.draw.rect(screen, CYAN, dash_btn_rect, border_radius=60)
                pygame.draw.rect(screen, WHITE, dash_btn_rect, 3, border_radius=60)
                d_txt = font_small.render("DASH", True, BLACK)
                screen.blit(d_txt, (dash_btn_rect.centerx - d_txt.get_width() // 2, dash_btn_rect.centery - d_txt.get_height() // 2))

            upg_col = ORANGE if (score >= 100 and player_coins >= 50) else GRAY
            pygame.draw.rect(screen, upg_col, upgrade_btn_rect, border_radius=10)
            u_txt = font_small.render("UPGRADE", True, WHITE)
            screen.blit(u_txt, (upgrade_btn_rect.centerx - u_txt.get_width() // 2, upgrade_btn_rect.centery - u_txt.get_height() // 2))

            hud_z = font_small.render(f"Zombies: {len(zombies)} | Coins: {player_coins}🪙", True, YELLOW)
            hud_hp = font_small.render(f"HP: {player_hp}/{max_player_hp} | Shield: {armor_shield}", True, CYAN)
            hud_time = font_small.render(f"Zone: {int(game_time // 60):02d}:{int(game_time % 60):02d}", True, WHITE)
            hud_dmg = font_small.render(f"Day {current_day} | Armor Lv {armor_level}", True, WHITE)

            screen.blit(hud_z, (20, 20))
            screen.blit(hud_hp, (20, 50))
            screen.blit(hud_time, (WIDTH - 180, 20))
            screen.blit(hud_dmg, (20, 80))

        elif game_state == 4:
            screen.fill(BLACK)
            over_txt = font_large.render("THE FOG CONSUMED YOU...", True, RED)
            screen.blit(over_txt, (WIDTH // 2 - over_txt.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(font_med.render("Tap anywhere to return to Base Camp", True, WHITE), (WIDTH // 2 - 200, HEIGHT // 2 + 30))

        elif game_state == 5:
            screen.fill(BLACK)
            win_txt = font_large.render(f"CYCLE {cycle_count} - DAY {current_day} SURVIVED", True, GREEN)
            screen.blit(win_txt, (WIDTH // 2 - win_txt.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(font_med.render("Tap to return to Base Camp diary", True, WHITE), (WIDTH // 2 - 180, HEIGHT // 2 + 30))

        pygame.display.flip()

if __name__ == "__main__":
    run_game()

