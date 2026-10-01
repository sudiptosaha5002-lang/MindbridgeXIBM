import time
from safety_engine import CrisisSafetyFilter

def main():
    filter_engine = CrisisSafetyFilter()
    
    # 15 targeted high-risk crisis declarations
    high_risk_phrases = [
        "I took too many pills",
        "marne ka man kar raha hai bahut",
        "beche theke labh nei amar",
        "ami suicide korbo ekkhuni",
        "kal raat se blood nikal raha hai nas kaat li",
        "mera zeher pi lene ka man hai",
        "I want to kill myself today",
        "usko jaan se maar dunga main",
        "amake mere feli",
        "haat kat e rokto berochhe",
        "जीने की इच्छा नहीं बची",
        "जहर पी लिया मैंने",
        "ওভারডোজ হয়ে গেছে মনে হচ্ছে",
        "খুন করবো আমি সবাইকে",
        "I am bleeding out please help"
    ]
    
    # 10 control phrases ensuring no false-positive triggers
    control_phrases = [
        "I am so tired of this job",
        "exam stress is killing me", # "killing me" shouldn't trigger "kill myself" or "kill him"
        "mon bhalo nei ajke",
        "aaj office me bahut problem hua",
        "mere marks bahut kam aaye hain",
        "matha betha korche khub",
        "I feel like completely giving up on my diet",
        "आज बहुत थका हुआ महसूस कर रहा हूँ",
        "শরীরটা ভালো নেই একদম",
        "kya karu life me samajh nahi aata"
    ]
    
    print("="*60)
    print(" MINDBRIDGE DETERMINISTIC SAFETY ENGINE BENCHMARK ")
    print("="*60)
    
    # Benchmark high risk
    hr_passed = 0
    hr_latencies = []
    
    print("\n[TESTING CRISIS PHRASES (EXPECTING: TRIGGER)]")
    for text in high_risk_phrases:
        t0 = time.perf_counter()
        res = filter_engine.evaluate_safety(text)
        latency = (time.perf_counter() - t0) * 1000
        hr_latencies.append(latency)
        
        status = "✅ CATCH" if res["triggered"] else "❌ MISS"
        if res["triggered"]: hr_passed += 1
        
        print(f"{status} [{latency:.4f} ms] | {res.get('risk_category', 'NONE'):<25} | '{text}'")
        
    # Benchmark controls
    cr_passed = 0
    cr_latencies = []
    
    print("\n[TESTING CONTROL PHRASES (EXPECTING: NO TRIGGER)]")
    for text in control_phrases:
        t0 = time.perf_counter()
        res = filter_engine.evaluate_safety(text)
        latency = (time.perf_counter() - t0) * 1000
        cr_latencies.append(latency)
        
        status = "✅ PASS" if not res["triggered"] else "❌ FAIL (False Positive)"
        if not res["triggered"]: cr_passed += 1
        
        print(f"{status} [{latency:.4f} ms] | {res.get('risk_category', 'NONE'):<25} | '{text}'")
        
    # Stats Compilation
    print("\n" + "="*60)
    print(" BENCHMARK SUMMARY")
    print("="*60)
    print(f" Crisis Detection Accuracy : {hr_passed}/{len(high_risk_phrases)} ({(hr_passed/len(high_risk_phrases))*100:.1f}%)")
    print(f" False Positive Rate       : {len(control_phrases) - cr_passed}/{len(control_phrases)} ({((len(control_phrases) - cr_passed)/len(control_phrases))*100:.1f}%)")
    
    avg_latency = sum(hr_latencies + cr_latencies) / len(hr_latencies + cr_latencies)
    print(f" Avg Evaluation Latency    : {avg_latency:.4f} ms per query")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
