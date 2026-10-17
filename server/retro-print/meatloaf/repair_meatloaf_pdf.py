#!/usr/bin/env python3
import re
import sys
from pathlib import Path


def pdf_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def extract_lines(raw):
    text = raw.decode("latin1", errors="ignore")
    found = re.findall(r"\[\((.*?)\)\]TJ", text, flags=re.S)
    lines = []
    for item in found:
        line = item.replace("\\(", "(").replace("\\)", ")").replace("\\\\", "\\")
        line = "".join(ch if ch == "\t" or ord(ch) >= 32 else " " for ch in line)
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def build_pdf(lines, out_path):
    if not lines:
        raise SystemExit("Geen complete tekstregels gevonden in Meatloaf-PDF")

    per_page = 58
    pages = [lines[i:i + per_page] for i in range(0, len(lines), per_page)]
    objects = []

    def add(obj):
        objects.append(obj)
        return len(objects)

    catalog_id = add("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add("")
    font_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    page_ids = []

    for page_lines in pages:
        content = ["BT", "/F1 10 Tf", "72 760 Td", "12 TL"]
        for line in page_lines:
            content.append(f"({pdf_escape(line)}) Tj")
            content.append("T*")
        content.append("ET")
        stream = "\n".join(content).encode("latin1", errors="replace")
        content_id = add(
            f"<< /Length {len(stream)} >>\nstream\n"
            + stream.decode("latin1")
            + "\nendstream"
        )
        page_id = add(
            "<< /Type /Page /Parent 2 0 R "
            "/MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        f"<< /Type /Pages /Count {len(page_ids)} /Kids "
        f"[{' '.join(f'{pid} 0 R' for pid in page_ids)}] >>"
    )

    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{idx} 0 obj\n{obj}\nendobj\n".encode("latin1", errors="replace"))

    xref = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    data.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        data.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    data.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            "startxref\n"
            f"{xref}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    out_path.write_bytes(data)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Gebruik: repair_meatloaf_pdf.py input.pdf output.pdf")
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    lines = extract_lines(src.read_bytes())
    build_pdf(lines, dst)


if __name__ == "__main__":
    main()
