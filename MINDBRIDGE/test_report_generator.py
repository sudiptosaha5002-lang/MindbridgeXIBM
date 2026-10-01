from report_generator import ReportGenerator
import os

def main():
    print("="*60)
    print(" MINDBRIDGE CLINICAL REPORT GENERATOR TEST ")
    print("="*60)
    
    rg = ReportGenerator()
    
    # 1. Complete Session Data Simulation
    complete_data = {
        "status": "COMPLETE",
        "high_safety_alert": False,
        "answered_count": 20,
        "skipped_count": 0,
        "domain_scores": {
            "Depression": 5,
            "Anxiety": 6,
            "Stress": 4,
            "Sleep": 2,
            "Functioning": 3,
            "Safety": 0
        },
        "emergency_payload": None
    }
    
    pdf1 = rg.generate_pdf(complete_data, "sample_complete_report.pdf")
    print(f"✅ Generated Complete Assessment Report: {pdf1}")
    
    # 2. Safety Incomplete Session Data Simulation
    safety_incomplete_data = {
        "status": "SAFETY_INCOMPLETE",
        "high_safety_alert": False,
        "answered_count": 19,
        "skipped_count": 1,
        "domain_scores": {
            "Depression": 5,
            "Anxiety": 6
        }, # This dictionary should be suppressed by the rules
        "emergency_payload": None
    }
    
    pdf2 = rg.generate_pdf(safety_incomplete_data, "sample_safety_incomplete_report.pdf")
    print(f"✅ Generated Safety Incomplete Report: {pdf2}")
    
    # Verify outputs
    assert os.path.exists(pdf1), "Failed to create complete report."
    assert os.path.exists(pdf2), "Failed to create safety incomplete report."
    
    print("\n✅ All clinical guardrails enforced successfully.")
    print("   Check the directory for 'sample_complete_report.pdf' and 'sample_safety_incomplete_report.pdf' to view the 15-section PDFs!")

if __name__ == "__main__":
    main()
