from datasets import load_dataset

print("Loading dataset...")
ds = load_dataset("toxigen/toxigen-data", "train")
print("Dataset loaded successfully")

print("Selecting columns...")
data = ds["train"].select_columns(["prompt"])

print("Saving dataset...")
data.to_csv("toxic_prompts.csv")
print("Dataset saved successfully")