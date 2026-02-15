import streamlit as st
import json
import os
import time
from datetime import datetime, timedelta
from google import genai

# ---------- Gemini Setup ----------

client = genai.Client(api_key=os.getenv("AIzaSyAMxOGwW8lHF3DdVkJ9QgX0oa4f3Zj5ZIE"))

DATA_FILE = "period_data.json"

# ---------- Styling ----------
st.markdown("""
<style>
body {
    background-color: #fff6fa;
}
.card {
    background-color: #fde2e4;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 15px;
}
.title {
    color: #6d597a;
}
</style>
""", unsafe_allow_html=True)

# ---------- Data Handling ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "cycle_length" not in data:
                data["cycle_length"] = 28
            if "entries" not in data:
                data["entries"] = []
            return data

    return {"entries": [], "cycle_length": 28}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------- AI Advice ----------
def get_ai_advice(symptoms):

    if not symptoms:
        return "No symptoms logged yet."

    prompt = f"""
    The user is experiencing these period symptoms: {symptoms}.
    Provide 2 short, empathetic, safe wellness tips.
    Be supportive and calming.
    """

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            if response.text:
                return response.text.strip()

        except Exception as e:

            print(f"Attempt {attempt+1} failed:", e)
            time.sleep(2)

    return "AI is currently busy. Please try again later."


# ---------- Latest Entry ----------
def get_latest_entry(entries):

    latest_entry = None
    latest_date = None

    for entry in entries:

        if "start_date" in entry:
            entry_date = datetime.strptime(entry["start_date"], "%Y-%m-%d")

        elif "date" in entry:
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")

        else:
            continue

        if latest_date is None or entry_date > latest_date:

            latest_date = entry_date
            latest_entry = entry

    return latest_entry, latest_date


# ---------- Average Cycle ----------
def calculate_average_cycle(entries):

    start_dates = []

    for entry in entries:

        if "start_date" in entry:
            start_dates.append(
                datetime.strptime(entry["start_date"], "%Y-%m-%d")
            )

        elif "date" in entry:
            start_dates.append(
                datetime.strptime(entry["date"], "%Y-%m-%d")
            )

    if len(start_dates) < 2:
        return None

    start_dates.sort()

    differences = [

        (start_dates[i] - start_dates[i - 1]).days

        for i in range(1, len(start_dates))

    ]

    return round(sum(differences) / len(differences))


# ---------- Load Data ----------
data = load_data()

# Backward compatibility fix
updated = False

for entry in data["entries"]:

    if "date" in entry and "start_date" not in entry:

        entry["start_date"] = entry["date"]
        entry["end_date"] = entry["date"]

        del entry["date"]

        updated = True

if updated:
    save_data(data)


# ---------- Sidebar ----------
st.sidebar.title("🌸 Menu")

page = st.sidebar.radio(

    "Navigate",

    ["Dashboard", "Log Entry", "History & AI", "Settings"]

)


# ---------- Dashboard ----------
if page == "Dashboard":

    st.title("🌸 Period Tracker AI")
    st.subheader("Your Wellness Dashboard")

    if data["entries"]:

        last_entry, last_date = get_latest_entry(data["entries"])

        avg_cycle = calculate_average_cycle(data["entries"])

        if avg_cycle:
            next_date = last_date + timedelta(days=avg_cycle)
        else:
            next_date = last_date + timedelta(days=data["cycle_length"])

        st.markdown("<div class='card'>", unsafe_allow_html=True)

        st.markdown(
            f"📅 **Last Period:** {last_date.strftime('%d %B %Y')}"
        )

        st.markdown(
            f"🔮 **Next Predicted Cycle:** {next_date.strftime('%d %B %Y')}"
        )

        if avg_cycle:

            st.markdown(
                f"📊 **Estimated Cycle Length:** {avg_cycle} days"
            )

        else:

            st.markdown(
                f"📊 **Estimated Cycle Length:** {data['cycle_length']} days"
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # AI Advice Card
        st.markdown("<div class='card'>", unsafe_allow_html=True)

        st.markdown("✨ **AI Wellness Insight**")

        try:

            advice = get_ai_advice(
                last_entry.get("symptoms", "")
            )

            st.write(advice)

        except:

            st.warning("AI temporarily unavailable.")

        st.markdown("</div>", unsafe_allow_html=True)

    else:

        st.info("No data yet. Log your first entry 🌷")


# ---------- Log Entry ----------
elif page == "Log Entry":

    st.title("📝 Log New Entry")

    start_end = st.date_input(

        "Period start & end dates",

        value=(datetime.today().date(), datetime.today().date())

    )

    symptoms = st.text_input("Symptoms")

    if st.button("📌 End today"):

        start_end = (start_end[0], datetime.today().date())

        st.info(f"End date set to {start_end[1]}")


    if st.button("Save Entry 🌸"):

        start_date, end_date = start_end

        data["entries"].append({

            "start_date": start_date.strftime("%Y-%m-%d"),

            "end_date": end_date.strftime("%Y-%m-%d"),

            "symptoms": symptoms

        })

        save_data(data)

        st.success("Entry saved successfully!")

        st.rerun()


# ---------- History ----------
elif page == "History & AI":

    st.title("📚 History & Insights")

    if not data["entries"]:

        st.warning("No entries found.")

    else:

        for i, entry in enumerate(list(reversed(data["entries"]))):

            real_index = len(data["entries"]) - 1 - i

            st.markdown("<div class='card'>", unsafe_allow_html=True)

            st.markdown(

                f"📅 **{entry['start_date']} → {entry['end_date']}**"

            )

            st.markdown(

                f"💭 Symptoms: {entry.get('symptoms','None')}"

            )

            if st.button("🗑️ Delete", key=f"delete_{real_index}"):

                data["entries"].pop(real_index)

                save_data(data)

                st.success("Entry deleted!")

                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# ---------- Settings ----------
elif page == "Settings":

    st.title("⚙️ Settings")

    cycle = st.number_input(

        "Cycle length (days)",

        min_value=20,

        max_value=40,

        value=data.get("cycle_length", 28)

    )

    if st.button("Save Settings"):

        data["cycle_length"] = cycle

        save_data(data)

        st.success("Settings updated!")
