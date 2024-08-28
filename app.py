import streamlit as st
import hashlib
import json
#import gspread
import os
#from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pandas as pd

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load users from file or create an empty file if it doesn't exist
if os.path.exists("users.json"):
    with open("users.json", "r") as file:
        users = json.load(file)
else:
    users = {}

# Function to save users to file
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file)

# Function to authenticate users
def authenticate(username, password):
    if username in users and users[username] == hash_password(password):
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
    else:
        st.error("Invalid username or password")

# Function to register a new user
def register_user(username, password):
    if username in users:
        st.error("Username already exists")
    else:
        users[username] = hash_password(password)
        save_users(users)
        st.success("User registered successfully! You can now log in.")

# Function to connect to Google Sheets using credentials from secrets.toml
def connect_to_google_sheets():
    try:
        # Define the required scopes
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Load credentials from Streamlit secrets
        creds_json = st.secrets["google"]["credentials"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(creds_json), 
            scopes
        )
        client = gspread.authorize(creds)
        sheet = client.open("MealTracker v0 Beta").sheet1  # Your Google Sheet name
        return sheet
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")

# Function to log meal data to Google Sheets
def log_meal(sheet, date, meal_type, food, ill_effects, time_of_meal, time_of_symptoms):
    try:
        entry = [str(date), meal_type, food, ill_effects, str(time_of_meal), str(time_of_symptoms)]
        sheet.append_row(entry)
        st.success("Meal entry added successfully!")
    except Exception as e:
        st.error(f"Failed to log meal data: {e}")

# Function to retrieve and display meal data
def retrieve_meal_data(sheet, start_date, end_date):
    try:
        # Get all data from the sheet
        data = sheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])

        # Convert the 'Date' column to datetime for filtering
        df['Date'] = pd.to_datetime(df['Date'])

        # Filter data based on the selected date range
        mask = (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))
        filtered_data = df.loc[mask]

        st.write(f"Displaying meal data from {start_date} to {end_date}:")
        st.dataframe(filtered_data)
    except Exception as e:
        st.error(f"Failed to retrieve meal data: {e}")

# Main app logic
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if st.session_state["authenticated"]:
    st.sidebar.title(f"Welcome, {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.experimental_rerun()  # Rerun after logout to refresh the state

    page = st.sidebar.selectbox("Choose a page", ["Log Meal", "View Meals"])

    sheet = connect_to_google_sheets()

    if page == "Log Meal":
        st.title("Meal Tracker")

        if sheet:
            with st.form("meal_form"):
                date = st.date_input("Date of Meal", datetime.date.today())
                meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
                food = st.text_input("Food Consumed")
                ill_effects = st.text_input("Ill Effects (if any)")
                time_of_meal = st.time_input("Time of Meal")
                time_of_symptoms = st.time_input("Time of Symptoms", datetime.time(0, 0))

                submitted = st.form_submit_button("Submit")

                if submitted:
                    log_meal(sheet, date, meal_type, food, ill_effects, time_of_meal, time_of_symptoms)

    elif page == "View Meals":
        st.title("View Meal Entries")

        if sheet:
            with st.form("view_meals_form"):
                start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=7))
                end_date = st.date_input("End Date", datetime.date.today())

                submitted = st.form_submit_button("Retrieve")

                if submitted:
                    retrieve_meal_data(sheet, start_date, end_date)

else:
    option = st.selectbox("Select an option", ["Login", "Register"])

    if option == "Login":
        st.title("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            authenticate(username, password)
            if st.session_state["authenticated"]:
                st.experimental_rerun()  # Rerun after login to refresh the state

    elif option == "Register":
        st.title("Register")

        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        if st.button("Register"):
            register_user(username, password)
