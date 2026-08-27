"""Gera uma versao do relatorio com as figuras embutidas no proprio arquivo.

O relatorio de trabalho referencia as figuras por caminho relativo
(``figures/fig01....png``), o que so funciona dentro do repositorio. Este
script le esse relatorio, converte cada PNG em data URI base64 e grava um
segundo arquivo Markdown autocontido, que pode ser enviado por e-mail ou
anexado sem a pasta de imagens.

As figuras sao quantizadas para 64 cores antes da codificacao. Como sao
graficos de linhas e barras com poucas cores, isso reduz o arquivo final em
cerca de dois tercos sem perda visivel de qualidade.

Uso:
    python scripts/build_shareable_report.py
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports"
SOURCE = REPORT_DIR / "relatorio_medidas_alternativas_longevidade.md"
TARGET = REPORT_DIR / "relatorio_medidas_alternativas_longevidade_compartilhavel.md"

IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\((?!data:)([^)]+)\)")
PALETTE_COLORS = 64


def encode_image(path: Path) -> str:
    """Return a base64 data URI for one PNG, quantized to a small palette."""
    image = Image.open(path).convert("RGB")
    quantized = image.quantize(colors=PALETTE_COLORS, method=Image.MEDIANCUT, dither=Image.NONE)
    buffer = io.BytesIO()
    quantized.save(buffer, format="PNG", optimize=True)
    payload = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    text = SOURCE.read_text(encoding="utf-8")
    embedded = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal embedded
        alt, relative = match.group(1), match.group(2).strip()
        image_path = (REPORT_DIR / relative).resolve()
        if not image_path.exists():
            print(f"aviso: imagem nao encontrada, mantida como link: {relative}")
            return match.group(0)
        embedded += 1
        print(f"embutida: {relative} ({image_path.stat().st_size // 1024} KB no disco)")
        return f"![{alt}]({encode_image(image_path)})"

    output = IMAGE_PATTERN.sub(replace, text)
    TARGET.write_text(output, encoding="utf-8")

    size_kb = TARGET.stat().st_size // 1024
    print(f"\n{embedded} figuras embutidas")
    print(f"gravado: {TARGET.relative_to(PROJECT_ROOT)} ({size_kb} KB)")


if __name__ == "__main__":
    main()
