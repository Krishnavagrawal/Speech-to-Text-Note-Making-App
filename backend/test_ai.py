from services.ai_service import clean_notes, generate_key_points, generate_title, summarize_text

text = """
Today we are studying supervised learning.
Supervised learning uses labelled data.
The model learns a relationship between
input and output data.
It is commonly used for classification
and regression.
"""

print("\n--- TITLE ---")
print(generate_title(text))

print("\n--- SUMMARY ---")
print(summarize_text(text))

print("\n--- KEY POINTS ---")
print(generate_key_points(text))

print("\n--- CLEAN NOTES ---")
print(clean_notes(text))
