from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    size = 256
    img = Image.new("RGBA", (size, size), (14, 22, 34, 255))
    draw = ImageDraw.Draw(img)

    shadow = (26, 46, 66, 255)
    folder_fill = (54, 112, 176, 255)
    folder_lid = (74, 140, 208, 255)
    page_fill = (240, 246, 252, 255)
    code_dark = (20, 54, 92, 255)
    code_light = (64, 184, 116, 255)

    draw.rounded_rectangle((36, 92, 224, 214), radius=30, fill=shadow)
    draw.rounded_rectangle((30, 78, 226, 208), radius=30, fill=folder_fill)
    draw.rounded_rectangle((50, 56, 132, 98), radius=18, fill=folder_lid)

    draw.rounded_rectangle((92, 76, 194, 192), radius=16, fill=page_fill)
    draw.polygon([(170, 76), (194, 76), (194, 100)], fill=(215, 228, 240, 255))

    draw.line([(118, 124), (100, 138), (118, 152)], fill=code_dark, width=10)
    draw.line([(164, 124), (182, 138), (164, 152)], fill=code_dark, width=10)
    draw.line([(132, 156), (146, 120)], fill=code_light, width=10)

    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    icon_path = assets_dir / "codeparser.ico"

    img.save(icon_path, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Wrote icon to {icon_path}")


if __name__ == "__main__":
    main()
