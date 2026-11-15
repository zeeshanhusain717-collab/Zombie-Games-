from ursina import *
import random

app = Ursina()

# --- Game States ---
# 0: Main Menu, 1: Map/Character Select, 2: Gameplay, 3: Game Over, 4: Win
game_state = 0

# --- Global Variables ---
selected_map = "Jungle"
selected_character = "Commando"
player_hp = 200
max_player_hp = 200
gun_damage = 50
score = 0
game_time = 600  # 10 minutes

# UI entities list
menu_entities = []
game_entities = []

window.title = "FREE FIRE: ZOMBIE SURVIVAL 3D"
window.borderless = False
window.fullscreen = False
window.exit_button.enabled = False
window.fps_counter.enabled = True

# ==========================================================
# 1. Menu System
# ==========================================================

def clear_menu():
    for e in menu_entities:
        destroy(e)
    menu_entities.clear()

def create_main_menu():
    global game_state
    game_state = 0
    clear_menu()
    
    # Background UI Panel
    menu_entities.append(Entity(model='quad', scale=(20, 20), color=color.dark_gray, z=1))
    
    # Title & Subtitle
    menu_entities.append(Text('FREE FIRE: ZOMBIE SURVIVAL', origin=(0,0), y=0.35, scale=2, color=color.orange))
    menu_entities.append(Text('Third-Person Mobile Edition', origin=(0,0), y=0.28, scale=1, color=color.light_gray))
    
    # Play Buttons
    def start_selection():
        create_selection_menu()
        
    menu_entities.append(Button(text='PLAY GAME', color=color.red, scale=(0.3, 0.1), y=0.05, on_click=start_selection))
    menu_entities.append(Button(text='EXIT', color=color.gray, scale=(0.3, 0.1), y=-0.1, on_click=application.quit))

def create_selection_menu():
    global game_state, selected_map, selected_character
    game_state = 1
    clear_menu()
    
    menu_entities.append(Entity(model='quad', scale=(20, 20), color=color.black33, z=1))
    menu_entities.append(Text('MAP & CHARACTER SELECTION', origin=(0,0), y=0.4, scale=1.5, color=color.yellow))
    
    # Map Selection
    menu_entities.append(Text('Select Map:', origin=(0,0), x=-0.3, y=0.2, scale=1.2))
    
    def set_map_jungle():
        global selected_map
        selected_map = "Jungle"
        map_status_text.text = "Map: Jungle (Unlocked)"
        map_status_text.color = color.green
        
    def set_map_ice():
        map_status_text.text = "Map: Ice/Water (LOCKED! Unlock at Level 5)"
        map_status_text.color = color.red
        
    def set_map_desert():
        map_status_text.text = "Map: Desert (LOCKED! Unlock at Level 10)"
        map_status_text.color = color.red

    menu_entities.append(Button(text='Jungle (Unlocked)', color=color.dark_green, scale=(0.25, 0.08), x=-0.3, y=0.1, on_click=set_map_jungle))
    menu_entities.append(Button(text='Ice/Water (Locked)', color=color.dark_gray, scale=(0.25, 0.08), x=-0.3, y=0.0, on_click=set_map_ice))
    menu_entities.append(Button(text='Desert (Locked)', color=color.dark_gray, scale=(0.25, 0.08), x=-0.3, y=-0.1, on_click=set_map_desert))
    
    map_status_text = Text('Map: Jungle (Unlocked)', origin=(0,0), x=-0.3, y=-0.22, scale=1, color=color.green)
    menu_entities.append(map_status_text)
    
    # Character Selection
    menu_entities.append(Text('Select Character:', origin=(0,0), x=0.3, y=0.2, scale=1.2))
    
    def set_char_commando():
        global selected_character
        selected_character = "Commando"
        char_status.text = "Character: Commando (HP 200, Fast)"
        
    def set_char_tank():
        global selected_character
        selected_character = "Tank"
        char_status.text = "Character: Tank (HP 300, Heavy)"

    menu_entities.append(Button(text='Commando', color=color.azure, scale=(0.25, 0.08), x=0.3, y=0.1, on_click=set_char_commando))
    menu_entities.append(Button(text='Tank Hero', color=color.blue, scale=(0.25, 0.08), x=0.3, y=0.0, on_click=set_char_tank))
    
    char_status = Text('Character: Commando', origin=(0,0), x=0.3, y=-0.1, scale=1, color=color.cyan)
    menu_entities.append(char_status)
    
    # Start Button
    def launch_game():
        start_game_world()
        
    menu_entities.append(Button(text='START BATTLE', color=color.orange, scale=(0.4, 0.1), y=-0.35, on_click=launch_game))
    menu_entities.append(Button(text='BACK', color=color.gray, scale=(0.2, 0.06), y=-0.45, on_click=create_main_menu))


