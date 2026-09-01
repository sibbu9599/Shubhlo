import shutil, glob, os

artifact_dir = r"C:\Users\Shailendra Singh\.gemini\antigravity-ide\brain\6979e514-2b2d-4f9e-94d9-e964d89c4954"
target_dir = r"c:\Users\Shailendra Singh\OneDrive\Desktop\celebrato project\static\image"

for path in glob.glob(os.path.join(artifact_dir, "hero_*.png")):
    filename = os.path.basename(path)
    # Extract clean name like hero_royal_wedding_bg.png
    clean_name = filename.split('_1786')[0] + ".png" if '_1786' in filename else filename
    dest = os.path.join(target_dir, clean_name)
    shutil.copy2(path, dest)
    print(f"Copied {filename} -> {dest}")
