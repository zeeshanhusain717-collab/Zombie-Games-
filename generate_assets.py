from PIL import Image, ImageDraw
import os

os.makedirs("app/src/main/res/drawable", exist_ok=True)

# 1. App Icon (512x512)
icon = Image.new("RGB", (512, 512), color=(20, 25, 30))
d = ImageDraw.Draw(icon)
d.rectangle([100, 100, 412, 412], fill=(210, 50, 50))
d.text((160, 230), "Z-Z", fill=(255, 255, 255))
icon.save("app/src/main/res/drawable/icon.png")

# 2. Player Sprite (Rocky)
player = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
pd = ImageDraw.Draw(player)
pd.ellipse([16, 16, 48, 48], fill=(40, 90, 220))
pd.rectangle([28, 0, 36, 20], fill=(255, 255, 255))
player.save("app/src/main/res/drawable/player.png")

# 3. Zombie Sprite
zombie = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
zd = ImageDraw.Draw(zombie)
zd.ellipse([12, 12, 52, 52], fill=(34, 139, 34))
zd.ellipse([24, 24, 40, 40], fill=(210, 50, 50))
zombie.save("app/src/main/res/drawable/zombie.png")
print("[SUCCESS] All game images & icons generated via code!")

