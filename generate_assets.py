from PIL import Image, ImageDraw
import os

os.makedirs("app/src/main/res/drawable", exist_ok=True)

# 1. App Icon (512x512)
icon = Image.new("RGB", (512, 512), color=(20, 25, 30))
d = ImageDraw.Draw(icon)
d.rectangle([100, 100, 412, 412], fill=(210, 50, 50))
d.text((160, 230), "Z-Z", fill=(255, 255, 255))
icon.save("app/src/main/res/drawable/icon.png")

# 2. Player Sprite (Free Fire / 3D Style with tactical vest and cap)
player = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
pd = ImageDraw.Draw(player)
pd.ellipse([16, 12, 48, 44], fill=(50, 100, 230)) # Body
pd.rectangle([24, 4, 40, 16], fill=(220, 180, 140)) # Head
pd.rectangle([20, 2, 44, 8], fill=(30, 30, 30)) # Cap/Helmet
pd.rectangle([22, 20, 42, 38], fill=(20, 180, 80)) # Tactical Vest
player.save("app/src/main/res/drawable/player.png")

# 3. Zombie 1: Normal Walker (Green tone with tattered cloth)
z1 = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
d1 = ImageDraw.Draw(z1)
d1.ellipse([14, 14, 50, 50], fill=(40, 140, 40))
d1.ellipse([24, 24, 40, 40], fill=(200, 40, 40)) # Glowing red eye
d1.rectangle([20, 36, 44, 56], fill=(90, 70, 50)) # Rags
z1.save("app/src/main/res/drawable/zombie_1.png")

# 4. Zombie 2: Axeman / Brown Brute
z2 = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
d2 = ImageDraw.Draw(z2)
d2.ellipse([10, 10, 54, 54], fill=(120, 90, 60)) # Brute body
d2.ellipse([22, 22, 42, 42], fill=(220, 100, 40))
d2.rectangle([40, 15, 58, 25], fill=(180, 180, 180)) # Axe blade
z2.save("app/src/main/res/drawable/zombie_2.png")

# 5. Zombie 3: Buckethead Boss (Metallic bucket on head)
z3 = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
d3 = ImageDraw.Draw(z3)
d3.ellipse([10, 16, 54, 60], fill=(50, 110, 180)) # Blue padded coat
d3.rectangle([20, 2, 44, 20], fill=(160, 170, 180)) # Bucket helmet
d3.ellipse([26, 26, 38, 38], fill=(255, 50, 50)) # Angry eye
z3.save("app/src/main/res/drawable/zombie_3.png")

# 6. Zombie 4: Purple Mutant (Heavy mutated body)
z4 = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
d4 = ImageDraw.Draw(z4)
d4.ellipse([8, 12, 56, 60], fill=(100, 50, 150)) # Purple body
d4.ellipse([20, 20, 44, 44], fill=(255, 200, 0)) # Yellow mutant eye
z4.save("app/src/main/res/drawable/zombie_4.png")

# 7. Zombie 5: Fast Runner (Small & agile)
z5 = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
d5 = ImageDraw.Draw(z5)
d5.ellipse([18, 18, 46, 46], fill=(180, 50, 50)) # Red runner
d5.ellipse([26, 26, 38, 38], fill=(255, 255, 255))
z5.save("app/src/main/res/drawable/zombie_5.png")

# Fallback default zombie mapping for compatibility
zombie = z1
zombie.save("app/src/main/res/drawable/zombie.png")

print("[SUCCESS] All 5 Zombie character sprites and player generated successfully!")
