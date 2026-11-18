from PIL import Image, ImageDraw, ImageFont
import os

OUT = "app/src/main/res/drawable"
os.makedirs(OUT, exist_ok=True)

OUTLINE = (10, 10, 10, 255)
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def new_sprite():
    # Kotlin code में sprite को x-32, y-32 पर draw होता है, इसलिए 64x64 ही रखा है
    return Image.new("RGBA", (64, 64), (0, 0, 0, 0))


def ellipse(d, box, fill):
    d.ellipse(box, fill=fill, outline=OUTLINE, width=2)


def rect(d, box, fill):
    d.rectangle(box, fill=fill, outline=OUTLINE, width=2)


# ---------- 1. App Icon (512x512) ----------
icon = Image.new("RGB", (512, 512), (20, 25, 30))
d = ImageDraw.Draw(icon)
d.ellipse([60, 60, 452, 452], fill=(210, 50, 50), outline=(255, 255, 255), width=8)
font = load_font(150)
text = "ZZ"
bbox = d.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((512 - tw) / 2 - bbox[0], (512 - th) / 2 - bbox[1]), text, font=font, fill=(255, 255, 255))
icon.save(f"{OUT}/icon.png")

# ---------- 2. Player (Tactical, cap, vest, rifle) ----------
player = new_sprite()
pd = ImageDraw.Draw(player)
ellipse(pd, [14, 14, 50, 50], (50, 100, 230))          # body
rect(pd, [30, 28, 58, 36], (60, 60, 60))               # rifle barrel
rect(pd, [24, 22, 40, 42], (20, 170, 80))              # tactical vest
ellipse(pd, [22, 8, 42, 28], (220, 180, 140))          # head
rect(pd, [20, 4, 44, 14], (30, 30, 30))                # cap
pd.point([(28, 16), (36, 16)], fill=OUTLINE)           # eyes
player.save(f"{OUT}/player.png")


# ---------- 3. Zombie 1: Walker (green, rags) ----------
z1 = new_sprite()
d1 = ImageDraw.Draw(z1)
ellipse(d1, [12, 12, 52, 52], (40, 140, 40))
rect(d1, [20, 40, 44, 58], (90, 70, 50))               # rags
ellipse(d1, [20, 22, 28, 30], (200, 40, 40))           # left red eye
ellipse(d1, [36, 22, 44, 30], (200, 40, 40))           # right red eye
z1.save(f"{OUT}/zombie_1.png")


# ---------- 4. Zombie 2: Axeman brute (brown, axe) ----------
z2 = new_sprite()
d2 = ImageDraw.Draw(z2)
ellipse(d2, [8, 8, 52, 54], (120, 90, 60))             # big body
ellipse(d2, [20, 18, 40, 38], (220, 100, 40))          # head
rect(d2, [46, 10, 58, 20], (180, 180, 180))            # axe blade
rect(d2, [50, 20, 54, 40], (100, 60, 30))              # axe handle
z2.save(f"{OUT}/zombie_2.png")


# ---------- 5. Zombie 3: Buckethead boss (blue coat, metal bucket) ----------
z3 = new_sprite()
d3 = ImageDraw.Draw(z3)
ellipse(d3, [8, 16, 56, 60], (50, 110, 180))           # coat
rect(d3, [18, 2, 46, 22], (160, 170, 180))             # bucket
ellipse(d3, [26, 28, 38, 38], (255, 50, 50))           # angry eye
z3.save(f"{OUT}/zombie_3.png")


# ---------- 6. Zombie 4: Purple mutant (spikes, yellow eye) ----------
z4 = new_sprite()
d4 = ImageDraw.Draw(z4)
for cx, cy in [(10, 20), (54, 20), (10, 44), (54, 44), (32, 8), (32, 56)]:
    ellipse(d4, [cx - 4, cy - 4, cx + 4, cy + 4], (160, 90, 200))   # spikes
ellipse(d4, [8, 12, 56, 60], (100, 50, 150))                         # body
ellipse(d4, [20, 20, 44, 44], (255, 200, 0))                         # mutant eye
ellipse(d4, [28, 28, 36, 36], OUTLINE)                               # pupil
z4.save(f"{OUT}/zombie_4.png")


# ---------- 7. Zombie 5: Fast runner (small, red, white eyes) ----------
z5 = new_sprite()
d5 = ImageDraw.Draw(z5)
ellipse(d5, [18, 18, 46, 46], (180, 50, 50))
ellipse(d5, [24, 24, 30, 30], (255, 255, 255))
ellipse(d5, [34, 24, 40, 30], (255, 255, 255))
rect(d5, [14, 30, 22, 36], (150, 40, 40))              # arm
rect(d5, [42, 30, 50, 36], (150, 40, 40))              # arm
z5.save(f"{OUT}/zombie_5.png")


# ---------- Fallback: zombie.png (Kotlin current code इसी को load करता है) ----------
z1.save(f"{OUT}/zombie.png")


# ---------- Verification ----------
expected = ["icon", "player", "zombie", "zombie_1", "zombie_2", "zombie_3", "zombie_4", "zombie_5"]
missing = [n for n in expected if not os.path.exists(f"{OUT}/{n}.png")]
if missing:
    raise SystemExit(f"[ERROR] Missing assets: {missing}")

print("[SUCCESS] Icon, player, 5 zombie sprites और fallback zombie.png बन गए।")
