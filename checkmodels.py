from openai import OpenAI

client = OpenAI(api_key="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")

models = client.models.list()

for model in models.data:
    print(model.id)