# ==========================================================
# 2. Gameplay World (Third-Person Free Fire Style)
# ==========================================================

player = None
zombies = []
hud_text = None
zone_timer_text = None
hp_text = None
damage_text = None

class DamagePopup(Entity):
    def __init__(self, text, pos):
        super().__init__()
        self.text = Text(text=text, position=pos, scale=1, color=color.orange, origin=(0,0))
        self.duration = 0.6
        
    def update(self):
        self.duration -= time.dt
        self.text.y += time.dt * 0.5
        if self.duration <= 0:
            destroy(self.text)
            destroy(self)

class PlayerCharacter(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        # करैक्टर बॉडी (Free Fire स्टाइल विज़िबल हीरो)
        self.model = 'cube'
        self.color = color.cyan
        self.scale = (1, 2, 1)
        self.origin_y = -0.5
        
        # छोटा गन मॉडल जो करैक्टर के हाथ में दिखेगा
        self.gun = Entity(model='cube', color=color.black, scale=(0.2, 0.2, 0.8), position=(0.5, 0.5, 0.5), parent=self)
        
        # Third-Person Camera (करैक्टर के पीछे और ऊपर सेट किया गया है)
        camera.parent = None
        camera.position = (0, 4, -8)
        
        self.speed = 10
        
    def update(self):
        global game_state
        if game_state != 2:
            return
            
        # Movement (WASD / Mobile directions)
        move_dir = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s']
        ).normalized()
        
        if move_dir.length() > 0:
            self.position += move_dir * self.speed * time.dt
            # करैक्टर को चलने की दिशा में घुमाना
            target_rotation = camera.rotation_y + atan2(move_dir.x, move_dir.z) * (180 / 3.14159)
            self.rotation_y = target_rotation
            
        # Third-Person Camera follows the player smoothly
        camera.position = self.position + Vec3(0, 3, -6)
        camera.rotation = (15, self.rotation_y, 0)
        
        # Mouse look for camera angle rotation
        if mouse.left:
            self.rotation_y += mouse.velocity[0] * 50

class Zombie(Entity):
    def __init__(self, z_type, pos):
        super().__init__()
        self.z_type = z_type  # "normal" (HP 200) or "heavy" (HP 500)
        self.model = 'cube'
        self.position = pos
        self.scale = (1, 2, 1) if z_type == "normal" else (1.4, 2.5, 1.4)
        self.color = color.green if z_type == "normal" else color.dark_green
        self.hp = 200 if z_type == "normal" else 500
        self.max_hp = self.hp
        self.attack_cooldown = 0
        
        # ज़ॉम्बी के ऊपर उसकी HP दिखने वाला टेक्स्ट बार
        self.hp_bar = Text(text=f'HP: {self.hp}/{self.max_hp}', scale=0.8, origin=(0,0), color=color.red)
        
    def update(self):
        global game_state, player_hp
        if game_state != 2 or not player:
            if self.hp_bar:
                destroy(self.hp_bar)
            return
            
        # ज़ॉम्बी की HP बार की पोजीशन स्क्रीन पर अपडेट करना
        screen_pos = camera.world_to_screen(self.position + Vec3(0, 1.8, 0))
        self.hp_bar.position = screen_pos
        self.hp_bar.text = f'HP: {self.hp}'
        
        dist = distance(self.position, player.position)
        
        # ज़ॉम्बी का प्लेयर की तरफ बढ़ना
        if dist > 2.5:
            self.look_at(player.position)
            self.rotation_x = 0
            self.rotation_z = 0
            self.direction = self.forward
            self.position += self.direction * 3 * time.dt
            
        # 100 मीटर की रेंज में कुल्हाड़ी फेंकना
        if dist <= 100:
            self.attack_cooldown += time.dt
            if self.attack_cooldown >= 3.0: 
                self.attack_cooldown = 0
                ThrowingAxe(self.position + Vec3(0,1,0), player.position)

    def on_destroy(self):
        if self.hp_bar:
            destroy(self.hp_bar)

