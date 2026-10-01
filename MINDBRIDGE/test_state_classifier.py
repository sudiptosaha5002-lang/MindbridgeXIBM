import time
from state_classifier import SupportStateClassifier

def main():
    print("="*80)
    print(" MINDBRIDGE STATE & INTENT ZERO-SHOT CLASSIFIER BENCHMARK ")
    print("="*80)
    
    classifier = SupportStateClassifier()
    
    # 10 Multilingual benchmark examples
    test_cases = [
        "Exam ko leke tension hai but manage kar lunga",
        "পরীক্ষা নিয়ে খুব চিন্তা হচ্ছে, কিছু মাথায় ঢুকছে না",
        "Can you teach me a 1-minute breathing exercise to calm down?",
        "Amar khub eka lagche, keu kotha bolar nei",
        "I want to talk to a doctor or counselor nearby",
        "Hi, how does this app work?",
        "Mujhe bahut akelapan mehsoos ho raha hai aaj kal",
        "khub rag hocche amar ajke",
        "mere dadaji guzar gaye, main bahut udas hu",
        "kya mujhe yahan madad mil sakti hai samajh nahi aa raha"
    ]
    
    # Warmup inference engine
    print("\n[*] Warming up embeddings engine...")
    _ = classifier.classify_support_state("warmup sequence")
    
    results = []
    print("[*] Running Multilingual Benchmarks...\n")
    
    for text in test_cases:
        t0 = time.perf_counter()
        res = classifier.classify_support_state(text)
        latency = (time.perf_counter() - t0) * 1000
        
        results.append({
            "Input": text,
            "Predicted State": res['primary_state'],
            "Predicted Intent": res['primary_intent'],
            "State Conf": res['state_confidence'],
            "Gate": res['confidence_gate'],
            "Latency (ms)": latency
        })
        
    # Print formatted markdown table directly
    print("| Input | Predicted State | Predicted Intent | State Confidence | Gate | Latency (ms) |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        # Truncate text cleanly if too long
        input_trunc = r['Input'] if len(r['Input']) <= 45 else r['Input'][:42] + "..."
        print(f"| {input_trunc} | **{r['Predicted State']}** | {r['Predicted Intent']} | {r['State Conf']:.2%} | {r['Gate']} | {r['Latency (ms)']:.2f} ms |")
        
    avg_lat = sum([r['Latency (ms)'] for r in results]) / len(results)
    print(f"\n[*] Average Latency: {avg_lat:.2f} ms")

if __name__ == "__main__":
    main()
