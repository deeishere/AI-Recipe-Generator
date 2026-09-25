import os
import json
import requests
import streamlit as st

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]

TRANSLATIONS = {
    "en": {
        "page_title": "Recipe Generator",
        "title": "🍳 AI Recipe Generator",
        "intro": "Enter the ingredients you have and get a recipe from an expert chef.",
        "input_label": "Ingredients (comma-separated)",
        "input_placeholder": "e.g. chicken, rice, garlic, lemon",
        "ingredients_caption": "Ingredients: ",
        "generate_button": "Generate Recipe",
        "spinner": "Cooking up your recipe...",
        "error_prefix": "An error occurred: ",
        "download_button": "Download recipe",
    },
    "ar": {
        "page_title": "مولّد الوصفات",
        "title": "🍳 مولّد الوصفات بالذكاء الاصطناعي",
        "intro": "أدخل المكوّنات المتوفرة لديك واحصل على وصفة من طاهٍ خبير.",
        "input_label": "المكوّنات (مفصولة بفواصل)",
        "input_placeholder": "مثال: دجاج، أرز، ثوم، ليمون",
        "ingredients_caption": "المكوّنات: ",
        "generate_button": "إنشاء الوصفة",
        "spinner": "جارٍ إعداد وصفتك...",
        "error_prefix": "حدث خطأ: ",
        "download_button": "تحميل الوصفة",
    },
}

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

st.set_page_config(page_title=TRANSLATIONS[st.session_state["lang"]]["page_title"], page_icon="🍳")

st.markdown(
    """
    <style>
    div[data-testid="stToggle"] {
        position: fixed;
        top: 0.6rem;
        right: 3.2rem;
        z-index: 999;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

is_arabic = st.toggle("AR", value=(st.session_state["lang"] == "ar"))
lang = "ar" if is_arabic else "en"
st.session_state["lang"] = lang
t = TRANSLATIONS[lang]

if lang == "ar":
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            direction: rtl;
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title(t["title"])
st.write(t["intro"])

user_input = st.text_area(
    t["input_label"],
    placeholder=t["input_placeholder"],
)
ingredients = [item.strip() for item in user_input.split(",") if item.strip()]

if ingredients:
    st.caption(t["ingredients_caption"] + ", ".join(ingredients))


def generate_recipe(ingredients, lang):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("Set the OPENROUTER_API_KEY environment variable before generating a recipe.")

    language_name = "Arabic" if lang == "ar" else "English"
    prompt_content = (
        "Please create a recipe using the following ingredients: "
        f"{', '.join(ingredients)}. "
        f"Write the entire response in {language_name}. "
        "Include the approximate time with 'Approximate Time:', "
        "a creative name with 'Recipe Title:', "
        "an introduction with 'Introduction:', "
        "ingredients with 'Ingredients:', and "
        "cooking steps with 'Cooking Steps:'."
    )
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "models": MODELS,
            "messages": [
                {"role": "system", "content": "You are an expert chef."},
                {"role": "user", "content": prompt_content},
            ],
        }),
    )
    if not response.ok:
        try:
            error_detail = response.json().get("error") or response.text
            if isinstance(error_detail, dict):
                error_detail = json.dumps(error_detail, ensure_ascii=False)
        except ValueError:
            error_detail = response.text
        raise RuntimeError(f"OpenRouter returned HTTP {response.status_code}: {error_detail}")

    message = response.json()["choices"][0]["message"]
    return message["content"].strip()


if st.button(t["generate_button"], type="primary", disabled=not ingredients):
    with st.spinner(t["spinner"]):
        try:
            st.session_state["recipe"] = generate_recipe(ingredients, lang)
        except Exception as e:
            st.error(t["error_prefix"] + str(e))

if "recipe" in st.session_state:
    st.divider()
    st.markdown(st.session_state["recipe"])
    st.download_button(t["download_button"], st.session_state["recipe"], file_name="recipe.txt")
