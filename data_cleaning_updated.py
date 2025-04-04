import json
from openai import OpenAI
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential
import time

# Initialize DeepSeek client
client = OpenAI(api_key="**********", base_url="https://api.deepseek.com")
data = json.load(open("data.json", "r", encoding="utf-8"))

# ================== OPTIMIZED PROMPT (NO PMIDs) ==================
SYSTEM_PROMPT = """You are a doctor generating clear, patient-friendly Q&A pairs. Follow these rules:
1. **Questions**: Phrase as a natural patient concern (e.g., "Can X help with Y?").
2. **Answers**: 
   - Start with a direct yes/no/maybe if applicable.
   - Explain the reasoning simply (e.g., "This works because...").
   - Provide actionable advice (e.g., "For best results, do Z").
   - Do NOT cite studies or PMIDs.
3. Format strictly as:
Q: [question]
A: [answer]"""

USER_PROMPT_TEMPLATE = """
Generate 3 questions patients might ask about {topic_name}, with clear answers from this context:
{context}

Example:
Q: Can granola bars lower cholesterol?
A: Yes, because they contain soluble fiber that helps remove cholesterol from your body. For best results, choose bars with whole oats and less than 5g of added sugar per serving.
"""

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
def generate_qa(topic_name, content):
    """Generate 3 QA pairs without PMIDs."""
    sentences = set()
    for pmid_sents in content["distant_exact_sentences"].values():
        sentences.update(pmid_sents)
    context = " ".join(sentences)[:3000]  # Truncate long text

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                topic_name=topic_name,
                context=context
            )}
        ],
        temperature=0.3  # Keep answers factual
    )
    return parse_qa(response.choices[0].message.content, topic_name)

def parse_qa(raw_text, topic_name):
    """Convert LLM output to structured QA pairs (cleans PMIDs)."""
    qa_pairs = []
    current_q = None
    for line in raw_text.split("\n"):
        line = line.strip()
        if line.startswith("Q:"):
            current_q = line[2:].strip()
        elif line.startswith("A:") and current_q:
            answer = line[2:].strip()
            # Remove any remaining PMID-like references
            answer = " ".join(word for word in answer.split() if not word.startswith("[PMID:"))
            qa_pairs.append({
                "topic": topic_name,
                "question": current_q,
                "answer": answer,
                "source": f"Generated from {topic_name}"
            })
            current_q = None
    return qa_pairs

# # ===== TEST MODE: Run on first 3 topics =====
# test_topics = dict(list(data.items())[:3])  # Test on 3 topics
# all_qa = []
# for topic_name, content in tqdm(test_topics.items(), desc="Generating QA"):
#     try:
#         all_qa.extend(generate_qa(topic_name, content))
#     except Exception as e:
#         print(f"⚠️ Failed on {topic_name}: {str(e)}")
#
# # Save clean results
# with open("health_qa_clean.json", "w", encoding="utf-8") as f:
#     json.dump(all_qa, f, indent=2, ensure_ascii=False)
#
# print(f"✅ Generated {len(all_qa)} clean QA pairs (test mode)!")



# ===== PROCESS ALL TOPICS =====
all_qa = []
failed_topics = []

for topic_name, content in tqdm(data.items(), desc="Generating QA Pairs"):
    try:
        all_qa.extend(generate_qa(topic_name, content))
        time.sleep(1)  # Rate limiting to avoid API overload
    except Exception as e:
        failed_topics.append(topic_name)
        print(f"⚠️ Failed on {topic_name}: {str(e)}")
        continue

# Save results
with open("health_qa_full_dataset.json", "w", encoding="utf-8") as f:
    json.dump(all_qa, f, indent=2, ensure_ascii=False)

# Generate report
print(f"\n✅ Successfully generated {len(all_qa)} QA pairs from {len(data)} topics!")
print(f"⚠️ Failed on {len(failed_topics)} topics: {failed_topics}")