class ThrowingAxe(Entity):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.model = 'cube'
        self.color = color.brown
        self.scale = (0.3, 0.8, 0.2)
        self.position = start_pos
        self.speed = 15
        
    def update(self):
        global game_state, player_hp
        if game_state != 2 or not player:
            destroy(self)
            return
            
        direction = (player.position - self.position).normalized()
        self.position += direction * self.speed * time.dt
        self.rotation_z += 500 * time.dt
        
        # Hit check with player
        if distance(self.position, player.position) < 1.5:
            player_hp -= 25
            update_hud()
            destroy(self)
            if player_hp <= 0:
                game_over()

# Medkit/HP Loot
class Loot(Entity):
    def __init__(self, pos, l_type):
        super().__init__()
        self.model = 'cube'
        self.position = pos
        self.l_type = l_type  # "medkit"
        self.color = color.green
        self.scale = (0.6, 0.6, 0.6)
        
    def update(self):
        global game_state, player_hp, max_player_hp
        if game_state != 2 or not player:
            return
        
        if distance(self.position, player.position) < 1.5:
            player_hp = min(player_hp + 50, max_player_hp)
            update_hud()
            destroy(self)

def start_game_world():
    global game_state, player, zombies, hud_text, zone_timer_text, hp_text, damage_text, game_time, player_hp, max_player_hp, score
    game_state = 2
    clear_menu()
    
    game_time = 600
    max_player_hp = 200 if selected_character == "Commando" else 300
    player_hp = max_player_hp
    score = 0
    
    # 1000m स्केल का ऑप्टिमाइज़्ड जंगल नक्शा (नदी और पेड़)
    ground = Entity(model='plane', scale=(500, 1, 500), color=color.rgb(34, 139, 34), texture='white_cube')
    game_entities.append(ground)
    
    # नदी (Water strip in jungle)
    river = Entity(model='quad', scale=(400, 20), color=color.blue, rotation_x=90, position=(0, 0.1, 0))
    game_entities.append(river)
    
    # पेड़ और हरियाली
    for _ in range(40):
        rx = random.uniform(-200, 200)
        rz = random.uniform(-200, 200)
        if abs(rx) < 20: continue # नदी के पास खाली जगह
        tree = Entity(model='cube', color=color.brown, scale=(2, 8, 2), position=(rx, 4, rz))
        leaves = Entity(model='sphere', color=color.dark_green, scale=(6, 6, 6), position=(rx, 8, rz))
        game_entities.append(tree)
        game_entities.append(leaves)

    # घरों में केवल मेडकिट / HP लूट (No gun loot)
    for _ in range(25):
        rx = random.uniform(-180, 180)
        rz = random.uniform(-180, 180)
        loot_box = Loot((rx, 1, rz), l_type="medkit")
        game_entities.append(loot_box)

    # Player Spawn
    player = PlayerCharacter(position=(0, 1, -20))
    game_entities.append(player)
    
    # Zombies Spawn (कुल 100 ज़ॉम्बी: 50 नॉर्मल [200 HP], 50 भारी [500 HP])
    zombies.clear()
    for i in range(100):
        z_type = "normal" if i < 50 else "heavy"
        pos = Vec3(random.uniform(-150, 150), 1, random.uniform(-150, 150))
        z = Zombie(z_type, pos)
        zombies.append(z)
        game_entities.append(z)

    # HUD (English UI)
    hud_text = Text(text=f'Zombies Left: {len(zombies)} | Score: {score}', position=(-0.85, 0.45), scale=1.2, color=color.yellow)
    zone_timer_text = Text(text=f'Zone Time: 10:00', position=(0.5, 0.45), scale=1.2, color=color.red)
    hp_text = Text(text=f'Player HP: {player_hp}/{max_player_hp}', position=(-0.85, 0.38), scale=1.2, color=color.green)
    damage_text = Text(text=f'Gun Damage: {gun_damage} (Press U to Upgrade)', position=(-0.85, 0.31), scale=1.1, color=color.cyan)
    
    game_entities.extend([hud_text, zone_timer_text, hp_text, damage_text])
    
    # Controls Instruction
    inst = Text(text='[Left Click]: Shoot | [W,A,S,D]: Run & Move | [U]: Upgrade Gun | Gun: PERMANENT AMMO', position=(-0.85, -0.45), scale=0.9, color=color.light_gray)
    game_entities.append(inst)

