# screening_engine.py

QUESTION_BANK = [
    # Domain 1: Depression-like symptoms (Q1-4)
    {"id": 1, "domain": "Depression", "text": {"en": "Little interest or pleasure in doing things?", "hi": "कामों में कम दिलचस्पी या खुशी महसूस करना?", "bn": "কাজে আগ্রহ বা আনন্দ কম পান?"}},
    {"id": 2, "domain": "Depression", "text": {"en": "Feeling down, depressed, or hopeless?", "hi": "निराश, उदास या हताश महसूस करना?", "bn": "মন খারাপ বা হতাশ বোধ করেন?"}},
    {"id": 3, "domain": "Depression", "text": {"en": "Feeling bad about yourself or feeling like a failure?", "hi": "खुद के बारे में बुरा महसूस करना या खुद को असफल मानना?", "bn": "নিজের সম্পর্কে খারাপ ধারণা বা নিজেকে ব্যর্থ মনে হয়?"}},
    {"id": 4, "domain": "Depression", "text": {"en": "Poor appetite or overeating?", "hi": "भूख कम लगना या बहुत ज़्यादा खाना?", "bn": "ক্ষুধা কম বা খুব বেশি খান?"}},
    
    # Domain 2: Anxiety and worry (Q5-8)
    {"id": 5, "domain": "Anxiety", "text": {"en": "Feeling nervous, anxious, or on edge?", "hi": "घबराहट या बेचैनी महसूस करना?", "bn": "খুব নার্ভাস বা চিন্তিত বোধ করেন?"}},
    {"id": 6, "domain": "Anxiety", "text": {"en": "Not being able to stop or control worrying?", "hi": "चिंता को रोकने या नियंत्रित करने में असमर्थ महसूस करना?", "bn": "দুশ্চিন্তা বন্ধ বা নিয়ন্ত্রণ করতে পারেন না?"}},
    {"id": 7, "domain": "Anxiety", "text": {"en": "Worrying too much about different things?", "hi": "अलग-अलग बातों के बारे में बहुत ज़्यादा चिंता करना?", "bn": "বিভিন্ন বিষয় নিয়ে খুব বেশি চিন্তা করেন?"}},
    {"id": 8, "domain": "Anxiety", "text": {"en": "Trouble relaxing?", "hi": "आराम करने में परेशानी?", "bn": "আराम করতে সমস্যা হয়?"}},
    
    # Domain 3: Stress and coping (Q9-11)
    {"id": 9, "domain": "Stress", "text": {"en": "Feeling overwhelmed by daily responsibilities?", "hi": "रोजमर्रा की जिम्मेदारियों से बोझिल महसूस करना?", "bn": "দৈনন্দিন দায়িত্ব নিয়ে খুব চাপে থাকেন?"}},
    {"id": 10, "domain": "Stress", "text": {"en": "Unable to cope with all the things you have to do?", "hi": "अपने सभी कामों को संभालने में असमर्थ महसूस करना?", "bn": "আপনার সমস্ত কাজ সামলাতে অক্ষম বোধ করেন?"}},
    {"id": 11, "domain": "Stress", "text": {"en": "Feeling constantly stressed or under pressure?", "hi": "लगातार तनाव या दबाव में महसूस करना?", "bn": "সবসময় মানসিক চাপ বা চাপের মধ্যে থাকেন?"}},
    
    # Domain 4: Sleep and energy (Q12-14)
    {"id": 12, "domain": "Sleep", "text": {"en": "Trouble falling or staying asleep, or sleeping too much?", "hi": "नींद आने या सोते रहने में परेशानी, या बहुत ज़्यादा सोना?", "bn": "ঘুমোতে বা ঘুমিয়ে থাকতে সমস্যা, বা খুব বেশি ঘুমান?"}},
    {"id": 13, "domain": "Sleep", "text": {"en": "Feeling tired or having little energy?", "hi": "थका हुआ महसूस करना या ऊर्जा कम लगना?", "bn": "ক্লান্ত বা খুব কম শক্তি বোধ করেন?"}},
    {"id": 14, "domain": "Sleep", "text": {"en": "Waking up too early and not being able to sleep again?", "hi": "बहुत जल्दी उठ जाना और फिर से सो न पाना?", "bn": "খুব সকালে ঘুম ভেঙে যায় এবং আর ঘুমাতে পারেন না?"}},
    
    # Domain 5: Daily functioning (Q15-17)
    {"id": 15, "domain": "Functioning", "text": {"en": "Trouble concentrating on things?", "hi": "चीज़ों पर ध्यान केंद्रित करने में परेशानी?", "bn": "কোনো কিছুতে মনোযোগ দিতে সমস্যা হয়?"}},
    {"id": 16, "domain": "Functioning", "text": {"en": "Moving or speaking slowly, or being overly fidgety?", "hi": "धीरे-धीरे बोलना/चलना या बहुत ज़्यादा बेचैन रहना?", "bn": "খুব ধীরে কথা বলা/হাঁটা, অথবা খুব বেশি অস্থির থাকেন?"}},
    {"id": 17, "domain": "Functioning", "text": {"en": "Difficulty performing your daily tasks at work or home?", "hi": "काम या घर पर अपनी दैनिक जिम्मेदारियां निभाने में कठिनाई?", "bn": "কাজ বা বাড়িতে দৈনন্দিন কাজ করতে সমস্যা হয়?"}},
    
    # Domain 6: Safety/crisis (Q18-20)
    {"id": 18, "domain": "Safety", "text": {"en": "Thoughts that you would be better off dead?", "hi": "ऐसे विचार आना कि आपका मर जाना ही बेहतर होगा?", "bn": "এমন কি মনে হয় যে মরে গেলেই ভালো হতো?"}},
    {"id": 19, "domain": "Safety", "text": {"en": "Thoughts of hurting yourself in some way?", "hi": "खुद को किसी तरह का नुकसान पहुँचाने का विचार आना?", "bn": "নিজেকে কোনোভাবে আঘাত করার চিন্তা আসে?"}},
    {"id": 20, "domain": "Safety", "text": {"en": "Feeling like you are in immediate danger or a crisis?", "hi": "ऐसा महसूस करना कि आप तत्काल खतरे या संकट में हैं?", "bn": "এমন মনে হয় যে আপনি খুব বিপদে বা সংকটে আছেন?"}},
]

