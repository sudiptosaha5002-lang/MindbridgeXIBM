import time
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='Disclaimer', parent=self.styles['Italic'], textColor=colors.red))
        self.styles.add(ParagraphStyle(name='Heading2_Custom', parent=self.styles['Heading2'], spaceAfter=10))

    def generate_json_summary(self, session_data: dict) -> dict:
        """
        Processes screening data and enforces strict clinical reporting rules.
        """
        status = session_data.get("status", "INSUFFICIENT_DATA")
        safety_alert = session_data.get("high_safety_alert", False)
        
        report = {
            "1_Letterhead": "MINDBRIDGE CLINICAL SCREENING PLATFORM\nConfidential Self-Report Summary",
            "2_Report_Identification": f"Report ID: MB-{int(time.time())} | Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Language: en",
            "3_User_Information": "User ID: ANONYMOUS | Age/Gender: Not Provided | Mode: Digital Self-Report",
            "4_Assessment_Purpose": "Initial self-report screening to assess mental wellbeing domains and flag acute distress.",
            "5_Assessment_Method": "20-item multilingual self-report scale (4-point Likert).",
            "6_Data_Quality": f"Status: {status} | Answered: {session_data.get('answered_count')} | Skipped: {session_data.get('skipped_count')}",
        }

        # Clinical Status Gating Engine
        if status == "COMPLETE":
            report["7_Domain_Summary"] = session_data.get("domain_scores", {})
            report["8_Mental_State"] = "Valid screening pattern detected across all domains."
            report["9_Risk_Assessment"] = "HIGH RISK DETECTED" if safety_alert else "NO ACUTE CRISIS INDICATORS REPORTED."
            report["10_Clinical_Impression"] = "Non-diagnostic impression indicates completed self-report. Refer to domain scores."
            report["11_Recommendations"] = "Consider reviewing these results with a licensed professional."
        
        elif status == "PARTIAL":
            report["7_Domain_Summary"] = session_data.get("domain_scores", {})
            report["8_Mental_State"] = "[SUPPRESSED: Incomplete Data] Observations available for completed domains only."
            report["9_Risk_Assessment"] = "HIGH RISK DETECTED" if safety_alert else "NO ACUTE CRISIS INDICATORS REPORTED (Based on answered items)."
            report["10_Clinical_Impression"] = "[SUPPRESSED: Partial Data] Overall severity cannot be concluded."
            report["11_Recommendations"] = "User is encouraged to complete the full assessment."
            
        elif status == "SAFETY_INCOMPLETE":
            # SAFETY_INCOMPLETE overrides everything to enforce clinical safety standards
            report["7_Domain_Summary"] = "[SUPPRESSED: Safety Incomplete]"
            report["8_Mental_State"] = "[SUPPRESSED: Safety Incomplete]"
            report["9_Risk_Assessment"] = "[SAFETY UNKNOWN] Critical crisis indicators were skipped. Cannot clear for low risk."
            report["10_Clinical_Impression"] = "[SUPPRESSED: Safety Incomplete]"
            report["11_Recommendations"] = "IMMEDIATE ACTION REQUIRED: Clarify safety status."
            
        else: # INSUFFICIENT_DATA
            report["7_Domain_Summary"] = "[SUPPRESSED: Insufficient Data]"
            report["8_Mental_State"] = "[SUPPRESSED: Insufficient Data]"
            report["9_Risk_Assessment"] = "HIGH RISK DETECTED" if safety_alert else "[SUPPRESSED: Insufficient Data]"
            report["10_Clinical_Impression"] = "[SUPPRESSED: Insufficient Data]"
            report["11_Recommendations"] = "Resume assessment to generate screening summary."
            
        # Standard Mandatory Clinical Footers
        report["12_Platform_Limitations"] = "LIMITATION WARNING: This document is a digital self-report screening summary. It is not a clinical diagnosis, psychiatric evaluation, or medical prescription."
        report["13_Privacy_Policy"] = "Data handled according to MindBridge privacy and HIPAA-compliant confidentiality guidelines."
        report["14_Digital_Authorization"] = "Generated autonomously by the MindBridge NLP Engine."
        report["15_Professional_Review"] = "Clinician Signature: ______________________\nLicense Number: ______________________\nClinical Notes: ____________________________________________________________________\n____________________________________________________________________"
        
        return report

    def generate_pdf(self, session_data: dict, output_filename: str) -> str:
        report_data = self.generate_json_summary(session_data)
        
        doc = SimpleDocTemplate(output_filename, pagesize=letter)
        elements = []
        
        # Add Section 1 & 12
        elements.append(Paragraph(report_data["1_Letterhead"].replace('\n', '<br/>'), self.styles['Heading1']))
        elements.append(Paragraph(report_data["12_Platform_Limitations"], self.styles['Disclaimer']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=10, spaceAfter=10))
        
        # Add Sections 2-5
        elements.append(Paragraph("Report Information", self.styles['Heading2_Custom']))
        elements.append(Paragraph(report_data["2_Report_Identification"], self.styles['Normal']))
        elements.append(Paragraph(report_data["3_User_Information"], self.styles['Normal']))
        elements.append(Paragraph(report_data["4_Assessment_Purpose"], self.styles['Normal']))
        elements.append(Paragraph(report_data["5_Assessment_Method"], self.styles['Normal']))
        
        # Add Section 6
        elements.append(Paragraph("Data Quality & Completion", self.styles['Heading2_Custom']))
        elements.append(Paragraph(report_data["6_Data_Quality"], self.styles['Normal']))
        
        # Add Section 7 (Table for scores)
        elements.append(Paragraph("Clinical Screening Results", self.styles['Heading2_Custom']))
        if isinstance(report_data["7_Domain_Summary"], dict) and len(report_data["7_Domain_Summary"]) > 0:
            data = [["Clinical Domain", "Screening Score"]]
            for k, v in report_data["7_Domain_Summary"].items():
                data.append([k, str(v)])
            t = Table(data, colWidths=[200, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8F9F9")),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(t)
        else:
            # Print suppression notice
            elements.append(Paragraph(str(report_data["7_Domain_Summary"]), self.styles['Normal']))
            
        elements.append(Spacer(1, 10))
        
        # Add Sections 8-11
        elements.append(Paragraph(f"<b>Mental State:</b> {report_data['8_Mental_State']}", self.styles['Normal']))
        elements.append(Paragraph(f"<b>Risk Assessment:</b> {report_data['9_Risk_Assessment']}", self.styles['Normal']))
        elements.append(Paragraph(f"<b>Clinical Impression:</b> {report_data['10_Clinical_Impression']}", self.styles['Normal']))
        elements.append(Paragraph(f"<b>Recommendations:</b> {report_data['11_Recommendations']}", self.styles['Normal']))
        
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=20, spaceAfter=20))
        
        # Add Sections 13-14
        elements.append(Paragraph("Administrative & Legal", self.styles['Heading2_Custom']))
        elements.append(Paragraph(report_data["13_Privacy_Policy"], self.styles['Normal']))
        elements.append(Paragraph(report_data["14_Digital_Authorization"], self.styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Add Section 15
        elements.append(Paragraph("Licensed Professional Review Section", self.styles['Heading2']))
        elements.append(Paragraph("Reserved exclusively for a human clinician.", self.styles['Italic']))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(report_data["15_Professional_Review"].replace('\n', '<br/><br/>'), self.styles['Normal']))
        
        # Render PDF
        doc.build(elements)
        return output_filename
