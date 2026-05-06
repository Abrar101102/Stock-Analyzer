from llama_cpp import Llama

llm = Llama(
    model_path="models/mistral-7b-instruct-v0.3.Q4_K_M.gguf",
    lora_path="models/model-f16.gguf"
)

prompt = """<|system|>
You are a financial analyst.
<|user|>
Analyze stock HDFCBANK with signals:
fundamental: positive
technical: neutral
sentiment: negative
valuation: expensive

Give a short thesis and verdict.
<|assistant|>
"""

output = llm(
    prompt,
    max_tokens=50
)

print(output["choices"][0]["text"])