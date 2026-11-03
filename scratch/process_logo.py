import os
from PIL import Image, ImageOps, ImageChops

source_path = r'C:\Users\Shailendra Singh\.gemini\antigravity\brain\3cdf2dbc-6dff-4554-9eb9-b160d1ff9209\.user_uploaded\media_1793618140415_93ad9973.jpg'
dest_dir = r'c:\Users\Shailendra Singh\OneDrive\Desktop\celebrato project\static'
dest_img_dir = os.path.join(dest_dir, 'image')

# 1. Open original
img = Image.open(source_path).convert('RGB')

# 2. Get bounding box of content
bg = Image.new('RGB', img.size, (255, 255, 255))
diff = ImageChops.difference(img, bg)
bbox = diff.getbbox()  # (264, 272, 768, 452)

# Add 20px padding
pad = 20
crop_box = (
    max(0, bbox[0] - pad),
    max(0, bbox[1] - pad),
    min(img.width, bbox[2] + pad),
    min(img.height, bbox[3] + pad)
)

cropped = img.crop(crop_box)
print("Cropped size:", cropped.size)

# Save standard white background versions
cropped.save(os.path.join(dest_img_dir, 'apna_infotech_logo.jpg'), 'JPEG', quality=95)
cropped.save(os.path.join(dest_dir, 'apna_infotech_logo.jpg'), 'JPEG', quality=95)
cropped.save(os.path.join(dest_img_dir, 'apna_infotech_logo.png'), 'PNG')
cropped.save(os.path.join(dest_dir, 'apna_infotech_logo.png'), 'PNG')
cropped.save(os.path.join(dest_img_dir, 'logo.png'), 'PNG')
cropped.save(os.path.join(dest_dir, 'logo.png'), 'PNG')

# 3. Create transparent version
# Convert near-white pixels to transparent with smooth gradient alpha
rgba = cropped.convert('RGBA')
datas = rgba.getdata()
new_data = []

for item in datas:
    r, g, b, a = item
    # Calculate brightness
    brightness = (r + g + b) / 3.0
    if brightness > 250:
        new_data.append((r, g, b, 0))
    elif brightness > 240:
        # smooth anti-aliased edge
        alpha = int((255 - brightness) / 15.0 * 255)
        new_data.append((r, g, b, alpha))
    else:
        new_data.append((r, g, b, 255))

rgba.putdata(new_data)
rgba.save(os.path.join(dest_img_dir, 'apna_infotech_logo_transparent.png'), 'PNG')
rgba.save(os.path.join(dest_dir, 'apna_infotech_logo_transparent.png'), 'PNG')

# 4. Create Dark Background version (White text + Cyan accent, transparent background)
rgba_white = cropped.convert('RGBA')
datas_w = rgba_white.getdata()
new_data_w = []

for item in datas_w:
    r, g, b, a = item
    brightness = (r + g + b) / 3.0
    if brightness > 245:
        # background -> fully transparent
        new_data_w.append((255, 255, 255, 0))
    else:
        # Check if it's the cyan accent
        if max(r, g, b) - min(r, g, b) > 20 and b > r:
            # Preserve / enhance cyan accent
            new_data_w.append((56, 189, 248, 255))
        else:
            # Convert dark typography to crisp white
            inv = int(255 - brightness)
            new_data_w.append((255, 255, 255, min(255, inv * 2)))

rgba_white.putdata(new_data_w)
rgba_white.save(os.path.join(dest_img_dir, 'apna_infotech_logo_white.png'), 'PNG')
rgba_white.save(os.path.join(dest_dir, 'apna_infotech_logo_white.png'), 'PNG')

print("Successfully processed and saved all logo variants!")

