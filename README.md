# local-ai-customer-support-agent
A local AI customer-support agent built with Qwen3, LangGraph, and Streamlit
## 1. Prerequisites
- Python 3.10 or newer
- Ollama installed and running
- Enough RAM/VRAM to run `qwen3:8b` locally

## 2. Download the model
Run in a terminal:

```bash
ollama pull qwen3:8b
```

Keep Ollama running. If needed, test it with:

```bash
ollama run qwen3:8b
```

## 3. Set up the Python environment
From this project folder:

```bash
python -m venv .venv
```

Activate it:
- macOS/Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

Then install packages:

```bash
pip install -r requirements.txt
```

## 4. Run the UI

```bash
streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## What it can answer
- Order status for demo IDs `12345`, `67890`, and `24680`
- Return policy
- Shipping timelines
- Basic demo product information
- Requests to escalate to a human

- <img width="1426" height="879" alt="image" src="https://github.com/user-attachments/assets/07932466-d652-45f8-8427-5d4b20a1e5a8" />
<img width="1422" height="885" alt="image" src="https://github.com/user-attachments/assets/a37e1b75-3d72-4f7f-8c79-9ebaac7b617d" />



## Important limitations
- The order and product data are hard-coded mock data.
- Return/refund/cancellation actions are not implemented.
- Escalation does not create a real ticket.
- `MemorySaver` stores conversation state in the running process; it is not persistent storage.
- Before production use, connect secure APIs/database, add authentication and authorization, validate tool inputs, and log/escalate errors safely.
