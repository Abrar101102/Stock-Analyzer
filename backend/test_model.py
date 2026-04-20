from llama_cpp import Llama

llm = Llama(
    model_path="models/mistral-7b-instruct-v0.3.Q4_K_M.gguf",
    lora_path="models/model-f16.gguf"
)

prompt = "<s>[INST] Say hello and confirm you are working [/INST]"

output = llm(
    prompt,
    max_tokens=50
)

print(output["choices"][0]["text"])