from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

model_name = "nvidia/NVIDIA-Nemotron-Nano-9B-v2"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    trust_remote_code=True
)

generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

prompt = "Write a short story about a robot learning to love."
output = generator(prompt, max_new_tokens=200)
print(output[0]["generated_text"])
