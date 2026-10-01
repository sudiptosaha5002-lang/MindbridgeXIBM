import os
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer

class SupportStateClassifier:
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        # CPU hardware constraints for AMD Ryzen 5
        torch.set_num_threads(4)
        print(f"[*] Loading Zero-Shot Multilingual Embedding Model on {torch.get_num_threads()} CPU threads...")
        
        # Load the sentence transformer
        self.model = SentenceTransformer(model_name, device='cpu')
        
        # Canonical Anchor Definitions (Multilingual)
        self.state_anchors = {
            "CALM_STABLE": ["I feel calm", "everything is fine", "mujhe theek lag raha hai", "ami bhalo achi"],
            "MILD_STRESS_OVERWHELMED": ["exam ko leke tension hai but manage kar lunga", "kaam ka pressure", "overwhelmed by office stress", "too much work to do", "halka chap lagche", "workload is high"],
            "ANXIETY_WORRY": ["bahut ghabrahat ho rahi hai", "anxious feel ho raha hai", "chinta hocche", "worrying too much", "fear of future", "khub voy korche", "পরীক্ষা নিয়ে খুব চিন্তা হচ্ছে, কিছু মাথায় ঢুকছে না"],
            "PANIC_LIKE_SYMPTOMS": ["panic attack", "saans lene me dikkat", "heart racing", "nishash bondho hoye asche", "can't breathe", "sweating and shaking", "severe panic"],
            "LOW_MOOD_SADNESS": ["sad", "feeling down today", "mood theek nahi", "mon kharap", "kuch accha nahi lag raha", "kosto hocche"],
            "DEPRESSION_LIKE_DISTRESS": ["no hope left", "completely empty", "zindagi bekar lag rahi hai", "kono asha nei", "nothing matters anymore", "completely burned out"],
            "LONELINESS_ISOLATION": ["lonely", "koi baat karne wala nahi", "amar keu nei", "eka lagche", "no one understands me", "completely alone", "Amar khub eka lagche, keu kotha bolar nei"],
            "GRIEF_LOSS": ["lost my loved one", "someone died", "grief", "breakup pain", "khub kacher keu chole geche", "shok"],
            "ANGER_IRRITABILITY": ["gussa aa raha hai", "angry", "irritated", "khoob raag hocche", "frustrated", "everyone annoys me"],
        }
        
        self.intent_anchors = {
            "VENT_ONLY": ["I just want to rant", "mujhe bas bolna hai", "just listening to me", "shudhu kotha bolte chai", "need to express myself", "listen to my problems", "I just want someone to listen to me right now"],
            "SEEK_COPING_TOOL": ["breathing exercise", "help me calm down", "kuch tips do", "grounding technique", "ekta upaye bole din", "how to stop panic", "Can you teach me a 1-minute breathing exercise to calm down?"],
            "SEEK_CLARITY": ["samajh nahi aa raha kya karu", "confused about my feelings", "why am I feeling this way", "ki korbo bujhte parchi na", "reflecting on emotions", "help me figure out what to do"],
            "SEEK_PROFESSIONAL": ["doctor", "counselor", "therapist", "psychiatrist", "professional help", "clinic", "I want to talk to a doctor or counselor nearby"],
            "CASUAL_INTERACTION": ["hello", "hi", "how are you", "kemon acho", "kya haal hai", "good morning", "how does this app work", "Hi, how does this app work?"]
        }

        # Precompute canonical anchor embeddings (Centroids)
        self.state_embeddings = self._precompute_embeddings(self.state_anchors)
        self.intent_embeddings = self._precompute_embeddings(self.intent_anchors)

    def _precompute_embeddings(self, anchors_dict):
        embeddings_dict = {}
        for category, texts in anchors_dict.items():
            emb = self.model.encode(texts, convert_to_tensor=True)
            # Calculate the centroid embedding for the category
            avg_emb = torch.mean(emb, dim=0, keepdim=True)
            embeddings_dict[category] = F.normalize(avg_emb, p=2, dim=1)
        return embeddings_dict

    def classify_support_state(self, text: str, conversation_history: list = None) -> dict:
        """
        Classifies the mental support state and primary user intent using Cosine Similarity against centroids.
        Includes confidence gating and historical decay context.
        """
        text_emb = self.model.encode([text], convert_to_tensor=True)
        text_emb = F.normalize(text_emb, p=2, dim=1)
        
        # Inject decaying conversation context
        if conversation_history and len(conversation_history) > 0:
            hist_emb = self.model.encode([conversation_history[-1]], convert_to_tensor=True)
            hist_emb = F.normalize(hist_emb, p=2, dim=1)
            # decay weight 0.35 for context
            text_emb = F.normalize(text_emb + 0.35 * hist_emb, p=2, dim=1)
            
        def _get_top_match(target_emb, ref_embeddings):
            best_score = -1.0
            best_cat = None
            for cat, ref_emb in ref_embeddings.items():
                # Cosine similarity (tensors are already L2 normalized, so dot product == cos sim)
                score = torch.sum(target_emb * ref_emb).item()
                if score > best_score:
                    best_score = score
                    best_cat = cat
            return best_cat, best_score

        top_state, state_conf = _get_top_match(text_emb, self.state_embeddings)
        top_intent, intent_conf = _get_top_match(text_emb, self.intent_embeddings)
        
        # Clinical Confidence Gating Logic
        if state_conf >= 0.70:
            conf_level = "HIGH"
        elif state_conf >= 0.50:
            conf_level = "MEDIUM"
        else:
            conf_level = "LOW"
            top_state = "UNKNOWN_NEEDS_CLARIFICATION"
            
        return {
            "primary_state": top_state,
            "state_confidence": state_conf,
            "primary_intent": top_intent,
            "intent_confidence": intent_conf,
            "confidence_gate": conf_level
        }
