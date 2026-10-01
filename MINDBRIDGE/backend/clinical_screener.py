"""
MindBridge Clinical Screening & Risk Assessment Engine.
Implements validated, non-diagnostic screening scoring (PHQ-9 & GAD-7 concepts),
distress estimation, crisis rule triggers, and clinical referral navigation.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple

class ClinicalScreener:
    """
    Empathetic, non-diagnostic clinical screening engine.
    Computes depressive and anxiety distress indices, detects acute crisis markers,
    and returns tiered professional care recommendations.
    """

    PHQ9_RULES = {
        "phq9_item_1": "anhedonia",
        "phq9_item_2": "depressed_mood",
        "phq9_item_3": "sleep_disturbance",
        "phq9_item_4": "fatigue",
        "phq9_item_5": "appetite_change",
        "phq9_item_6": "low_self_worth",
        "phq9_item_7": "concentration_difficulty",
        "phq9_item_8": "psychomotor_agitation_retardation",
        "phq9_item_9_suicidality": "suicidal_ideation"
    }

    GAD7_RULES = {
        "gad7_item_1": "nervousness",
        "gad7_item_2": "uncontrolled_worry",
        "gad7_item_3": "excessive_worry",
        "gad7_item_4": "trouble_relaxing",
        "gad7_item_5": "restlessness",
        "gad7_item_6": "irritability",
        "gad7_item_7": "fear_of_catastrophe"
    }

    CRISIS_RULES = {
        "crisis_rule_active_ideation": "Active suicidal thoughts",
        "crisis_rule_suicide_plan": "Suicidal plan or preparation",
        "crisis_rule_means_access": "Access to lethal means",
        "crisis_rule_self_harm": "Recent active self-harm",
        "crisis_rule_past_attempt": "History of suicide attempt",
        "crisis_rule_domestic_abuse": "Active domestic violence or abuse",
        "crisis_rule_harm_to_others": "Homicidal ideation or intent to harm others"
    }

    def __init__(self, questions_path: Optional[str] = None):
        if not questions_path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            questions_path = os.path.join(base_dir, "screening_questions.json")
        self.questions_path = questions_path
        self.questions: List[Dict[str, Any]] = []
        self.questions_by_id: Dict[int, Dict[str, Any]] = {}
        self.questions_by_rule: Dict[str, Dict[str, Any]] = {}
        self._load_questions()

    def _load_questions(self):
        if os.path.exists(self.questions_path):
            with open(self.questions_path, "r", encoding="utf-8") as f:
                self.questions = json.load(f)
                for q in self.questions:
                    self.questions_by_id[q["id"]] = q
                    rule = q.get("scoring_rule")
                    if rule:
                        self.questions_by_rule[rule] = q

    def get_question_by_id(self, q_id: int) -> Optional[Dict[str, Any]]:
        return self.questions_by_id.get(q_id)

    def get_questions(self, domain: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Filters questions by domain and optionally limits quantity."""
        qs = self.questions
        if domain:
            qs = [q for q in qs if q.get("domain") == domain]
        if limit and limit > 0:
            qs = qs[:limit]
        return qs

    def parse_numeric_response(self, raw_value: Any) -> int:
        """Parses Likert responses (0 to 3) or converts text numbers safely."""
        if isinstance(raw_value, (int, float)):
            return max(0, min(3, int(raw_value)))
        if isinstance(raw_value, str):
            clean = raw_value.strip().lower()
            if clean in ["0", "not at all", "never", "no"]:
                return 0
            if clean in ["1", "several days", "sometimes", "mild"]:
                return 1
            if clean in ["2", "more than half the days", "often", "frequently", "moderate"]:
                return 2
            if clean in ["3", "nearly every day", "always", "severe", "yes"]:
                return 3
            # Search for integer digit
            m = re.search(r"\b([0-3])\b", clean)
            if m:
                return int(m.group(1))
        return 0

    def parse_yes_no(self, raw_value: Any) -> bool:
        """Parses affirmative yes/no responses."""
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, (int, float)):
            return int(raw_value) > 0
        if isinstance(raw_value, str):
            clean = raw_value.strip().lower()
            return clean in ["yes", "y", "true", "1", "definitely", "frequently", "always"]
        return False

    def evaluate_phq9(self, answers: Dict[Any, Any]) -> Tuple[int, str]:
        """
        Computes standard PHQ-9 score (0-27) and severity tier:
        0-4: minimal, 5-9: mild, 10-14: moderate, 15-19: moderately_severe, 20-27: severe.
        """
        score = 0
        for rule in self.PHQ9_RULES:
            q = self.questions_by_rule.get(rule)
            val = 0
            if q and q["id"] in answers:
                val = self.parse_numeric_response(answers[q["id"]])
            elif rule in answers:
                val = self.parse_numeric_response(answers[rule])
            score += val

        if score <= 4:
            severity = "minimal"
        elif score <= 9:
            severity = "mild"
        elif score <= 14:
            severity = "moderate"
        elif score <= 19:
            severity = "moderately_severe"
        else:
            severity = "severe"

        return score, severity

    def evaluate_gad7(self, answers: Dict[Any, Any]) -> Tuple[int, str]:
        """
        Computes standard GAD-7 score (0-21) and severity tier:
        0-4: minimal, 5-9: mild, 10-14: moderate, 15-21: severe.
        """
        score = 0
        for rule in self.GAD7_RULES:
            q = self.questions_by_rule.get(rule)
            val = 0
            if q and q["id"] in answers:
                val = self.parse_numeric_response(answers[q["id"]])
            elif rule in answers:
                val = self.parse_numeric_response(answers[rule])
            score += val

        if score <= 4:
            severity = "minimal"
        elif score <= 9:
            severity = "mild"
        elif score <= 14:
            severity = "moderate"
        else:
            severity = "severe"

        return score, severity

    def evaluate_crisis_risk(self, answers: Dict[Any, Any]) -> Tuple[str, List[str]]:
        """
        Evaluates immediate crisis triggers:
        - Active suicide ideation, plan, access to means
        - Deliberate self-harm
        - Harm to others
        - Severe domestic abuse
        Returns:
            risk_flag: 'none' | 'moderate' | 'high' | 'immediate'
            triggered_reasons: List of triggered clinical flags
        """
        triggered = []
        is_immediate = False
        is_high = False
        is_moderate = False

        # 1. Check PHQ-9 Item 9 (Suicidal Ideation)
        phq9_item9_q = self.questions_by_rule.get("phq9_item_9_suicidality")
        item9_score = 0
        if phq9_item9_q and phq9_item9_q["id"] in answers:
            item9_score = self.parse_numeric_response(answers[phq9_item9_q["id"]])
        elif "phq9_item_9_suicidality" in answers:
            item9_score = self.parse_numeric_response(answers["phq9_item_9_suicidality"])

        if item9_score >= 2:
            is_high = True
            triggered.append("Frequent thoughts of self-harm or being better off dead (PHQ-9 Item 9 >= 2)")
        elif item9_score == 1:
            is_moderate = True
            triggered.append("Intermittent passive thoughts of being better off dead (PHQ-9 Item 9 = 1)")

        # 2. Check explicit crisis questions
        for rule, desc in self.CRISIS_RULES.items():
            q = self.questions_by_rule.get(rule)
            affirmed = False
            if q and q["id"] in answers:
                affirmed = self.parse_yes_no(answers[q["id"]])
            elif rule in answers:
                affirmed = self.parse_yes_no(answers[rule])

            if affirmed:
                triggered.append(desc)
                if rule in ["crisis_rule_suicide_plan", "crisis_rule_means_access", "crisis_rule_harm_to_others"]:
                    is_immediate = True
                elif rule in ["crisis_rule_active_ideation", "crisis_rule_self_harm", "crisis_rule_domestic_abuse"]:
                    is_high = True
                else:
                    is_moderate = True

        # Check safety contract
        safety_q = self.questions_by_rule.get("safety_contract_check")
        if safety_q and safety_q["id"] in answers:
            can_keep_safe = self.parse_yes_no(answers[safety_q["id"]])
            if not can_keep_safe and (is_high or is_moderate):
                is_immediate = True
                triggered.append("Unable to confirm immediate self-safety agreement")

        if is_immediate:
            return "immediate", triggered
        if is_high:
            return "high", triggered
        if is_moderate:
            return "moderate", triggered
        return "none", triggered

    def compute_overall_distress(self, phq9_score: int, gad7_score: int, answers: Dict[Any, Any]) -> str:
        """
        Combines PHQ-9, GAD-7, sleep, stress, and functional impairment items
        to estimate overall distress: 'low' | 'moderate' | 'high'.
        """
        combined_score = phq9_score + gad7_score

        # Add functional impairment weight
        impairment_q = self.questions_by_rule.get("functional_impairment_core")
        if impairment_q and impairment_q["id"] in answers:
            combined_score += self.parse_numeric_response(answers[impairment_q["id"]]) * 2

        # Add sleep disturbance weight
        sleep_q = self.questions_by_rule.get("non_restorative_sleep_score")
        if sleep_q and sleep_q["id"] in answers:
            combined_score += self.parse_numeric_response(answers[sleep_q["id"]])

        # Add perceived stress weight
        stress_q = self.questions_by_rule.get("subjective_nervous_overload")
        if stress_q and stress_q["id"] in answers:
            combined_score += self.parse_numeric_response(answers[stress_q["id"]])

        if combined_score <= 6:
            return "low"
        if combined_score <= 18:
            return "moderate"
        return "high"

    def determine_recommendation(
        self,
        overall_distress: str,
        risk_flag: str,
        phq9_severity: str,
        gad7_severity: str
    ) -> Tuple[str, str]:
        """
        Determines the safe, non-diagnostic recommended action and empathetic summary:
        1. crisis_resources: Active crisis risk detected (Immediate risk)
        2. urgent_psychiatrist_referral: High distress / severe depression or anxiety
        3. psychologist_referral: Mild–moderate distress
        4. self_care: Low distress
        """
        if risk_flag == "immediate":
            action = "crisis_resources"
            summary = (
                "Your responses indicate urgent emotional distress. Your safety and wellbeing are paramount. "
                "Please connect immediately with a verified 24/7 crisis counselor (such as Tele-MANAS at 14416) "
                "or contact an emergency hospital or trusted family member right now."
            )
        elif risk_flag == "high" or overall_distress == "high" or phq9_severity == "severe" or gad7_severity == "severe":
            action = "urgent_psychiatrist_referral"
            summary = (
                "Your responses reflect high emotional distress that appears to significantly impact your functioning and peace of mind. "
                "MindBridge recommends an urgent, caring consultation with a verified clinical psychologist or psychiatrist "
                "registered with the National Medical Commission (NMC) or RCI."
            )
        elif overall_distress == "moderate" or phq9_severity in ["mild", "moderate", "moderately_severe"] or gad7_severity in ["mild", "moderate"]:
            action = "psychologist_referral"
            summary = (
                "Your responses suggest mild-to-moderate distress, worry, or mood strain. Speaking with a licensed "
                "clinical or counseling psychologist can provide dedicated emotional support and evidence-based coping strategies."
            )
        else:
            action = "self_care"
            summary = (
                "Your responses indicate low distress and healthy baseline coping. Continuing supportive self-care routines, "
                "mindful breathing, regular rest, and staying connected with loved ones will help maintain your wellbeing."
            )

        return action, summary

    def evaluate_assessment(self, answers: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Evaluates a complete or partial screening assessment.
        Returns the exact JSON schema required by technical specifications:
        {
          "phq9_score": int,
          "phq9_severity": "minimal|mild|moderate|moderately_severe|severe",
          "gad7_score": int,
          "gad7_severity": "minimal|mild|moderate|severe",
          "overall_distress": "low|moderate|high",
          "risk_flag": "none|moderate|high|immediate",
          "summary_text": "short empathetic explanation",
          "recommended_action": "self_care|psychologist_referral|urgent_psychiatrist_referral|crisis_resources"
        }
        """
        # Normalize keys so both integer IDs, string IDs, and rule strings work seamlessly
        normalized_answers = {}
        for k, v in answers.items():
            normalized_answers[k] = v
            try:
                normalized_answers[int(k)] = v
            except (ValueError, TypeError):
                pass
            normalized_answers[str(k)] = v
        answers = normalized_answers

        phq9_score, phq9_sev = self.evaluate_phq9(answers)
        gad7_score, gad7_sev = self.evaluate_gad7(answers)
        risk_flag, triggered_reasons = self.evaluate_crisis_risk(answers)
        overall_distress = self.compute_overall_distress(phq9_score, gad7_score, answers)
        action, summary = self.determine_recommendation(overall_distress, risk_flag, phq9_sev, gad7_sev)

        return {
            "phq9_score": phq9_score,
            "phq9_severity": phq9_sev,
            "gad7_score": gad7_score,
            "gad7_severity": gad7_sev,
            "overall_distress": overall_distress,
            "risk_flag": risk_flag,
            "summary_text": summary,
            "recommended_action": action,
            "clinical_governance": {
                "is_diagnostic": False,
                "disclaimer": "This tool is a supportive care-navigation screener and does not diagnose any psychiatric condition.",
                "triggered_risk_markers": triggered_reasons,
                "total_items_answered": len(answers)
            }
        }
