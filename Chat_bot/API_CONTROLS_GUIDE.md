# 🎛️ API Controls Guide

## ✅ **NEW! Real-Time API Toggle Controls**

You now have **full control** over the chatbot's behavior through toggle switches in the UI!

---

## 🎯 **Three API Controls:**

### 1. 🧠 **Memory Context (Semantic Search)**
**What it does:** Controls whether the bot uses past conversation context
- ✅ **ON**: Bot remembers and uses past messages for better responses
- ❌ **OFF**: Bot ignores past context, treats each message independently

**Example:**
```
Memory Context ON:  "What's my name?" → "Your name is Alice" (remembers)
Memory Context OFF: "What's my name?" → "I don't know your name" (forgets)
```

---

### 2. ⚡ **Answer Caching (Instant Responses)**
**What it does:** Controls whether identical questions get instant cached answers
- ✅ **ON**: Identical questions get instant responses (no LLM call)
- ❌ **OFF**: Every question goes to LLM (slower but always fresh)

**Example:**
```
Answer Cache ON:  "Price of Honda?" → Instant cached answer ⚡
Answer Cache OFF: "Price of Honda?" → LLM generates new answer (5-8s)
```

---

### 3. 💭 **Fresh LLM (Always Generate)**
**What it does:** Controls whether the LLM generates responses
- ✅ **ON**: LLM generates intelligent responses
- ❌ **OFF**: Returns simple fallback message

**Example:**
```
Fresh LLM ON:  "How are you?" → "I'm doing well, thank you for asking!"
Fresh LLM OFF: "How are you?" → "I'm currently in a limited mode..."
```

---

## 🧪 **Testing Scenarios:**

### Scenario 1: **Memory Context Testing**
```
1. Turn ON Memory Context
2. Say: "My name is Alice"
3. Ask: "What's my name?"
4. Result: "Alice" (remembers!)

5. Turn OFF Memory Context  
6. Ask: "What's my name?"
7. Result: "I don't know" (forgets!)
```

### Scenario 2: **Answer Caching Testing**
```
1. Turn ON Answer Caching
2. Ask: "Price of Honda?"
3. Wait 8 seconds for LLM response
4. Ask SAME: "Price of Honda?"
5. Result: Instant cached answer! ⚡

6. Turn OFF Answer Caching
7. Ask: "Price of Honda?" (again)
8. Result: LLM generates new response (5-8s)
```

### Scenario 3: **Fresh LLM Testing**
```
1. Turn OFF Fresh LLM
2. Ask: "How are you?"
3. Result: "I'm currently in a limited mode..."

4. Turn ON Fresh LLM
5. Ask: "How are you?"
6. Result: Full intelligent response!
```

---

## 🔧 **How It Works:**

### **Frontend (UI):**
- Toggle switches send `api_settings` with each message
- Real-time control without page refresh
- Visual feedback with toggle states

### **Backend (API):**
- Receives `api_settings` in `/chat` endpoint
- Passes settings to `generate_response()` method
- Respects each toggle independently

### **Chatbot Logic:**
- **Memory Context**: Controls `use_semantic_context` parameter
- **Answer Caching**: Controls `use_answer_cache` parameter  
- **Fresh LLM**: Controls `use_fresh_llm` parameter

---

## 📊 **Response Indicators:**

The UI shows **exactly** what happened:

| Toggle State | Response Badge | What It Means |
|--------------|----------------|---------------|
| 🧠 **Memory ON** | 🧠 LLM response using X past messages as context | LLM + Memory |
| 🧠 **Memory OFF** | 💭 Fresh LLM response (no past context found) | LLM only |
| ⚡ **Cache ON** | ⚡ Cached answer (X% similar) - Instant response! | Memory only |
| ⚡ **Cache OFF** | 🧠/💭 LLM response | LLM always |
| 💭 **LLM ON** | 🧠/💭/⚡ Normal response | Full functionality |
| 💭 **LLM OFF** | Limited mode message | No LLM |

---

## 🎯 **Use Cases:**

### **Development & Testing:**
- **Test Memory**: Turn OFF memory, see if responses change
- **Test Caching**: Turn OFF cache, see if responses are always fresh
- **Test LLM**: Turn OFF LLM, see fallback behavior

### **Performance Testing:**
- **Speed Test**: Turn ON cache, measure instant responses
- **Memory Test**: Turn OFF memory, test without context
- **LLM Test**: Turn OFF LLM, test fallback mode

### **Debugging:**
- **Isolate Issues**: Turn OFF specific features to find problems
- **Compare Modes**: See difference between memory vs no-memory
- **Cache Testing**: Verify cached vs fresh responses

---

## 🚀 **Quick Test:**

**Refresh your browser** at `http://localhost:5001`

**Try this sequence:**
1. **Turn OFF Memory Context**
2. Ask: "What's my name?"
3. Should show: 💭 **Fresh LLM response (no past context found)**

4. **Turn ON Memory Context**  
5. Say: "My name is Alice"
6. Ask: "What's my name?"
7. Should show: 🧠 **LLM response using 1 past message as context**

**Perfect!** You now have **full control** over the chatbot's behavior! 🎯✅
