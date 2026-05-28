import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER
from .config import PDF_FOLDER, MAX_SAMPLE_FRAMES


def generate_pdf(counts, alerts, file_type, original_path, output_path, uid,
                 video_mode=False, conf_summary=None):
    pdf_path = os.path.join(PDF_FOLDER, f"report_{uid}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    def S(n, **kw):
        return ParagraphStyle(n, parent=styles["Normal"], **kw)

    ts = S("t", fontSize=22, textColor=colors.HexColor("#1a1a2e"),
           fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
    ss = S("s", fontSize=11, textColor=colors.HexColor("#555"),
           alignment=TA_CENTER, spaceAfter=2)
    hs = S("h", fontSize=13, textColor=colors.HexColor("#1a1a2e"),
           fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6)
    bs = S("b", fontSize=10, textColor=colors.HexColor("#333"), spaceAfter=4)
    cs = S("c", fontSize=10, textColor=colors.HexColor("#c0392b"),
           fontName="Helvetica-Bold", spaceAfter=4)
    ws = S("w", fontSize=10, textColor=colors.HexColor("#e67e22"),
           fontName="Helvetica-Bold", spaceAfter=4)
    gs = S("g", fontSize=10, textColor=colors.HexColor("#27ae60"),
           fontName="Helvetica-Bold", spaceAfter=4)
    fs = S("f", fontSize=8, textColor=colors.grey, alignment=TA_CENTER)

    story = [
        Paragraph("Road Anomaly Detection", ts),
        Paragraph("AI-Powered Road Safety Analysis Report", ss),
        Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", ss),
    ]
    if video_mode:
        story.append(Paragraph(
            f"Video: counts = PEAK per frame ({MAX_SAMPLE_FRAMES} sampled).", ss))
    story += [Spacer(1,6), HRFlowable(width="100%",thickness=2,
               color=colors.HexColor("#1a1a2e")), Spacer(1,10)]

    hazard_count  = counts.get("RoadDamages",0) + counts.get("UnsurfacedRoad",0)
    vehicle_count = counts.get("HMV",0) + counts.get("LMV",0)
    severity      = "Critical" if hazard_count>=3 else ("Moderate" if hazard_count>0 else "Low")

    story.append(Paragraph("Analysis Summary", hs))
    sdata = [["Parameter","Value"],
             ["File Type", file_type.upper()],
             ["Total Objects", str(sum(counts.values()))],
             ["Total Hazards", str(hazard_count)],
             ["Total Vehicles", str(vehicle_count)],
             ["Severity", severity],
             ["Time", datetime.now().strftime("%H:%M:%S")]]
    st = Table(sdata, colWidths=[90*mm,80*mm])
    st.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#f8f9fa"),colors.white]),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#ddd")),
        ("PADDING",(0,0),(-1,-1),8),
        ("ALIGN",(1,0),(1,-1),"CENTER"),
    ]))
    story += [st, Spacer(1,12)]

    story.append(Paragraph("Detection Breakdown & Confidence", hs))
    lmap = {"HMV":"Heavy Motor Vehicle","LMV":"Light Motor Vehicle",
            "Pedestrian":"Pedestrian","RoadDamages":"Road Damages / Potholes",
            "SpeedBump":"Speed Bump","UnsurfacedRoad":"Unsurfaced Road"}
    cats = {"HMV":"Vehicle","LMV":"Vehicle","Pedestrian":"People",
            "RoadDamages":"Road Hazard","SpeedBump":"Road Feature",
            "UnsurfacedRoad":"Road Hazard"}
    ddata = [["Class","Count","Category","Avg Conf","Min","Max"]]
    for key, lbl in lmap.items():
        c = (conf_summary or {}).get(key, {})
        ddata.append([lbl, str(counts.get(key,0)), cats[key],
                      f"{c['avg']}%" if c else "—",
                      f"{c['min']}%" if c else "—",
                      f"{c['max']}%" if c else "—"])
    dt = Table(ddata, colWidths=[60*mm,20*mm,35*mm,22*mm,18*mm,18*mm])
    dt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2c3e50")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#f8f9fa"),colors.white]),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#ddd")),
        ("PADDING",(0,0),(-1,-1),7),
        ("ALIGN",(1,0),(-1,-1),"CENTER"),
    ]))
    story += [dt, Spacer(1,12)]

    story.append(Paragraph("Alerts & Recommendations", hs))
    if alerts:
        for a in alerts:
            sty = cs if a["level"]=="critical" else ws if a["level"]=="warning" else gs
            story.append(Paragraph(f"{a['icon']}  {a['message']}", sty))
    else:
        story.append(Paragraph("No alerts generated.", bs))
    story += [Spacer(1,12),
              HRFlowable(width="100%",thickness=1,color=colors.HexColor("#ccc")),
              Spacer(1,6),
              Paragraph("Generated by Road Anomaly Detection — YOLOv8", fs)]
    doc.build(story) # type: ignore
    return pdf_path