class ScreeningSession:
    def __init__(self, lang="en"):
        self.lang = lang
        self.answers = {}
        
    def submit_answer(self, question_id: int, value: int, skipped: bool = False):
        """
        Stores an answer. Skipped answers are explicitly tracked with a None value.
        """
        self.answers[question_id] = {
            "value": None if skipped else value,
            "skipped": skipped
        }
        
    def calculate_results(self) -> dict:
        """
        Calculates domain scores and enforces clinical safety gating logic.
        """
        total_questions = len(QUESTION_BANK)
        answered_count = sum(1 for a in self.answers.values() if not a['skipped'])
        # Total skipped is explicitly skipped + unsubmitted
        skipped_count = total_questions - answered_count
        
        # Check safety/crisis domains
        safety_q_ids = [q['id'] for q in QUESTION_BANK if q['domain'] == 'Safety']
        
        safety_skipped = False
        high_safety_alert = False
        
        for q_id in safety_q_ids:
            ans = self.answers.get(q_id)
            if not ans or ans.get("skipped"):
                safety_skipped = True
            elif ans.get("value") is not None and ans.get("value") >= 1:
                high_safety_alert = True
                
        # Calculate domain scores safely (only if not skipped)
        domains = {}
        for q in QUESTION_BANK:
            ans = self.answers.get(q['id'])
            if not ans or ans['skipped']:
                continue
            if q['domain'] not in domains:
                domains[q['domain']] = 0
            domains[q['domain']] += ans['value']
            
        # Clinical Status Gating Logic
        status = "INSUFFICIENT_DATA"
        
        if safety_skipped:
            status = "SAFETY_INCOMPLETE"
        elif answered_count == total_questions:
            status = "COMPLETE"
        elif answered_count >= 16:
            status = "PARTIAL"
            
        result = {
            "status": status,
            "high_safety_alert": high_safety_alert,
            "answered_count": answered_count,
            "skipped_count": skipped_count,
            "domain_scores": domains if status in ["COMPLETE", "PARTIAL"] else {},
            "emergency_payload": None
        }
        
        if high_safety_alert:
            result["emergency_payload"] = {
                "message": "Immediate help is available. Please reach out to emergency services right now.",
                "helpline": "Tele-MANAS (14416) or 112"
            }
            
        return result
