# Technical defense practice

## 1. How does RAG retrieve university information and generate supported responses?

**Suggested speaker: Kamryn Schmidt**

“We store excerpts from the Registrar page with a title and URL. At question time, MiniLM encodes the question. We compare it with normalized passage vectors and give the top three labeled excerpts to the local Llama 3.2 model. The prompt directs the model to use that evidence and cite the numbered passages. The Hub checks that the referenced numbers point to displayed sources. A matching number still needs a human check that the passage supports the claim. On the checkpoint machine, we showed the retrieved excerpts because Ollama was unavailable.”

## 2. Why use Streamlit and modular Python integrations?

**Suggested speaker: Rhaiyn Newby**

“The team already had separate Python engines. Streamlit gave us forms, tables, and temporary session state, so I could connect the engines in one app and keep the same request and appointment workflows. The audit still decides degree eligibility, the scheduling team’s checker still validates schedules, and the recommendation engine still ranks electives. We load optional model and solver code only when needed. That lets us show a greedy schedule or actual excerpts when one dependency is unavailable.”

## 3. What do the three retrieval approaches reveal?

**Suggested speaker: Jarren Woodward**

“We asked the same five questions against 11 passages and took up to three results per question. Keyword overlap counts shared words. BM25 adjusts for word rarity and passage length. MiniLM compares question and passage vectors. All three found every expected term for four questions, and all averaged 90 percent coverage. Each missed the exact word ‘hold’ on the fifth question. The corpus uses ‘holds’ in some passages and the metric matches whole terms. A paragraph can contain the right words and still fail to answer the question. We'd ask reviewers to label supporting passages before reporting recall or reciprocal rank.”
