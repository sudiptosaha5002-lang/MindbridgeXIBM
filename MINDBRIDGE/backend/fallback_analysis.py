import json
from typing import Dict, List, Any
from emotion_classifier import emotion_classifier

class FallbackAnalyzer:
    """
    Analyzes the answers collected from the F01-F10 fallback interview questions.
    Generates a non-diagnostic summary and recommended support level.
    """
    
    def __init__(self):
        pass
        
    def analyze_fallback_session(self, answers: List[Dict[str, Any]], language: str = "en") -> Dict[str, Any]:
        """
        Takes a list of answers: [{"question_id": "F01", "text": "..."}, ...]
        Returns the non-diagnostic structured output.
        """
        
        identified_emotions = []
        intensity = "low"
        risk_flag = "none"
        
        # Analyze each answer with the emotion classifier
        for answer in answers:
            if not answer.get("text"):
                continue
                
            # Classify the text
            classification = emotion_classifier.classify_input(answer["text"])
            
            # Aggregate emotions
            for emo in classification.get("detected_emotions", []):
                if emo != "uncertain" and emo not in identified_emotions:
                    identified_emotions.append(emo)
                    
            # Check risk flag
            cf_risk = classification.get("risk_flag", "none")
            if cf_risk == "immediate":
                risk_flag = "immediate"
            elif cf_risk == "high" and risk_flag != "immediate":
                risk_flag = "high"
            elif cf_risk == "moderate" and risk_flag not in ["immediate", "high"]:
                risk_flag = "moderate"
                
            # Check intensity
            cf_intensity = classification.get("emotion_intensity", "low")
            if cf_intensity == "high":
                intensity = "high"
            elif cf_intensity == "moderate" and intensity == "low":
                intensity = "moderate"
                
        # Determine support level and recommendation
        support_level = "low"
        recommended_action = "continue_normal_flow"
        
        if risk_flag in ["immediate", "high"]:
            support_level = "immediate_crisis"
            recommended_action = "activate_crisis_flow"
        elif risk_flag == "moderate" or intensity == "high" or len(identified_emotions) >= 3:
            support_level = "high"
            recommended_action = "psychologist_referral"
        elif intensity == "moderate" or len(identified_emotions) >= 1:
            support_level = "moderate"
            recommended_action = "psychologist_referral"

        # Generate non-diagnostic summary text based on language
        summary_text = "Thank you for sharing. It seems you are managing okay, but we are always here to support you."
        if support_level == "immediate_crisis":
            summary_text = "Your safety is the most important thing right now. We strongly recommend speaking with emergency services or a trusted contact immediately."
        elif support_level in ["high", "moderate"]:
            emo_str = " and ".join(identified_emotions[:2]) if identified_emotions else "difficult emotions"
            if language == "bn":
                summary_text = f"আপনার উত্তর থেকে মনে হচ্ছে আপনি {emo_str} অনুভব করছেন। এটি কোনো মেডিকেল ডায়াগনসিস নয়, তবে একজন বিশেষজ্ঞের সাথে কথা বলা আপনার জন্য উপকারী হতে পারে।"
            elif language == "hi":
                summary_text = f"आपके उत्तर बताते हैं कि आप {emo_str} का अनुभव कर रहे हैं। यह कोई निदान नहीं है, लेकिन किसी विशेषज्ञ से बात करना आपके लिए मददगार हो सकता है।"
            else:
                summary_text = f"Your answers suggest that you may be experiencing {emo_str}. This is not a diagnosis, but speaking with a qualified professional may be helpful."
            
        return {
            "analysis_source": "fallback_emotion_interview",
            "identified_emotions": identified_emotions,
            "emotion_intensity": intensity,
            "risk_flag": risk_flag,
            "support_level": support_level,
            "summary_text": summary_text,
            "recommended_action": recommended_action
        }

fallback_analyzer = FallbackAnalyzer()
