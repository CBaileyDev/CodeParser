from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    size = 256
    img = Image.new("RGBA", (size, size), (18, 18, 18, 255))
    draw = ImageDraw.Draw(img)

    # Folder body
    folder_rect = (32, 80, 224, 208)
    draw.rounded_rectangle(
        folder_rect,
        radius=28,
        fill=(38, 38, 38, 255),
        outline=(96, 96, 96, 255),
        width=3,
    )

    # Simple "< />" code glyph inside the folder
    # Left angle bracket
    draw.line([(90, 112), (70, 128), (90, 144)], fill=(76, 175, 80, 255), width=10)
    # Right angle bracket
    draw.line([(166, 112), (186, 128), (166, 144)], fill=(76, 175, 80, 255), width=10)
    # Forward slash
    draw.line([(120, 112), (144, 144)], fill=(129, 199, 132, 255), width=10)

    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    icon_path = assets_dir / "codeparser.ico"

    # Save as multi-size ICO for Windows
    img.save(icon_path, sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    print(f"Wrote icon to {icon_path}")


if __name__ == "__main__":
    main()
