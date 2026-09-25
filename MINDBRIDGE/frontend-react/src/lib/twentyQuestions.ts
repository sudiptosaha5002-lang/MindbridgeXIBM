export interface TwentyQuestion {
  id: number;
  section_id: string;
  category: string;
  category_badge: string;
  question: string;
  hint: string;
}

export const TWENTY_QUESTIONS: TwentyQuestion[] = [
  // 🟣 Category A: Inner Emotional Landscape & Current State
  { id: 1, section_id: "A", category: "Inner Emotional Landscape", category_badge: "🟣 A. Inner Emotional Landscape", question: "If you had to describe how you’re feeling right now in three words, what would they be?", hint: "Share any three words that come naturally to mind right now." },
  { id: 2, section_id: "A", category: "Inner Emotional Landscape", category_badge: "🟣 A. Inner Emotional Landscape", question: "When you experience strong or overwhelming emotions, how do you usually deal with them?", hint: "e.g. taking space, deep breathing, listening to music, crying, speaking to someone, or holding it in." },
  { id: 3, section_id: "A", category: "Inner Emotional Landscape", category_badge: "🟣 A. Inner Emotional Landscape", question: "Are there any emotions that you tend to keep inside or avoid expressing? If so, what makes you hold them back?", hint: "e.g. anger, sorrow, fear of burdening others, pride, or fear of vulnerability." },

  // 🟪 Category B: Stress, Anxiety & Emotional Well-being
  { id: 4, section_id: "B", category: "Stress & Anxiety", category_badge: "🟪 B. Stress, Anxiety & Well-being", question: "Are there particular situations, thoughts, or experiences that tend to trigger stress or anxiety for you?", hint: "e.g. deadlines, crowds, unexpected conflict, financial thoughts, academic expectations." },
  { id: 5, section_id: "B", category: "Stress & Anxiety", category_badge: "🟪 B. Stress, Anxiety & Well-being", question: "What do you do to take care of your emotional well-being when you’re feeling stressed or emotionally tired?", hint: "e.g. quiet walks, warm showers, mindfulness, speaking to a loved one, disconnection from screens." },
  { id: 6, section_id: "B", category: "Stress & Anxiety", category_badge: "🟪 B. Stress, Anxiety & Well-being", question: "When you start overthinking, how do you usually handle it? Does it make it harder for you to relax or switch off your mind?", hint: "Reflect on nighttime looping thoughts and mental fatigue." },

  // 🟨 Category C: Thoughts & Self-Perception
  { id: 7, section_id: "C", category: "Thoughts & Self-Perception", category_badge: "🟨 C. Thoughts & Self-Perception", question: "When you have self-critical thoughts, how do you usually deal with them? How do they affect the way you see yourself?", hint: "Reflect on how harsh or compassionate your internal voice is when setbacks happen." },
  { id: 8, section_id: "C", category: "Thoughts & Self-Perception", category_badge: "🟨 C. Thoughts & Self-Perception", question: "How do you usually decide whether a thought is helpful, unhelpful, appropriate, or worth letting go of?", hint: "Reflect on how you differentiate emotional fears from grounded reality." },
  { id: 9, section_id: "C", category: "Thoughts & Self-Perception", category_badge: "🟨 C. Thoughts & Self-Perception", question: "How does the way you talk to yourself affect your motivation, determination, and ability to keep going when things get difficult?", hint: "Does your inner monologue give you courage, or does it leave you drained?" },

  // 🟩 Category D: Past Experiences & Personal Growth
  { id: 10, section_id: "D", category: "Past & Personal Growth", category_badge: "🟩 D. Past Experiences & Growth", question: "In what ways do you think your past has shaped your personality, beliefs, or the way you see life?", hint: "Reflect on formative events, upbringing, or challenges that strengthened you." },
  { id: 11, section_id: "D", category: "Past & Personal Growth", category_badge: "🟩 D. Past Experiences & Growth", question: "Do you still feel the impact of any important or difficult experiences from your past today?", hint: "Consider whether past echoes trigger caution, hypervigilance, or resilience today." },
  { id: 12, section_id: "D", category: "Past & Personal Growth", category_badge: "🟩 D. Past Experiences & Growth", question: "Is there a memory from your childhood that still affects you emotionally today?", hint: "Share whatever feels comfortable and safe to reflect upon." },

  // 🟧 Category E: Beliefs, Relationships & Social Connection
  { id: 13, section_id: "E", category: "Beliefs & Relationships", category_badge: "🟧 E. Beliefs & Relationships", question: "How does the way you see your own worth and your ability to give or receive love affect your emotional well-being?", hint: "Reflect on whether accepting warmth and love feels comforting or difficult." },
  { id: 14, section_id: "E", category: "Beliefs & Relationships", category_badge: "🟧 E. Beliefs & Relationships", question: "How do your past relationships—both good and bad—affected the way you trust and connect with people today?", hint: "Reflect on emotional safety, boundaries, and openness with others." },
  { id: 15, section_id: "E", category: "Beliefs & Relationships", category_badge: "🟧 E. Beliefs & Relationships", question: "When two of your beliefs seem to conflict with each other, how do you usually find a sense of balance?", hint: "e.g. striving for perfection vs granting yourself grace." },

  // 🟫 Category F: Healthy Habits & Lifestyle
  { id: 16, section_id: "F", category: "Habits & Lifestyle", category_badge: "🟫 F. Healthy Habits & Lifestyle", question: "How do you make sure you get enough sleep, and how important is sleep in your daily routine?", hint: "Reflect on your sleep schedule, nighttime wind-down, and waking energy." },
  { id: 17, section_id: "F", category: "Habits & Lifestyle", category_badge: "🟫 F. Healthy Habits & Lifestyle", question: "When you face setbacks or find it difficult to maintain your healthy habits, how do you usually respond?", hint: "Do you feel guilty, take a patient pause, or rebuild step by step?" },
  { id: 18, section_id: "F", category: "Habits & Lifestyle", category_badge: "🟫 F. Healthy Habits & Lifestyle", question: "What do you do to maintain a healthy balance between work, studies, responsibilities, and personal time? How does this balance affect how you feel?", hint: "Reflect on boundaries between obligations and personal restoration." },

  // 🟥 Category G: Future, Purpose & Resilience
  { id: 19, section_id: "G", category: "Future & Resilience", category_badge: "🟥 G. Future, Purpose & Resilience", question: "How do you deal with uncertainty or not knowing exactly what the future holds?", hint: "Reflect on your balance between planning and trusting your ability to adapt." },
  { id: 20, section_id: "G", category: "Future & Resilience", category_badge: "🟥 G. Future, Purpose & Resilience", question: "How do you make sure that the future you’re planning for will actually make you feel fulfilled and satisfied?", hint: "Reflect on living true to your personal values, passions, and relationships." }
];
