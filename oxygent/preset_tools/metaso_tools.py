import http.client
import json
import contextvars
from oxygent.oxy import FunctionHub

metaso_tools = FunctionHub(name="metaso_tools")

# Context-local usage counter for concurrency support
# This ensures that each async task has its own independent counter
_usage_counter_ctx = contextvars.ContextVar("metaso_usage", default={"chat": 0, "reader": 0})

def reset_metaso_usage():
    """Reset the usage counters for the current context (task)."""
    _usage_counter_ctx.set({"chat": 0, "reader": 0})

@metaso_tools.tool(
    description="Ask Metaso AI a question. This tool uses RAG to search and answer. Use this for almost all questions."
)
def metaso_chat(message: str) -> str:
    usage = _usage_counter_ctx.get()
    # Strict limit: 1 call per task
    if usage["chat"] >= 1:
        return "Error: You have used metaso_chat once. You cannot use it again. Please output the final answer based on what you know."
    
    # Increment usage
    # Note: We must create a new dictionary to avoid mutating the shared default object if it was used
    new_usage = usage.copy()
    new_usage["chat"] += 1
    _usage_counter_ctx.set(new_usage)
    
    conn = http.client.HTTPSConnection("metaso.cn")
    payload = json.dumps({
        "model": "fast",
        "stream": False, # Disable stream for simpler handling
        "messages": [{"role": "user", "content": message}]
    })
    headers = {
        'Authorization': 'Bearer mk-8AA784D355A335948AAA2FE90B222EF4',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    try:
        conn.request("POST", "/api/v1/chat/completions", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_json = json.loads(data.decode("utf-8"))
        # Extract content from OpenAI-compatible format
        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"]
        return f"Error: Unexpected response format: {data.decode('utf-8')}"
    except Exception as e:
        return f"Error calling metaso_chat: {str(e)}"

@metaso_tools.tool(
    description="Read webpage content using Metaso reader. Use this ONLY when you have a specific URL."
)
def metaso_reader(url: str) -> str:
    usage = _usage_counter_ctx.get()
    if usage["reader"] >= 1:
        return "Error: You have already used metaso_reader once. You cannot use it again for this task."
    
    new_usage = usage.copy()
    new_usage["reader"] += 1
    _usage_counter_ctx.set(new_usage)

    conn = http.client.HTTPSConnection("metaso.cn")
    payload = json.dumps({"url": url})
    headers = {
        'Authorization': 'Bearer mk-8AA784D355A335948AAA2FE90B222EF4',
        'Accept': 'text/plain',
        'Content-Type': 'application/json'
    }
    try:
        conn.request("POST", "/api/v1/reader", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")
    except Exception as e:
        return f"Error calling metaso_reader: {str(e)}"
