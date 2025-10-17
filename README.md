# Measuring Bias in LLMs

Project to measure bias in LLMs.

This repository documents methods, datasets, and experiments to evaluate, visualize, and mitigate bias in large language models.

In this workshop, we will:

- pick popular open source LLMs that we will be used to measure bias (see [/how_to_llamafile.md](/how_to_llamafile.md))
- design experiment methods to measure bias in LLMs
- run experiments to measure and capture results
- analyze results of experiments
- publish results in this repo and give a lightning talk

Each team will create a new folder in the root directory of this repo and add their method, experiments, results, and findings there.

## Design Experiment Methods

When designing your experiments, you may consider the following:

- Define objectives: Determine what you want to achieve, such as assessing gender bias, measuring likeliness of generating toxic content or hate speech, etc.
- Prepare datasets: Create or adopt datasets of prompts to test the model. You may have a look at public data set at [Kaggle](https://www.kaggle.com/datasets) or [Hugging Face](https://huggingface.co/datasets).
- Consider the LLM limitations: Be aware of the potential for "hallucinations" and performance issues.
- Method to run experiments: How to programmatically run your experiments.
- Capture results: How to capture the results of your experiments.
- Define evaluation: Define how you will evaluate the result of your experiments.

## Analyze and publish results

Put on your data science hat and analyze the results of your experiments. Inspecting the data and data visualization would be a good start. You can also publish your results in this repo in any format, Jupyter notebooks, slides, documents with pictures, etc.

