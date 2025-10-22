from datasets import load_dataset

ds = load_dataset("toxigen/toxigen-data", "train")
data = ds["train"].select_columns(["prompt"])
data.to_csv("experiments/toxic_prompts.csv")

