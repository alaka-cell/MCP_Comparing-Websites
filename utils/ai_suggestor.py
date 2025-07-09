from ollama import Client

def generate_suggestions(query: str, model: str = "mistral", count: int = 5) -> list:
    client = Client()
    prompt = f"""
    Based on the user’s interest in "{query}", suggest {count} related beauty product search phrases.
    Keep them under 6 words, consumer-friendly, and diverse.
    """
    try:
        response = client.chat(model=model, messages=[{"role": "user", "content": prompt}])
        suggestions = response["message"]["content"].strip().split("\n")
        return [s.strip("-•1234567890. ").strip() for s in suggestions if len(s.strip()) > 3]
    except Exception as e:
        print("Ollama error (suggestions):", e)
        return []

def generate_comparison_summary(matched_products: list, model: str = "mistral") -> str:
    client = Client()
    prompt = f"""
    You are an expert beauty advisor.

    Given the following matched product sets from different sites, summarize their similarities and differences briefly.
    Don't list prices or links—just do a qualitative comparison as if advising a user.

    Matched Sets:
    {matched_products}

    Return the summary in 2-3 sentences.
    """
    try:
        response = client.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"].strip()
    except Exception as e:
        print("Ollama error (comparison):", e)
        return "AI comparison could not be generated."
