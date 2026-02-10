# RAG Implementation Guide

Complete technical explanation of Retrieval-Augmented Generation (RAG) system using movie subtitles for context-aware quiz generation.

## Table of Contents
1. [What is RAG?](#what-is-rag)
2. [Why RAG for Madagascar Quiz?](#why-rag-for-madagascar-quiz)
3. [Architecture](#architecture)
4. [Implementation Details](#implementation-details)
5. [Subtitle File Format](#subtitle-file-format)
6. [Vector Embeddings](#vector-embeddings)
7. [Semantic Search](#semantic-search)
8. [Prompt Engineering](#prompt-engineering)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## What is RAG?

**Retrieval-Augmented Generation** combines:
- **Retrieval**: Finding relevant documents/text from a knowledge base
- **Augmentation**: Adding that context to LLM prompts
- **Generation**: LLM generates responses using both training + retrieved context

**Benefits:**
- ✅ Accurate, fact-based responses
- ✅ No hallucinations (LLM can cite sources)
- ✅ Dynamic knowledge (update docs without retraining model)
- ✅ Reduced token costs (only send relevant context)

**Traditional LLM:**
```
User: "What did Marty say to Alex in Madagascar?"
LLM: "I don't know, I wasn't trained on that movie."
```

**RAG-Enhanced LLM:**
```
User: "What did Marty say to Alex in Madagascar?"
RAG System: [Retrieves dialogue: "Marty: I'm 10 years old today!"]
LLM: "Marty told Alex that he's 10 years old today on his birthday."
```

---

## Why RAG for Madagascar Quiz?

### Problem
- LLMs (even 70B) have limited knowledge of specific movie dialogues
- Quiz questions need to be factually accurate
- Cannot retrain model on Madagascar content

### Solution
- Extract all dialogues from movie subtitles
- Embed dialogues into vector space
- Retrieve relevant context for each quiz question
- Inject context into LLM prompt

### Benefits
- **Accuracy**: Questions based on actual movie content
- **Diversity**: 1,064 dialogue lines = rich question variety
- **Freshness**: Can update subtitle file anytime
- **Cost**: Only relevant chunks sent to LLM (saves tokens)

---

## Architecture

### Data Flow

```
┌─────────────────────┐
│ Madagascar.srt      │ (Subtitle file: 1,064 lines)
│ Dialogue lines      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Chunk Dialogues     │ Group 10 lines → 107 chunks
│ (chunk_dialogues)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generate Embeddings │ sentence-transformers
│ (SentenceTransformer│ all-MiniLM-L6-v2 model
│  .encode)           │ 384-dim vectors
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Store Vectors       │ In-memory storage
│ chunks[] + vectors[]│ (107 chunks, 107 embeddings)
└──────────┬──────────┘
           │
           ▼
   [Quiz Question Needed]
           │
           ▼
┌─────────────────────┐
│ Embed Query         │ "Generate quiz question"
│ (SentenceTransformer│
│  .encode)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Cosine Similarity   │ Compare query vector to all chunks
│ (numpy dot product) │ Find top 3 matches
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Retrieve Context    │ Top 3 relevant chunks
│ (get_relevant_      │
│  context)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Build Prompt        │ System + Context + User request
│ (quiz_tutor_call)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ AWS Bedrock LLM     │ Llama 70B generates question
│ (Llama 3.1 70B)     │ Using context from subtitles
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Quiz Question       │ JSON: {question, choices, answer}
│ Based on Movie      │
└─────────────────────┘
```

---

## Implementation Details

### 1. Load Subtitle File

**Function:** `load_srt_file(filepath)`

```python
def load_srt_file(filepath):
    """Parse SRT subtitle file, extract dialogue lines."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by subtitle blocks (separated by blank lines)
    blocks = content.strip().split('\n\n')
    
    dialogues = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # Line 1: Index (1, 2, 3...)
            # Line 2: Timestamp (00:00:01,000 --> 00:00:03,000)
            # Line 3+: Dialogue text
            dialogue = ' '.join(lines[2:])
            
            # Clean HTML tags, speaker names
            dialogue = re.sub(r'<[^>]+>', '', dialogue)  # Remove <i>, <b>, etc.
            dialogue = re.sub(r'^\w+:', '', dialogue)    # Remove "MARTY:"
            dialogue = dialogue.strip()
            
            if dialogue and len(dialogue) > 3:
                dialogues.append(dialogue)
    
    return dialogues
```

**Example Output:**
```python
[
    "I'm 10 years old today! Can you believe it?",
    "Alex, do you ever wonder what's out there?",
    "I can't just ship him off to the wild.",
    ...
]
# Total: 1,064 dialogues
```

### 2. Chunk Dialogues

**Function:** `chunk_dialogues(dialogues, chunk_size=10)`

```python
def chunk_dialogues(dialogues, chunk_size=10):
    """Group dialogues into chunks for better context."""
    chunks = []
    for i in range(0, len(dialogues), chunk_size):
        chunk = dialogues[i:i + chunk_size]
        chunk_text = '\n'.join(chunk)
        chunks.append(chunk_text)
    
    return chunks
```

**Why Chunk?**
- Single dialogue line too short (5-20 words)
- Chunk provides context (scene, conversation flow)
- 10 lines = ~100-200 words (optimal for embeddings)

**Example Chunk:**
```
I'm 10 years old today!
Happy birthday, Marty!
Alex, do you ever wonder what's out there?
Out where?
You know, out there. Beyond the zoo.
What are you talking about?
The wild, Alex. Don't you ever think about the wild?
I'm a zoo animal. The zoo is my home.
But we're from the wild originally.
That was like a million years ago.
```

**Stats:**
- Input: 1,064 dialogues
- Output: 107 chunks (10 lines each, last chunk has 4 lines)

### 3. Generate Embeddings

**Function:** `initialize_rag(subtitle_path)`

```python
from sentence_transformers import SentenceTransformer

def initialize_rag(subtitle_path):
    """Load subtitles, generate embeddings."""
    # Load model (downloads automatically on first run)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # Model: 90MB, 384-dimensional embeddings
    
    # Load and chunk dialogues
    dialogues = load_srt_file(subtitle_path)
    chunks = chunk_dialogues(dialogues, chunk_size=10)
    
    # Generate embeddings for all chunks
    embeddings = model.encode(chunks, show_progress_bar=True)
    # Output: numpy array (107, 384)
    
    return chunks, embeddings, model
```

**Embedding Model: all-MiniLM-L6-v2**
- Size: 90MB
- Dimensions: 384
- Speed: ~1000 sentences/second on CPU
- Quality: Good for semantic similarity
- Trained on: 1 billion sentence pairs

**Example Embedding:**
```python
chunk = "I'm 10 years old today! Happy birthday, Marty!"
embedding = model.encode([chunk])[0]
# Output: [0.042, -0.123, 0.567, ..., 0.891]  (384 numbers)
```

### 4. Semantic Search

**Function:** `get_relevant_context(query, chunks, embeddings, model, top_k=3)`

```python
import numpy as np

def get_relevant_context(query, chunks, embeddings, model, top_k=3):
    """Find most relevant chunks using cosine similarity."""
    # Embed the query
    query_embedding = model.encode([query])[0]
    # Output: (384,)
    
    # Normalize vectors for cosine similarity
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    # Compute cosine similarity
    similarities = np.dot(embeddings_norm, query_norm)
    # Output: (107,) - similarity score for each chunk
    
    # Get top K indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    # Sort descending, take first 3
    
    # Retrieve top chunks
    top_chunks = [chunks[i] for i in top_indices]
    
    return '\n\n---\n\n'.join(top_chunks)
```

**Cosine Similarity:**
```
cos(A, B) = (A · B) / (||A|| × ||B||)

Range: -1 to 1
- 1.0: Identical vectors (perfect match)
- 0.0: Orthogonal (unrelated)
- -1.0: Opposite (very different)
```

**Example Search:**
```python
query = "What did Marty say about his age?"

# Similarity scores:
# Chunk 1 (contains "I'm 10 years old"): 0.87
# Chunk 5 (contains "birthday"): 0.72
# Chunk 23 (random dialogue): 0.15
# ...

# Returns top 3:
# Chunk 1, Chunk 5, Chunk 12
```

---

## Subtitle File Format

### SRT Format Specification

```
1
00:00:01,000 --> 00:00:03,500
I'm 10 years old today!

2
00:00:03,600 --> 00:00:05,200
Happy birthday, Marty!

3
00:00:05,300 --> 00:00:08,000
<i>Alex, do you ever wonder
what's out there?</i>

...
```

**Structure:**
- **Line 1**: Sequence number (1, 2, 3...)
- **Line 2**: Timestamp (HH:MM:SS,mmm --> HH:MM:SS,mmm)
- **Line 3+**: Dialogue text (may span multiple lines)
- **Blank line**: Separator between subtitles

### Where to Get Subtitles

**Option 1: Download**
```bash
# OpenSubtitles.org (requires account)
# Subscene.com
# YIFY-subtitles.com

# Search for: "Madagascar 2005 English subtitles"
# Download .srt file
# Place in: /mnt/nvme/adrian/ChatBotRobot/data/Madagascar.srt
```

**Option 2: Extract from Video**
```bash
# Install ffmpeg
sudo apt install ffmpeg

# Extract subtitles
ffmpeg -i Madagascar.mkv -map 0:s:0 Madagascar.srt

# -map 0:s:0 = first subtitle stream
```

**Option 3: Use Sample**
```bash
# For testing, create small sample:
cat > data/test_subtitles.srt << 'EOF'
1
00:00:01,000 --> 00:00:03,000
I'm 10 years old today!

2
00:00:03,500 --> 00:00:05,000
Happy birthday, Marty!

3
00:00:05,500 --> 00:00:08,000
Alex, do you ever wonder what's out there?
EOF

# Use with --subtitle flag:
python3 voice_chat_riva_aws.py --subtitle data/test_subtitles.srt --rag
```

---

## Vector Embeddings

### What Are Embeddings?

**Definition:** Vector representation of text that captures semantic meaning.

**Example:**
```
"dog" → [0.2, 0.8, -0.3, 0.5, ...]  (384 numbers)
"puppy" → [0.18, 0.82, -0.28, 0.52, ...]  (very similar)
"car" → [-0.5, 0.1, 0.9, -0.2, ...]  (very different)
```

**Properties:**
- Similar words have similar vectors
- Can do math: `king - man + woman ≈ queen`
- Enables semantic search (meaning-based, not keyword-based)

### Sentence-BERT Model

**all-MiniLM-L6-v2:**
- **Size**: 90MB (lightweight)
- **Dimensions**: 384
- **Architecture**: BERT with mean pooling
- **Training**: Contrastive learning on sentence pairs
- **Performance**: 0.89 correlation with human similarity judgments

**Why This Model?**
- ✅ Fast (can run on Jetson CPU)
- ✅ Good quality (better than TF-IDF, Word2Vec)
- ✅ Pre-trained (no training needed)
- ✅ Multilingual support available

**Alternatives:**
- `all-mpnet-base-v2` (768-dim, slower, better quality)
- `all-distilroberta-v1` (768-dim, balanced)
- `paraphrase-MiniLM-L6-v2` (similar to all-MiniLM)

### Memory Usage

**Storage:**
```
107 chunks × 384 dimensions × 4 bytes (float32) = 164KB
Model weights: 90MB
Total RAM: ~100MB
```

**Very efficient!** Can store millions of chunks on Jetson.

---

## Semantic Search

### Cosine Similarity Explained

**Intuition:** Angle between two vectors in high-dimensional space.

**Geometric Interpretation:**
```
      A (dog)
     /
    /  θ = 15°
   /___________B (puppy)
   cos(15°) = 0.97 (very similar)

      A (dog)
      |
      |  θ = 90°
      |___________C (car)
   cos(90°) = 0.0 (unrelated)
```

**Formula:**
```python
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

**Optimized (batch):**
```python
# Normalize once
a_norm = a / np.linalg.norm(a)
B_norm = B / np.linalg.norm(B, axis=1, keepdims=True)

# Dot product = cosine similarity (since normalized)
similarities = np.dot(B_norm, a_norm)
```

### Performance

**On Jetson Xavier:**
- Embedding generation: ~0.1s per chunk (CPU)
- Similarity computation: <0.001s for 107 chunks
- Total RAG overhead: ~0.1s per query (negligible)

**Scalability:**
- 1,000 chunks: <0.01s
- 10,000 chunks: <0.1s
- 100,000 chunks: ~1s (consider FAISS)

---

## Prompt Engineering

### Quiz Question Generation

**Without RAG:**
```python
prompt = f"""Generate a quiz question about Madagascar movie.
Question should be for a {difficulty} difficulty level.

Return JSON:
{{
  "question": "...",
  "choices": ["A", "B", "C", "D"],
  "answer": "A"
}}"""
```

**Result:** Generic questions, often incorrect facts.

**With RAG:**
```python
# 1. Get relevant context
context = get_relevant_context(
    query="Generate quiz question about Madagascar",
    chunks=chunks,
    embeddings=embeddings,
    model=model,
    top_k=3
)

# 2. Build enhanced prompt
prompt = f"""You are Buzz Lightyear creating a quiz for Adrian.

CONTEXT (from Madagascar movie):
---
{context}
---

Generate a {difficulty} difficulty quiz question BASED ON THE CONTEXT ABOVE.
Use actual dialogue and events from the context.

Return JSON:
{{
  "question": "...",
  "choices": ["A", "B", "C", "D"],
  "answer": "A"
}}"""
```

**Result:** Accurate, fact-based questions from actual movie content.

### Context Example

**Query:** "Generate quiz question about Marty's birthday"

**Retrieved Context:**
```
I'm 10 years old today!
Happy birthday, Marty!
Alex, do you ever wonder what's out there?
Out where?
You know, out there. Beyond the zoo.

---

This is the best birthday ever!
You're the best friend a zebra could ask for.
Happy birthday, buddy.
Thanks, Alex.

---

Marty, you can't just run away!
But I want to see the wild, Alex!
```

**Generated Question:**
```json
{
  "question": "How old did Marty turn on his birthday in the movie?",
  "choices": [
    "8 years old",
    "10 years old",
    "12 years old",
    "5 years old"
  ],
  "answer": "10 years old"
}
```

**Notice:** Question directly references context (age 10).

---

## Performance Optimization

### 1. Cache Embeddings

```python
# Don't re-embed chunks every time
# Embed once during initialization

# Bad (slow):
for i in range(100):
    chunks, embeddings, model = initialize_rag(subtitle_path)  # Re-embeds each time

# Good (fast):
chunks, embeddings, model = initialize_rag(subtitle_path)  # Embed once
for i in range(100):
    context = get_relevant_context(query, chunks, embeddings, model)  # Reuse embeddings
```

### 2. Batch Encoding

```python
# Bad (slow):
embeddings = []
for chunk in chunks:
    emb = model.encode([chunk])
    embeddings.append(emb)

# Good (fast):
embeddings = model.encode(chunks)  # Batch encode all chunks
```

### 3. Top-K Selection

```python
# Don't sort all, just get top K
top_indices = np.argpartition(similarities, -top_k)[-top_k:]  # Faster than sort
# But np.argsort is fine for 107 chunks
```

### 4. GPU Acceleration (Optional)

```python
# Use GPU for embeddings (if available)
model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')

# Check:
print(model.device)  # Should show: cuda:0
```

**Note:** For 107 chunks, CPU is fast enough. GPU helps for 10,000+ chunks.

---

## Troubleshooting

### Issue: Model Download Fails

**Error:** `OSError: Can't load model 'all-MiniLM-L6-v2'`

**Solution:**
```bash
# Download manually
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Models saved to: ~/.cache/torch/sentence_transformers/
```

### Issue: Out of Memory

**Error:** `RuntimeError: CUDA out of memory`

**Solutions:**
```bash
# 1. Use CPU
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

# 2. Reduce chunk size
chunks = chunk_dialogues(dialogues, chunk_size=5)  # Smaller chunks

# 3. Reduce top_k
context = get_relevant_context(query, chunks, embeddings, model, top_k=1)
```

### Issue: Poor Search Results

**Problem:** Retrieved context not relevant

**Solutions:**
```python
# 1. Increase chunk size (more context)
chunks = chunk_dialogues(dialogues, chunk_size=15)

# 2. Increase top_k
context = get_relevant_context(query, chunks, embeddings, model, top_k=5)

# 3. Better query
# Bad query:
query = "quiz question"
# Good query:
query = "Generate quiz question about Marty's birthday and his desire to see the wild"

# 4. Try different embedding model
model = SentenceTransformer('all-mpnet-base-v2')  # Better quality, slower
```

### Issue: Subtitle Parsing Errors

**Error:** `IndexError: list index out of range`

**Solution:**
```python
# Add error handling in load_srt_file
for block in blocks:
    try:
        lines = block.split('\n')
        if len(lines) >= 3:
            dialogue = ' '.join(lines[2:])
            # ... process dialogue
    except Exception as e:
        print(f"Skipping block: {e}")
        continue
```

### Issue: Duplicate Questions

**Problem:** RAG always returns same chunks

**Solutions:**
```python
# 1. Add randomness to query
import random
query = f"Generate {difficulty} quiz question about {random.choice(['characters', 'events', 'dialogues', 'plot'])}"

# 2. Exclude previously used chunks
used_chunks = set()

def get_relevant_context(query, chunks, embeddings, model, top_k=3, exclude=set()):
    similarities = np.dot(embeddings_norm, query_norm)
    
    # Mask out excluded chunks
    for idx in exclude:
        similarities[idx] = -1
    
    top_indices = np.argsort(similarities)[::-1][:top_k]
    return top_chunks, top_indices

# Update exclude set
context, used_indices = get_relevant_context(query, chunks, embeddings, model, exclude=used_chunks)
used_chunks.update(used_indices)
```

---

## Advanced Topics

### 1. Hybrid Search (Keyword + Semantic)

```python
def hybrid_search(query, chunks, embeddings, model, top_k=3, alpha=0.5):
    """Combine semantic similarity + keyword matching."""
    # Semantic similarity
    query_emb = model.encode([query])[0]
    semantic_scores = np.dot(embeddings_norm, query_emb / np.linalg.norm(query_emb))
    
    # Keyword matching (TF-IDF)
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(chunks)
    query_tfidf = vectorizer.transform([query])
    keyword_scores = (tfidf_matrix * query_tfidf.T).toarray().flatten()
    
    # Combine scores
    combined = alpha * semantic_scores + (1 - alpha) * keyword_scores
    top_indices = np.argsort(combined)[::-1][:top_k]
    
    return [chunks[i] for i in top_indices]
```

### 2. FAISS for Large-Scale Search

```python
# For 100,000+ chunks, use FAISS
import faiss

# Build index
index = faiss.IndexFlatIP(384)  # Inner product (cosine similarity)
index.add(embeddings_norm)  # Add all embeddings

# Search
query_emb = model.encode([query])[0]
query_norm = query_emb / np.linalg.norm(query_emb)
D, I = index.search(query_norm.reshape(1, -1), top_k)  # Distances, Indices

# D[0]: similarity scores
# I[0]: chunk indices
```

### 3. Metadata Filtering

```python
# Add metadata to chunks
chunks_metadata = [
    {"text": "I'm 10 years old!", "timestamp": "00:00:01", "speaker": "Marty"},
    {"text": "Happy birthday!", "timestamp": "00:00:03", "speaker": "Alex"},
    ...
]

# Filter before search
def filtered_search(query, chunks_metadata, embeddings, model, speaker="Marty"):
    # Get indices where speaker matches
    valid_indices = [i for i, meta in enumerate(chunks_metadata) if meta["speaker"] == speaker]
    
    # Search only valid chunks
    valid_embeddings = embeddings[valid_indices]
    similarities = np.dot(valid_embeddings_norm, query_norm)
    
    # Map back to original indices
    top_k_in_valid = np.argsort(similarities)[::-1][:3]
    top_k_original = [valid_indices[i] for i in top_k_in_valid]
    
    return [chunks_metadata[i]["text"] for i in top_k_original]
```

---

## Evaluation Metrics

### Retrieval Quality

```python
# Manual evaluation
test_queries = [
    "What did Marty say about his age?",
    "What animals are in the zoo?",
    "Where did they end up?",
]

for query in test_queries:
    context = get_relevant_context(query, chunks, embeddings, model, top_k=3)
    print(f"Query: {query}")
    print(f"Context: {context[:200]}...")
    print("Is relevant? (y/n): ")
    # Manual check

# Compute:
# - Precision: % of retrieved chunks that are relevant
# - Recall: % of relevant chunks that were retrieved
# - MRR (Mean Reciprocal Rank): 1/rank of first relevant result
```

---

## Additional Resources

- [Sentence-BERT Paper](https://arxiv.org/abs/1908.10084)
- [Sentence-Transformers Docs](https://www.sbert.net/)
- [RAG Paper](https://arxiv.org/abs/2005.11401)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)

---

**Next:** Test the full system with `python3 voice_chat_riva_aws.py --mode madagascar_quiz --llm llama70b --rag`
