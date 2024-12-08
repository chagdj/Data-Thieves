import csv
from datetime import datetime, timedelta, date
import requests
import pandas as pd
import streamlit as st
import altair as alt  # For creating interactive charts

# Spoonacular API details
api_url = "https://api.spoonacular.com/recipes/findByIngredients"
api_key = "3402019df6944e5380bd1eb7cd3a78e5"  # Replace with your actual Spoonacular API key

# Function to read ingredients from CSV
def read_ingredients(file_path='ingredients.csv'):
    try:
        df = pd.read_csv(file_path, parse_dates=['expiration_date'])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=['ingredient', 'expiration_date'])
    except Exception as e:
        st.error(f"Error reading ingredients: {e}")
        return pd.DataFrame(columns=['ingredient', 'expiration_date'])

# Function to add a new ingredient
def add_ingredient():
    st.header("Add a New Ingredient")
    with st.form("add_ingredient_form"):
        ingredient_name = st.text_input("Ingredient Name").strip().lower()
        expiration_date = st.date_input("Expiration Date", min_value=date.today())
        submitted = st.form_submit_button("Add Ingredient")

        if submitted:
            if ingredient_name:
                df = read_ingredients()
                new_row = {'ingredient': ingredient_name, 'expiration_date': expiration_date}
                
                # Replace df.append() with pd.concat()
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
                try:
                    df.to_csv('ingredients.csv', index=False)
                    st.success(f"Ingredient '{ingredient_name}' added successfully!")
                except Exception as e:
                    st.error(f"Error saving ingredient: {e}")
            else:
                st.error("Ingredient name cannot be empty.")

# Function to view all ingredients
def view_ingredients():
    st.header("Your Ingredients")
    df = read_ingredients()
    if not df.empty:
        st.dataframe(df)

        # Create a bar chart of ingredients and their expiration dates
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('ingredient', sort='-y'),
            y=alt.Y('expiration_date', title='Expiration Date'),
            color='ingredient',
            tooltip=['ingredient', 'expiration_date']
        ).properties(
            width=700,
            height=400,
            title="Ingredients Expiration Dates"
        )
        st.altair_chart(chart)
    else:
        st.info("No ingredients found. Please add some ingredients.")

# Function to check for ingredients expiring soon
def check_expiring_ingredients():
    st.header("Ingredients Expiring Soon")
    df = read_ingredients()
    if not df.empty:
        today = date.today()
        warning_date = today + timedelta(days=3)
        expiring_soon = df[(df['expiration_date'] >= pd.to_datetime(today)) & (df['expiration_date'] <= pd.to_datetime(warning_date))]

        if not expiring_soon.empty:
            st.warning("The following ingredients are expiring soon:")
            st.dataframe(expiring_soon)
        else:
            st.success("No ingredients are expiring in the next few days.")
    else:
        st.info("No ingredients found.")

# Function to remove an ingredient
def remove_ingredient():
    st.header("Remove an Ingredient")
    df = read_ingredients()
    if not df.empty:
        ingredient_list = df['ingredient'].tolist()
        ingredient_to_remove = st.selectbox("Select an ingredient to remove", ingredient_list)

        if st.button("Remove Ingredient"):
            updated_df = df[df['ingredient'] != ingredient_to_remove]
            try:
                updated_df.to_csv('ingredients.csv', index=False)
                st.success(f"Ingredient '{ingredient_to_remove}' has been removed.")
            except Exception as e:
                st.error(f"Error removing ingredient: {e}")
    else:
        st.info("No ingredients to remove.")

# Function to get recipes from the Spoonacular API
def get_recipes_from_api(user_ingredients):
    params = {
        "ingredients": user_ingredients,
        "number": 5,             # Number of recipes to retrieve
        "ranking": 2,            # 1: Maximize used ingredients, 2: Minimize missing ingredients
        "ignorePantry": "true",  # Ignore common pantry items like water and salt
        "apiKey": api_key
    }

    try:
        response = requests.get(api_url, params=params)
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

# Function to display recipes
def display_recipes(recipes, user_ingredients):
    if recipes:
        st.write(f"### Recipes Found Using Your Ingredients: {user_ingredients}\n")
        for idx, recipe in enumerate(recipes, start=1):
            st.subheader(f"Recipe {idx}: {recipe['title']}")
            st.image(recipe['image'], width=300)
            st.write(f"**Recipe ID:** {recipe['id']}")
            st.write("**Used Ingredients:**")
            for ingredient in recipe['usedIngredients']:
                st.write(f"- {ingredient['original']}")
            st.write("**Missing Ingredients:**")
            for ingredient in recipe['missedIngredients']:
                st.write(f"- {ingredient['original']}")
            st.markdown("---")
    else:
        st.warning("No recipes found with the provided ingredients.")

# Function to find recipes based on user's ingredients
def find_recipes():
    st.header("Find Recipes Based on Your Ingredients")
    df = read_ingredients()
    if not df.empty:
        ingredient_names = df['ingredient'].tolist()
        user_ingredients = ','.join(ingredient_names)
        st.write(f"Searching for recipes using: **{user_ingredients}**")

        recipes = get_recipes_from_api(user_ingredients)
        display_recipes(recipes, user_ingredients)
    else:
        st.info("No ingredients found. Please add ingredients first.")

# Main function to control the app's navigation
def main():
    st.title("🍲 Recipe Finder App")
    menu_options = [
        "Add a New Ingredient",
        "View All Ingredients",
        "Check Ingredients Expiring Soon",
        "Remove an Ingredient",
        "Find Recipes with My Ingredients"
    ]
    choice = st.sidebar.selectbox("Menu", menu_options)

    if choice == 'Add a New Ingredient':
        add_ingredient()
    elif choice == 'View All Ingredients':
        view_ingredients()
    elif choice == 'Check Ingredients Expiring Soon':
        check_expiring_ingredients()
    elif choice == 'Remove an Ingredient':
        remove_ingredient()
    elif choice == 'Find Recipes with My Ingredients':
        find_recipes()
    else:
        st.error("Invalid selection.")

# Execute the app
if __name__ == "__main__":
    main()
