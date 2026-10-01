from screening_engine import ScreeningSession

def test_case_1():
    print("--- Test Case 1: 20/20 Complete ---")
    session = ScreeningSession()
    for i in range(1, 21):
        # Answers 0 (Never), except safety questions answered as 0
        session.submit_answer(i, 0, skipped=False)
    res = session.calculate_results()
    assert res['status'] == 'COMPLETE'
    assert res['high_safety_alert'] == False
    return res

def test_case_2():
    print("--- Test Case 2: 17 answered, 3 non-safety skipped ---")
    session = ScreeningSession()
    for i in range(1, 18):
        session.submit_answer(i, 0, skipped=False)
    for i in range(18, 21):
        session.submit_answer(i, 0, skipped=False)
    # let's explicitly skip 15, 16, 17
    session.submit_answer(15, None, skipped=True)
    session.submit_answer(16, None, skipped=True)
    session.submit_answer(17, None, skipped=True)
    res = session.calculate_results()
    assert res['status'] == 'PARTIAL'
    assert res['high_safety_alert'] == False
    return res

def test_case_3():
    print("--- Test Case 3: 19 answered, 1 safety skipped ---")
    session = ScreeningSession()
    for i in range(1, 21):
        session.submit_answer(i, 0, skipped=False)
    # explicitly skip Q20 (crisis indicator)
    session.submit_answer(20, None, skipped=True)
    res = session.calculate_results()
    assert res['status'] == 'SAFETY_INCOMPLETE'
    return res

def test_case_4():
    print("--- Test Case 4: Crisis Indicator Triggered (< 16 answered) ---")
    session = ScreeningSession()
    # Answer 10 questions
    for i in range(1, 11):
        session.submit_answer(i, 0, skipped=False)
    # Answer safety questions, trigger 1
    session.submit_answer(18, 2, skipped=False)  # More than half the days!
    session.submit_answer(19, 0, skipped=False)
    session.submit_answer(20, 0, skipped=False)
    res = session.calculate_results()
    assert res['status'] == 'INSUFFICIENT_DATA' # Only 13 total answered
    assert res['high_safety_alert'] == True     # But alert is still processed!
    return res

def main():
    tc1 = test_case_1()
    tc2 = test_case_2()
    tc3 = test_case_3()
    tc4 = test_case_4()

    print("\n| Test Case | Status | High Safety Alert | Answered | Skipped | Notes |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    print(f"| Case 1 (20/20 answered) | {tc1['status']} | {tc1['high_safety_alert']} | {tc1['answered_count']} | {tc1['skipped_count']} | Full completion, all domains scored |")
    print(f"| Case 2 (17 answered, 3 non-safety skipped) | {tc2['status']} | {tc2['high_safety_alert']} | {tc2['answered_count']} | {tc2['skipped_count']} | Valid Partial completion |")
    print(f"| Case 3 (19 answered, 1 safety skipped) | {tc3['status']} | {tc3['high_safety_alert']} | {tc3['answered_count']} | {tc3['skipped_count']} | Safety incomplete overrides completion status! |")
    print(f"| Case 4 (Crisis Alert, low answered count) | {tc4['status']} | {tc4['high_safety_alert']} | {tc4['answered_count']} | {tc4['skipped_count']} | Insufficient data for domains, but Safety Alert fires! |")

if __name__ == "__main__":
    main()
