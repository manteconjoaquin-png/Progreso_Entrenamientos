from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE_CANDIDATES = (ROOT / "foto.jpg", ROOT / "foto.JPG")
OUTPUT_DIR = ROOT / "views" / "icons"
ICON_SIZES = (192, 512)


def main() -> None:
    source_path = next((path for path in SOURCE_CANDIDATES if path.is_file()), None)
    if source_path is None:
        raise FileNotFoundError(f"No se encontró foto.jpg en {ROOT}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        for size in ICON_SIZES:
            icon = ImageOps.fit(
                image,
                (size, size),
                method=Image.Resampling.LANCZOS,
            )
            output_path = OUTPUT_DIR / f"icon-{size}.png"
            icon.save(output_path, format="PNG", optimize=True)
            print(f"Creado: {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()