from unsloth import FastLanguageModel
from peft import PeftModel
import torch

# 🔹 Your adapter path (use best checkpoint)
ADAPTER_PATH = "./checkpoint-135"

# 🔹 Base model
BASE_MODEL = "unsloth/mistral-7b-instruct-v0.3-bnb-4bit"

# Load base model via Unsloth
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)

# Attach your LoRA adapter
model = PeftModel.from_pretrained(model, ADAPTER_PATH)

# Enable inference optimizations
FastLanguageModel.for_inference(model)

# ---- TEST PROMPT ----
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
# Tokenize
inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")

# Generate
outputs = model.generate(
    **inputs,
    max_new_tokens=120,
    temperature=0.7,
    do_sample=True
)

# Decode
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("\n===== MODEL OUTPUT =====\n")
print(response)