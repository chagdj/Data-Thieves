import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, date
import requests
import os
import altair as alt
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY")  

if API_KEY:
    print("API Key successfully loaded.")
else:
    print("API Key is missing!")


API_URL = "https://api.spoonacular.com/recipes/findByIngredients"
FILE_PATH = "ingredients.csv"

# To ensure the ingredients CSV exists or create one if missing
def initialize_ingredients_file():
    if not os.path.exists(FILE_PATH):
        # Create a default CSV with example data
        data = [
            {"ingredient": "milk", "expiration_date": "2023-12-10"},
            {"ingredient": "eggs", "expiration_date": "2023-12-12"}
        ]
        pd.DataFrame(data).to_csv(FILE_PATH, index=False)

# To read ingredients from CSV
def read_ingredients():
    try:
        df = pd.read_csv(FILE_PATH)
        if "expiration_date" in df.columns:
            df["expiration_date"] = pd.to_datetime(df["expiration_date"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Error reading ingredients file: {e}")
        return pd.DataFrame(columns=["ingredient", "expiration_date"])

# To add a new ingredient
def add_ingredient():
    st.header("➕ Add a New Ingredient")
    with st.form("add_ingredient_form"):
        ingredient_name = st.text_input("Ingredient Name").strip().lower()
        expiration_date = st.date_input("Expiration Date", min_value=date.today())
        submitted = st.form_submit_button("Add Ingredient")
        
        if submitted:
            if ingredient_name:
                df = read_ingredients()
                new_row = {"ingredient": ingredient_name, "expiration_date": expiration_date}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                try:
                    df.to_csv(FILE_PATH, index=False)
                    st.success(f"Ingredient '{ingredient_name}' added successfully!")
                except Exception as e:
                    st.error(f"Error saving ingredient: {e}")
            else:
                st.error("Ingredient name cannot be empty.")

# All ingredients with visuals
def view_ingredients():
    st.header("📋 Your Ingredients")
    df = read_ingredients()
    if not df.empty:
        st.dataframe(df)

        # Create a timeline-style bar chart
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("expiration_date:T", title="Expiration Date"),
            y=alt.Y("ingredient", sort='-x', title="Ingredient"),
            color="ingredient",
            tooltip=["ingredient", "expiration_date"]
        ).properties(
            title="Ingredient Expiration Timeline",
            width=800,
            height=400
        )
        st.altair_chart(chart)
    else:
        st.info("No ingredients found. Please add some.")

# To check for ingredients expiring soon
def check_expiring_ingredients():
    st.header("⏰ Ingredients Expiring Soon")
    df = read_ingredients()
    if not df.empty:
        today = datetime.now().date()
        warning_date = today + timedelta(days=3)
        expiring_soon = df[
            (df["expiration_date"] >= pd.to_datetime(today)) &
            (df["expiration_date"] <= pd.to_datetime(warning_date))
        ]
        if not expiring_soon.empty:
            st.warning("⚠️ The following ingredients are expiring soon:")
            st.dataframe(expiring_soon)
        else:
            st.success("✅ No ingredients are expiring soon.")
    else:
        st.info("No ingredients found.")

# To remove an ingredient
def remove_ingredient():
    st.header("❌ Remove an Ingredient")
    df = read_ingredients()
    if not df.empty:
        ingredient_list = df["ingredient"].tolist()
        ingredient_to_remove = st.selectbox("Select an ingredient to remove", ingredient_list)
        if st.button("Remove Ingredient"):
            df = df[df["ingredient"] != ingredient_to_remove]
            try:
                df.to_csv(FILE_PATH, index=False)
                st.success(f"Ingredient '{ingredient_to_remove}' has been removed.")
            except Exception as e:
                st.error(f"Error removing ingredient: {e}")
    else:
        st.info("No ingredients to remove.")

# To get recipes from Spoonacular API
def get_recipes_from_api(user_ingredients):
    params = {
        "ingredients": user_ingredients,
        "number": 5,
        "ranking": 2,  # Minimize missing ingredients
        "ignorePantry": "true",
        "apiKey": API_KEY
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        recipes = response.json()
        st.write(f"The API returned {len(recipes)} recipes.")
        return recipes
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while accessing the API: {http_err}")
    except requests.exceptions.RequestException as req_err:
        st.error(f"Request error occurred while accessing the API: {req_err}")
    except Exception as e:
        st.error(f"An unexpected error occurred while accessing the API: {e}")
    return []

# To display recipes
def display_recipes(recipes, user_ingredients):
    if recipes:
        st.write(f"### Recipes Found Using Your Ingredients: {user_ingredients}\n")
        for idx, recipe in enumerate(recipes, start=1):
            st.subheader(f"Recipe {idx}: {recipe['title']}")
            st.image(recipe["image"], width=300)
            st.write(f"**Recipe ID:** {recipe['id']}")
            st.write("**Used Ingredients:**")
            for ingredient in recipe["usedIngredients"]:
                st.write(f"- {ingredient['original']}")
            st.write("**Missing Ingredients:**")
            for ingredient in recipe["missedIngredients"]:
                st.write(f"- {ingredient['original']}")
            st.markdown("---")
    else:
        st.warning("No recipes found with the provided ingredients.")

# To find recipes
def find_recipes():
    st.header("🍴 Find Recipes")
    df = read_ingredients()
    if not df.empty:
        ingredient_list = df["ingredient"].tolist()
        unique_ingredients = list(set(ingredient_list))  # Remove duplicates
        user_ingredients = ",".join(unique_ingredients)
        st.write(f"Ingredients sent to API: {user_ingredients}")
        recipes = get_recipes_from_api(user_ingredients)
        display_recipes(recipes, user_ingredients)
    else:
        st.info("Please add some ingredients first!")

# Mains menus
def main():
    st.title("🍲 Recipe Finder App")
    menu_options = [
        "➕ Add a New Ingredient",
        "📋 View All Ingredients",
        "⏰ Check Ingredients Expiring Soon",
        "❌ Remove an Ingredient",
        "🍴 Find Recipes"
    ]
    choice = st.sidebar.selectbox("Menu", menu_options)
    
    if choice == "➕ Add a New Ingredient":
        add_ingredient()
    elif choice == "📋 View All Ingredients":
        view_ingredients()
    elif choice == "⏰ Check Ingredients Expiring Soon":
        check_expiring_ingredients()
    elif choice == "❌ Remove an Ingredient":
        remove_ingredient()
    elif choice == "🍴 Find Recipes":
        find_recipes()
    else:
        st.error("Invalid selection.")


if __name__ == "__main__":
    initialize_ingredients_file()
    main()
