"""Generate the Planning ADMR logo: calendar + heart on a green rounded square."""
from PIL import Image, ImageDraw

SIZE = 1024
GREEN_TOP = (60, 177, 121)
GREEN_BOT = (29, 122, 82)
WHITE = (255, 255, 255)
RING = (25, 100, 68)
HEART = (230, 57, 70)
LINE_GRAY = (200, 205, 202)

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Background: vertical gradient rounded square
bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
bpx = bg.load()
for y in range(SIZE):
    t = y / (SIZE - 1)
    r = int(GREEN_TOP[0] + (GREEN_BOT[0] - GREEN_TOP[0]) * t)
    g = int(GREEN_TOP[1] + (GREEN_BOT[1] - GREEN_TOP[1]) * t)
    b = int(GREEN_TOP[2] + (GREEN_BOT[2] - GREEN_TOP[2]) * t)
    for x in range(SIZE):
        bpx[x, y] = (r, g, b, 255)
mask = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE, SIZE], radius=230, fill=255)
img.paste(bg, (0, 0), mask)

# Calendar body
d.rounded_rectangle([232, 300, 792, 800], radius=60, fill=WHITE)
# Green header band: rounded top corners, flat bottom edge
d.rounded_rectangle([232, 300, 792, 520], radius=60, fill=GREEN_BOT)
d.rectangle([232, 430, 792, 520], fill=GREEN_BOT)
d.line([252, 452, 772, 452], fill=(255, 255, 255, 70), width=4)

# Binder rings
for cx in (360, 664):
    d.rounded_rectangle([cx - 26, 238, cx + 26, 372], radius=26, fill=RING)

# Heart (two discs + triangle)
d.ellipse([392, 470, 532, 610], fill=HEART)
d.ellipse([492, 470, 632, 610], fill=HEART)
d.polygon([(392, 545), (632, 545), (512, 700)], fill=HEART)

# Schedule lines under the heart
for y in (742, 776):
    d.rounded_rectangle([332, y - 9, 692, y + 9], radius=9, fill=LINE_GRAY)

img.save("assets/logo.png")
print("logo.png saved")
