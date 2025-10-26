# 🧠 Memory vs LLM Indicators - User Guide

## What You See in the Chat

Every bot response now shows **where the information came from**:

### 🧠 **Blue Badge: "Used X past messages from Cortex Memory"**

```
┌─────────────────────────────────────────────┐
│ AI Assistant                                │
│ The prices of Honda cars vary depending... │
│                                             │
│ 🧠 Used 3 past messages from Cortex Memory │
│ Retrieved: 1. You: "whats the price..."    │
│            2. Bot: "The prices..."          │
│            3. You: "whats the price..."     │
└─────────────────────────────────────────────┘
```

**This means:**
- ✅ Cortex SDK **searched your conversation history**
- ✅ Found **3 relevant past messages**
- ✅ Passed them to the LLM for context
- ✅ LLM generated response **using this context**

**Flow:**
```
Your Question → Cortex Memory Search → Found Past Messages → LLM (with context) → Response
```

---

### 💭 **Orange Badge: "Fresh LLM response (no memory used)"**

```
┌─────────────────────────────────────────────┐
│ AI Assistant                                │
│ Hello! How can I help you today?           │
│                                             │
│ 💭 Fresh LLM response (no memory used)     │
└─────────────────────────────────────────────┘
```

**This means:**
- ❌ No conversation history found
- ❌ First message in session OR unrelated question
- ✅ LLM generated response **without context**

**Flow:**
```
Your Question → Cortex Memory Search → No Match → LLM (no context) → Response
```

---

## 🔍 Real Example from Your Chat

### Example 1: Memory Recall Working

**You asked twice:** "whats the price of honda car"

**First time:**
- Badge: 🧠 **1 memory context recalled**
- Retrieved: Your initial question (user message)
- LLM used this to understand you're asking about prices

**Second time:**
- Badge: 🧠 **3 memory contexts recalled**
- Retrieved: 
  1. Your first "whats the price of honda car" question
  2. Bot's first response about $20,000 to $30,000
  3. Your second identical question
- LLM recognized you asked the same question and provided consistent answer

---

## 📊 What Each Part Means

### 1. **Memory Source (Blue Badge)**
```
🧠 Used 3 past messages from Cortex Memory
```
- **"3"** = Number of past messages retrieved
- **"from Cortex Memory"** = Retrieved from SDK's semantic search
- **Blue color** = Memory was used

### 2. **Retrieved Details**
```
Retrieved: 1. You: "whats the price of honda car..."
           2. Bot: "The prices of Honda cars..."
           3. You: "whats the price of honda car..."
```
- Shows **which past messages** were sent to LLM
- **"You"** = Your previous questions
- **"Bot"** = Previous bot responses
- **Truncated to 40 chars** for readability

### 3. **The Response Above**
```
The prices of Honda cars vary depending on the model...
```
- This is the **LLM's output**
- Generated using the retrieved context
- LLM = Llama-2-7B model

---

## 🎯 Why This Matters

### Without Memory (Orange Badge):
```
You: "What's my name?"
Bot: "I don't know your name." 💭 Fresh response
```

### With Memory (Blue Badge):
```
You: "My name is Alice"
Bot: "Nice to meet you, Alice!" 🧠 1 memory

[Later...]
You: "What's my name?"
Bot: "Your name is Alice." 🧠 2 memories (recalled both messages)
```

---

## 🧪 Test It Yourself

### Test 1: Build Context
```bash
# Message 1
You: "My favorite color is blue"
Bot: [response] 🧠 1 memory

# Message 2
You: "I love programming in Python"
Bot: [response] 🧠 2 memories

# Message 3 - Ask about earlier info
You: "What's my favorite color?"
Bot: "Your favorite color is blue" 🧠 3-4 memories ✓
```

### Test 2: Semantic Search
```bash
# Tell the bot something
You: "I work at Google"
Bot: [response] 🧠 1 memory

# Ask in different ways - all should recall "Google"
You: "Where do I work?"        → 🧠 2 memories (should mention Google)
You: "What's my company?"      → 🧠 3 memories (should mention Google)
You: "My workplace?"           → 🧠 4 memories (should mention Google)
```

### Test 3: New Session (No Memory)
```bash
# Open new browser tab or clear session
You: "What's my name?"
Bot: "I don't know your name" 💭 Fresh response (correct!)
```

---

## 🔧 Technical Details

### Data Flow:

```
┌─────────────┐
│ Your Message│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Cortex SDK      │
│ Semantic Search │  ← Searches past messages using embeddings
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Retrieved       │
│ Past Messages   │  ← 0 to 10 most relevant messages
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Llama-2-7B LLM  │  ← Generates response with context
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Bot Response    │
│ + Memory Badge  │  ← Shows memory indicator
└─────────────────┘
```

### Memory Storage:
- **Stored in:** Cortex SDK Short-term Memory
- **Capacity:** 1000 messages per session
- **TTL:** 1 day (messages expire after 24 hours)
- **Search:** Semantic (meaning-based, not keyword-based)
- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2

---

## 📝 Summary

| Indicator | Color | Meaning | Source |
|-----------|-------|---------|--------|
| 🧠 **X past messages from Cortex Memory** | Blue | Used conversation history | Cortex Memory → LLM |
| 💭 **Fresh LLM response** | Orange | No history used | LLM only |

**Key Takeaway:**
- **Blue Badge** = Response used your conversation history (Cortex Memory is working!)
- **Orange Badge** = Response is fresh, no prior context

---

## 🎉 Benefits

1. **Transparency** - You see exactly what context was used
2. **Debugging** - Easy to verify Cortex SDK is working
3. **Trust** - Understand how the bot "remembers" things
4. **Learning** - See how semantic search finds relevant context

---

**Questions?** Check the response badges to understand where each answer comes from!

