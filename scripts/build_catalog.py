"""Render every variant from several cameras and build the choice catalog PDF."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from PIL import Image as PILImage
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scad_cli import dims_for, load_variants, run_openscad  # noqa: E402

RENDERS = ROOT / "renders"
EXPORT = ROOT / "export"
PDF = ROOT / "docs" / "leg-drawers-variant-catalog.pdf"
OPENSCAD = Path(r"C:\Program Files\OpenSCAD\openscad.exe")

H2D_GUARD = (320.0, 315.0, 320.0)

VIEWS = [
    ("assembled_iso", "assembled", "0,0,0,55,0,35,500", None, {"show_context": True, "show_table": False}),
    ("assembled_iso_rear", "assembled", "0,0,0,52,0,145,500", None, {"show_context": True, "show_table": False}),
    ("assembled_iso_flank", "assembled", "0,0,0,62,0,310,500", None, {"show_context": True, "show_table": False}),
    ("assembled_front", "assembled", "0,0,0,90,0,0,500", "o", {"show_context": True, "show_table": False}),
    ("assembled_top", "assembled", "0,0,0,0,0,0,500", "o", {"show_context": True, "show_table": False}),
    ("assembled_mount", "assembled", "0,0,0,78,0,-70,500", None, {"show_context": True, "show_table": False}),
    ("exploded_iso", "exploded", "0,0,0,55,0,35,500", None, {"show_context": False, "show_table": False}),
    ("housing_print_iso", "housing_print", "0,0,0,55,0,35,500", None, {}),
    ("housing_print_openings", "housing_print", "0,0,0,18,0,15,500", None, {}),
    ("drawer_print_iso", "drawer_print", "0,0,0,55,0,25,500", None, {}),
]


def png_path(vid: str, view: str) -> Path:
    return RENDERS / vid / f"{view}.png"


def stl_path(vid: str, part: str) -> Path:
    return EXPORT / vid / f"{part}.stl"


def render_all(variants: list[dict]) -> list[str]:
    log: list[str] = []
    for v in variants:
        vid = v["id"]
        params = v["params"]
        for name, part, camera, projection, extra in VIEWS:
            extra = dict(extra)
            extra["part"] = part
            out = png_path(vid, name)
            if out.exists() and out.stat().st_size > 4000:
                log.append(f"skip png {vid}/{name}")
                continue
            result = run_openscad(
                out,
                params,
                extra,
                camera=camera,
                projection=projection,
                imgsize="1600,1200",
                timeout=180,
            )
            if result.returncode != 0 or not out.exists() or out.stat().st_size < 2000:
                raise RuntimeError(
                    f"render failed {vid}/{name} rc={result.returncode}\n"
                    f"{(result.stderr or '')[-2000:]}"
                )
            log.append(f"png {vid}/{name} {out.stat().st_size}")
        for part in ("housing_print", "drawer_print"):
            out = stl_path(vid, part)
            if out.exists() and out.stat().st_size > 8000:
                log.append(f"skip stl {vid}/{part}")
                continue
            result = run_openscad(out, params, {"part": part}, timeout=180)
            if result.returncode != 0 or not out.exists() or out.stat().st_size < 8000:
                raise RuntimeError(
                    f"stl failed {vid}/{part} rc={result.returncode}\n"
                    f"{(result.stderr or '')[-2000:]}"
                )
            log.append(f"stl {vid}/{part} {out.stat().st_size}")
    return log


def collect_dims(variants: list[dict]) -> dict[str, dict]:
    out = {}
    for v in variants:
        dims, _raw = dims_for(v["params"])
        hx, hy, hz = dims["housing_print_x"], dims["housing_print_y"], dims["housing_print_z"]
        dx, dy, dz = dims["drawer_print_x"], dims["drawer_print_y"], dims["drawer_print_z"]
        dims["h2d_housing_ok"] = hx <= H2D_GUARD[0] and hy <= H2D_GUARD[1] and hz <= H2D_GUARD[2]
        dims["h2d_drawer_ok"] = dx <= H2D_GUARD[0] and dy <= H2D_GUARD[1] and dz <= H2D_GUARD[2]
        dims["h2d_ok"] = bool(dims["h2d_housing_ok"] and dims["h2d_drawer_ok"])
        out[v["id"]] = dims
    return out


def styles():
    base = getSampleStyleSheet()
    s = {
        "title": ParagraphStyle(
            "T", parent=base["Title"], fontName="Times-Bold", fontSize=22,
            leading=26, textColor=colors.HexColor("#0b0f19"), alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Times-Bold", fontSize=16,
            leading=20, textColor=colors.HexColor("#0b0f19"), spaceBefore=8, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Times-Bold", fontSize=12,
            leading=15, textColor=colors.HexColor("#0b0f19"), spaceBefore=6, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "B", parent=base["Normal"], fontName="Times-Roman", fontSize=10,
            leading=13, textColor=colors.HexColor("#0b0f19"),
        ),
        "small": ParagraphStyle(
            "S", parent=base["Normal"], fontName="Times-Roman", fontSize=8,
            leading=10, textColor=colors.HexColor("#0b0f19"),
        ),
        "caption": ParagraphStyle(
            "C", parent=base["Normal"], fontName="Times-Italic", fontSize=8,
            leading=10, textColor=colors.HexColor("#1f2937"), alignment=TA_CENTER,
        ),
        "cell": ParagraphStyle(
            "Cell", parent=base["Normal"], fontName="Times-Roman", fontSize=7.5,
            leading=9.5, textColor=colors.HexColor("#0b0f19"),
        ),
        "cellb": ParagraphStyle(
            "CellB", parent=base["Normal"], fontName="Times-Bold", fontSize=7.5,
            leading=9.5, textColor=colors.HexColor("#0b0f19"),
        ),
        "foot": ParagraphStyle(
            "F", parent=base["Normal"], fontName="Times-Roman", fontSize=8,
            leading=10, textColor=colors.HexColor("#4b5563"), alignment=TA_CENTER,
        ),
    }
    return s


def jpeg_for(path: Path) -> Path:
    jpg = path.with_suffix(".jpg")
    if jpg.exists() and jpg.stat().st_mtime >= path.stat().st_mtime:
        return jpg
    with PILImage.open(path) as im:
        im.convert("RGB").save(jpg, "JPEG", quality=82, optimize=True)
    return jpg


def fig(path: Path, max_w: float, max_h: float) -> Image:
    jpg = jpeg_for(path)
    with PILImage.open(jpg) as im:
        w, h = im.size
    if w < 1 or h < 1:
        raise RuntimeError(f"bad image size {jpg}: {w}x{h}")
    scale = min(max_w / float(w), max_h / float(h))
    img = Image(str(jpg), width=float(w) * scale, height=float(h) * scale)
    img.hAlign = "CENTER"
    return img


def labeled_fig(path: Path, label: str, st, max_w, max_h):
    block = Table(
        [[fig(path, max_w, max_h)], [Paragraph(label, st["caption"])]],
        colWidths=[max_w + 6],
    )
    block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return block


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#ffffff"))
    canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0b0f19"))
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(0.7 * inch, 0.45 * inch, "leg-drawers  ·  parametric table-leg zip-tie drawer set")
    canvas.drawRightString(letter[0] - 0.7 * inch, 0.45 * inch, f"page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#9ca3af"))
    canvas.setLineWidth(0.6)
    canvas.line(0.7 * inch, 0.62 * inch, letter[0] - 0.7 * inch, 0.62 * inch)
    canvas.restoreState()


def comparison_table(variants, dims, st):
    cell, cellb = st["cell"], st["cellb"]
    header = [
        Paragraph("<b>Name</b>", cellb),
        Paragraph("<b>Drawers</b>", cellb),
        Paragraph("<b>Bay H x W x D mm</b>", cellb),
        Paragraph("<b>Leg X x Y mm</b>", cellb),
        Paragraph("<b>Mount</b>", cellb),
        Paragraph("<b>Ledges L/R/B/F mm</b>", cellb),
        Paragraph("<b>Housing print mm</b>", cellb),
        Paragraph("<b>H2D</b>", cellb),
    ]
    rows = [header]
    for v in variants:
        p = v["params"]
        d = dims[v["id"]]
        side = "left" if p["leg_on_left"] else "right"
        ok = "PASS" if d["h2d_ok"] else "FAIL"
        rows.append([
            Paragraph(v["id"], cellb),
            Paragraph(str(p["drawer_count"]), cell),
            Paragraph(f"{p['drawer_height']} x {p['drawer_width']} x {p['drawer_depth']}", cell),
            Paragraph(f"{p['leg_x']} x {p['leg_y']}", cell),
            Paragraph(side, cell),
            Paragraph(
                f"{p['ledge_left']}/{p['ledge_right']}/{p['ledge_back']}/{p['ledge_front']}",
                cell,
            ),
            Paragraph(
                f"{d['housing_print_x']:.0f} x {d['housing_print_y']:.0f} x {d['housing_print_z']:.0f}",
                cell,
            ),
            Paragraph(ok, cellb),
        ])
    usable = letter[0] - 1.4 * inch
    widths = [usable * x for x in (0.16, 0.08, 0.16, 0.12, 0.08, 0.16, 0.16, 0.08)]
    tbl = Table(rows, colWidths=widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0b0f19")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#6b7280")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tbl


def param_table(v, d, st):
    p = v["params"]
    cell, cellb = st["cell"], st["cellb"]
    side = "left" if p["leg_on_left"] else "right"
    rows = [
        [Paragraph("<b>Parameter</b>", cellb), Paragraph("<b>Value</b>", cellb),
         Paragraph("<b>Parameter</b>", cellb), Paragraph("<b>Value</b>", cellb)],
        [Paragraph("drawer_count", cell), Paragraph(str(p["drawer_count"]), cell),
         Paragraph("leg_on_left", cell), Paragraph(side, cell)],
        [Paragraph("drawer_height mm", cell), Paragraph(str(p["drawer_height"]), cell),
         Paragraph("leg_x mm", cell), Paragraph(str(p["leg_x"]), cell)],
        [Paragraph("drawer_width mm", cell), Paragraph(str(p["drawer_width"]), cell),
         Paragraph("leg_y mm", cell), Paragraph(str(p["leg_y"]), cell)],
        [Paragraph("drawer_depth mm", cell), Paragraph(str(p["drawer_depth"]), cell),
         Paragraph("zip ties (auto)", cell), Paragraph(str(int(d["auto_zips"])), cell)],
        [Paragraph("ledge_left mm", cell), Paragraph(str(p["ledge_left"]), cell),
         Paragraph("housing print X mm", cell), Paragraph(f"{d['housing_print_x']:.1f}", cell)],
        [Paragraph("ledge_right mm", cell), Paragraph(str(p["ledge_right"]), cell),
         Paragraph("housing print Y mm", cell), Paragraph(f"{d['housing_print_y']:.1f}", cell)],
        [Paragraph("ledge_back mm", cell), Paragraph(str(p["ledge_back"]), cell),
         Paragraph("housing print Z mm", cell), Paragraph(f"{d['housing_print_z']:.1f}", cell)],
        [Paragraph("ledge_front mm", cell), Paragraph(str(p["ledge_front"]), cell),
         Paragraph("drawer print mm", cell),
         Paragraph(f"{d['drawer_print_x']:.1f} x {d['drawer_print_y']:.1f} x {d['drawer_print_z']:.1f}", cell)],
        [Paragraph("H2D guard 320 x 315 x 320", cell),
         Paragraph("PASS" if d["h2d_ok"] else "FAIL", cellb),
         Paragraph("drawer outer mm", cell),
         Paragraph(f"{d['dw']:.1f} x {d['dd']:.1f} x {d['dh']:.1f}", cell)],
    ]
    usable = letter[0] - 1.4 * inch
    tbl = Table(rows, colWidths=[usable * 0.28, usable * 0.22, usable * 0.28, usable * 0.22])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#6b7280")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tbl


def build_pdf(variants, dims):
    PDF.parent.mkdir(parents=True, exist_ok=True)
    st = styles()
    story = []
    story.append(Paragraph("Table-leg zip-tie drawer set", st["title"]))
    story.append(Paragraph(
        "Ten printable variants of one OpenSCAD file. Housing and drawers are separate parts. "
        "Housing always prints with drawer openings up (back of the housing on the bed). "
        "Drawers always print bottom-down. A U-wrap on the left or right comes out of the side "
        "with a front wall and a back wall around the table leg, offset 10 mm past the far face, "
        "and a 4 x 12 mm hole through both walls front-to-back for the zip tie. Choose a winner from the plates below.",
        st["body"],
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Print envelope", st["h2"]))
    story.append(Paragraph(
        "Target printer: Bambu Lab H2D. Single-nozzle volume is 325 x 320 x 325 mm. "
        "This model uses a 5 mm guard of <b>320 x 315 x 320 mm</b>. Every variant in this catalog "
        "is marked PASS against that guard. File: <font face='Courier'>leg-drawers.scad</font> "
        "plus <font face='Courier'>variants.json</font>.",
        st["body"],
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph("How the parts go together", st["h2"]))
    story.append(Paragraph(
        "The housing is a stack of open-front bays with a tray on top. Tray wall heights are "
        "independent: left, right, back, and a usually-lower front lip. The side wrap is a front "
        "wall and a back wall around the table leg, with a 10 mm tab past the far face. Thread a "
        "zip tie through the 4 x 12 mm holes front-to-back. Drawers are separate open-top boxes with a finger slot in the front wall.",
        st["body"],
    ))
    v0 = variants[0]["id"]
    w = (letter[0] - 1.5 * inch) / 2
    h = 2.15 * inch
    pair = Table(
        [[
            labeled_fig(png_path(v0, "assembled_iso"), "Assembled (office-slim-left)", st, w, h),
            labeled_fig(png_path(v0, "housing_print_iso"), "Housing print pose — openings up", st, w, h),
        ]],
        colWidths=[w + 0.1 * inch, w + 0.1 * inch],
    )
    pair.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
    ]))
    story.append(pair)
    story.append(Paragraph("Comparison", st["h1"]))
    story.append(comparison_table(variants, dims, st))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Housing print axes after the openings-up rotation: X = width + mount, "
        "Y = stacked height + tallest ledge, Z = housing depth (front-back). "
        "Drawer print axes: X = width, Y = depth, Z = height.",
        st["small"],
    ))
    story.append(PageBreak())

    # contact sheet of assembled isos
    story.append(Paragraph("Assembled ISO — all ten", st["h1"]))
    cells = []
    row = []
    cw = (letter[0] - 1.5 * inch) / 2
    ch = 1.45 * inch
    for v in variants:
        row.append(labeled_fig(png_path(v["id"], "assembled_iso"), v["id"], st, cw, ch))
        if len(row) == 2:
            cells.append(row)
            row = []
    if row:
        row.append(Paragraph("", st["body"]))
        cells.append(row)
    sheet = Table(cells, colWidths=[cw + 0.1 * inch, cw + 0.1 * inch])
    sheet.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(sheet)
    story.append(PageBreak())

    for v in variants:
        vid = v["id"]
        d = dims[vid]
        story.append(Paragraph(f"{v['title']}  ({vid})", st["h1"]))
        story.append(Paragraph(v["intent"], st["body"]))
        story.append(Spacer(1, 6))
        story.append(param_table(v, d, st))
        story.append(Spacer(1, 8))
        w = (letter[0] - 1.5 * inch) / 2
        h = 2.35 * inch
        g1 = Table(
            [[
                labeled_fig(png_path(vid, "assembled_iso"), "ISO, drawers pulled, ghost leg", st, w, h),
                labeled_fig(png_path(vid, "assembled_iso_rear"), "ISO from the rear / mount", st, w, h),
            ]],
            colWidths=[w + 0.1 * inch, w + 0.1 * inch],
        )
        g1.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ]))
        story.append(g1)
        g2 = Table(
            [[
                labeled_fig(png_path(vid, "assembled_iso_flank"), "ISO opposite flank", st, w, h),
                labeled_fig(png_path(vid, "exploded_iso"), "Exploded — housing and drawers separate", st, w, h),
            ]],
            colWidths=[w + 0.1 * inch, w + 0.1 * inch],
        )
        g2.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ]))
        story.append(g2)
        story.append(PageBreak())

        story.append(Paragraph(f"{v['title']} — drawings and print poses", st["h1"]))
        w3 = (letter[0] - 1.6 * inch) / 3
        h3 = 1.85 * inch
        g3 = Table(
            [[
                labeled_fig(png_path(vid, "assembled_front"), "Front elevation", st, w3, h3),
                labeled_fig(png_path(vid, "assembled_top"), "Top / plan (front and back wrap walls)", st, w3, h3),
                labeled_fig(png_path(vid, "assembled_mount"), "Mount side (4 x 12 mm holes, front to back)", st, w3, h3),
            ]],
            colWidths=[w3 + 0.08 * inch] * 3,
        )
        g3.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ]))
        story.append(g3)
        g4 = Table(
            [[
                labeled_fig(png_path(vid, "housing_print_iso"), "Housing print — openings up", st, w, h),
                labeled_fig(png_path(vid, "housing_print_openings"), "Housing print — looking into bays", st, w, h),
            ]],
            colWidths=[w + 0.1 * inch, w + 0.1 * inch],
        )
        g4.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ]))
        story.append(g4)
        story.append(labeled_fig(
            png_path(vid, "drawer_print_iso"),
            "Drawer print — bottom down, finger slot in the front wall",
            st, w + 0.4 * inch, h,
        ))
        story.append(Paragraph(
            f"Export STL: <font face='Courier'>export/{vid}/housing_print.stl</font> and "
            f"<font face='Courier'>export/{vid}/drawer_print.stl</font>. "
            "Print housing as exported (openings up). Print one drawer per bay, bottom down, "
            f"{int(v['params']['drawer_count'])} copies. PETG recommended for the housing; PLA is fine for drawers. "
            "0.4 mm nozzle, 0.2 mm layers, 3 walls, 20% gyroid. No supports.",
            st["small"],
        ))
        story.append(PageBreak())

    story.append(Paragraph("Customizer reference", st["h1"]))
    story.append(Paragraph(
        "Open <font face='Courier'>leg-drawers.scad</font> in OpenSCAD. The Customizer groups are "
        "Part, Drawers, Table leg, Top ledges, and Structure. Set <font face='Courier'>part</font> "
        "to <font face='Courier'>housing_print</font> or <font face='Courier'>drawer_print</font> "
        "before F6 and STL export. A variant from this catalog is a set of "
        "<font face='Courier'>-D</font> flags matching <font face='Courier'>variants.json</font>.",
        st["body"],
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Locked print rules: housing openings face +Z after <font face='Courier'>housing_print</font> "
        "rotation (back of the housing on the bed; the wrap back wall is on the bed; "
        "the wrap front wall is a 10 mm tab past the leg with the zip-tie hole). Drawers export with the floor on Z=0. "
        "If a parameter set exceeds the H2D guard, OpenSCAD <font face='Courier'>assert</font> fails "
        "and no STL is written.",
        st["body"],
    ))

    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.75 * inch,
        title="leg-drawers variant catalog",
        author="leg-drawers",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return PDF


def main():
    data = load_variants()
    variants = data["variants"]
    assert len(variants) == 10, f"expected 10 variants, got {len(variants)}"
    print("collecting dims", flush=True)
    dims = collect_dims(variants)
    failed = [vid for vid, d in dims.items() if not d["h2d_ok"]]
    if failed:
        raise SystemExit(f"H2D guard failed: {failed}")
    print(json.dumps({vid: {k: d[k] for k in (
        "housing_print_x", "housing_print_y", "housing_print_z",
        "drawer_print_x", "drawer_print_y", "drawer_print_z", "h2d_ok",
    )} for vid, d in dims.items()}, indent=2), flush=True)
    print("rendering", flush=True)
    log = render_all(variants)
    print("\n".join(log), flush=True)
    print("building pdf", flush=True)
    path = build_pdf(variants, dims)
    print(f"PDF {path} {path.stat().st_size}", flush=True)


if __name__ == "__main__":
    main()
