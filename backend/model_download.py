from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="TheBloke/Mistral-7B-Instruct-v0.3-GGUF",
    local_dir="models/mistral",
    allow_patterns=["*Q4_K_M.gguf"]
)