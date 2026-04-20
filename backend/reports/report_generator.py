import os
import time
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_incident_report(session_data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom Styles matching UI Theme
    title_style = ParagraphStyle('TitleCustom', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#0A0C0F'), spaceAfter=5)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#888888'), spaceAfter=20)
    heading_style = ParagraphStyle('Heading2Custom', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#0A0C0F'), spaceBefore=20, spaceAfter=10)
    normal_style = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#333333'), leading=14)
    warning_style = ParagraphStyle('Warning', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#FF1744'), leading=14, fontName='Helvetica-Bold')
    
    story = []
    
    # Header
    story.append(Paragraph("SentinelMesh Incident Report", title_style))
    report_tag = f"Report ID: SM-{int(time.time())} | Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    story.append(Paragraph(report_tag, subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#00E5FF'), spaceAfter=20))
    
    # Executive Summary (from Groq)
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(session_data.get('groq_summary', 'No summary available.'), normal_style))
    
    # Threat Overview Table
    story.append(Paragraph("Threat Overview", heading_style))
    p = session_data.get('profile', {})
    enrich = session_data.get('enrichment', {})
    
    # Determine Threat Color
    thr = p.get('threat_level', 'LOW')
    t_color = colors.HexColor('#FF1744') if thr == 'CRITICAL' else \
              colors.HexColor('#FFB300') if thr == 'HIGH' else \
              colors.HexColor('#FF8F00') if thr == 'MEDIUM' else \
              colors.HexColor('#00E676')
              
    overview_data = [
        ["Attacker IP", p.get('ip', 'Unknown')],
        ["Location", f"{enrich.get('city', 'Unknown')}, {enrich.get('country', 'Unknown')}"],
        ["Organization", enrich.get('org', 'Unknown')],
        ["Tor Exit Node", "YES (Warning)" if enrich.get('is_tor') else "No"],
        ["Behavior Pattern", p.get('behavior_type', 'Unknown').replace('_', ' ')],
        ["Inferred Intent", p.get('intent', 'Unknown').replace('_', ' ')],
        ["Peak Risk Score", f"{session_data.get('peak_score', 0)}/100"],
        ["Escalation Probability", f"{p.get('escalation_probability', 0)}%"],
        ["Threat Level", thr],
        ["Session Duration", f"{p.get('session_duration', 0)} seconds"],
        ["Resources Probed", str(p.get('access_count', 0))]
    ]
    
    t1 = Table(overview_data, colWidths=[150, 350])
    t1.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#888888')), # Left col gray
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#0A0C0F')), # Right col dark
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (1, 8), (1, 8), t_color) # Format Threat Level color
    ]))
    story.append(t1)
    
    # Attack Timeline Table
    story.append(Paragraph("Attack Timeline", heading_style))
    events = session_data.get('events', [])
    timeline_data = [["#", "Time", "Resource Accessed", "Risk", "Threat Level"]]
    
    # Reverse reverse-chronological events back to chronological for the report
    events.reverse()
    
    for idx, ev in enumerate(events):
        res = ev.get('resource_name', '')
        if len(res) > 40: res = res[:37] + "..."
        timeline_data.append([
            str(idx + 1),
            ev.get('timestamp', ''),
            res,
            str(ev.get('risk_score', 0)),
            ev.get('threat_level', 'LOW')
        ])
    
    t2 = Table(timeline_data, colWidths=[30, 80, 250, 50, 90])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A0C0F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
    ]))
    story.append(t2)
    
    # Autonomous Responses
    story.append(Paragraph("Autonomous Response Actions", heading_style))
    actions = session_data.get('actions', [])
    if not actions:
        story.append(Paragraph("No autonomous healing actions were triggered during this session.", normal_style))
    else:
        for a in actions:
            story.append(Paragraph(f"✓ {a}", normal_style))
            
    # Canary Tokens
    canaries = session_data.get('canary_events', [])
    if canaries:
        story.append(Paragraph("Canary Token Alerts (Post-Exfiltration)", heading_style))
        for ce in canaries:
            txt = f"[{ce.get('timestamp', '')}] File opened on Attacker Machine IP: {ce.get('attacker_ip')}. User Agent: {ce.get('user_agent')}"
            story.append(Paragraph(txt, warning_style))
            story.append(Spacer(1, 5))
            
    # Footer
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0'), spaceAfter=10))
    story.append(Paragraph("SentinelMesh Threat Intelligence | Symbiot 2026 | VVCE Mysuru", subtitle_style))
    
    doc.build(story)
    return output_path