def update_hud():
    if hud_text and hp_text and damage_text:
        hud_text.text = f'Zombies Left: {len(zombies)} | Score: {score}'
        hp_text.text = f'Player HP: {player_hp}/{max_player_hp}'
        damage_text.text = f'Gun Damage: {gun_damage} (Press U to Upgrade)'

def input(key):
    global game_state, gun_damage, score, player_hp
    if game_state == 2:
        # Gun Upgrade (U की दबाने पर)
        if key == 'u' and score >= 100:
            score -= 100
            gun_damage += 25
            update_hud()
            
        # Shooting Mechanism with Damage Popups
        if key == 'left mouse down':
            hit_info = raycast(camera.world_position, camera.forward, distance=100)
            if hit_info.hit:
                hit_entity = hit_info.entity
                if isinstance(hit_entity, Zombie):
                    hit_entity.hp -= gun_damage
                    hit_entity.color = color.red
                    invoke(setattr, hit_entity, 'color', color.green if hit_entity.z_type == "normal" else color.dark_green, delay=0.1)
                    
                    # स्क्रीन पर डैमेज नंबर दिखाना (जैसे Free Fire में दिखता है)
                    DamagePopup(f'-{gun_damage}', (0, 0))
                    
                    if hit_entity.hp <= 0:
                        destroy(hit_entity)
                        if hit_entity in zombies:
                            zombies.remove(hit_entity)
                        score += 50
                        update_hud()
                        
                        if len(zombies) == 0:
                            game_win()

def game_over():
    global game_state
    game_state = 3
    for e in game_entities:
        destroy(e)
    game_entities.clear()
    
    Text('YOU DIED! ZOMBIES KILLED YOU.', origin=(0,0), y=0.1, scale=2, color=color.red)
    Button(text='Main Menu', color=color.orange, scale=(0.3, 0.1), y=-0.1, on_click=create_main_menu)

def game_win():
    global game_state
    game_state = 4
    for e in game_entities:
        destroy(e)
    game_entities.clear()
    
    Text('VICTORY! ALL ZOMBIES ELIMINATED.', origin=(0,0), y=0.1, scale=2, color=color.green)
    Button(text='Main Menu', color=color.orange, scale=(0.3, 0.1), y=-0.1, on_click=create_main_menu)

# --- Main Game Loop (Timer) ---
def update():
    global game_state, game_time
    if game_state == 2:
        # 10 मिनट का ज़ोन टाइमर
        game_time -= time.dt
        mins = int(game_time // 60)
        secs = int(game_time % 60)
        if zone_timer_text:
            zone_timer_text.text = f'Zone Time: {mins:02d}:{secs:02d}'
            
        if game_time <= 0:
            game_over()

# --- Start Game ---
create_main_menu()

app.run()
