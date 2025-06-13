from flask import Flask, render_template, request
import pandas as pd
import random
# IMPORTANT: You need to install the Google AI library:
# pip install google-generativeai
import google.generativeai as genai # Uncomment this line when you have the library

app = Flask(__name__)

# --- IMPORTANT: Configure Gemini ---
# You MUST set up your API key securely, preferably using environment variables.
# DO NOT HARDCODE YOUR KEY HERE.
# Example (replace with your actual key setup):
import os
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY environment variable not set. AI features will be simulated.")
    # Handle the case where the key isn't available (e.g., use simulation only)
else:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro') # Or your preferred model
        GEMINI_ACTIVE = True
    except Exception as e:
        print(f"Error configuring Gemini: {e}. AI features will be simulated.")
        GEMINI_ACTIVE = False

# # --- Simulation flag (use if API key isn't set or configuration fails) ---
# GEMINI_ACTIVE = True # Set to True only if genai.configure and model creation succeed

# --- Dummy Data Generation ---
def generate_dummy_lounges(num_lounges=100):
    lounges = []
    airports = ["JFK", "LAX", "LHR", "CDG", "DXB", "HND", "ORD", "ATL", "AMS", "SIN"]
    lounge_names = ["Sky", "Star", "Aspire", "Centurion", "Maple Leaf", "Plaza Premium", "Qantas", "Emirates", "United Club", "Delta Sky Club"]
    terminals = ["T1", "T2", "T3", "T4", "International", "Domestic"]
    amenities = [
        "Wi-Fi, Showers, Food, Bar",
        "Wi-Fi, Snacks, Drinks",
        "Wi-Fi, Business Center, Food",
        "Premium Wi-Fi, Spa, A la carte Dining, Bar",
        "Wi-Fi, Quiet Zone, Refreshments",
    ]

    for i in range(num_lounges):
        airport = random.choice(airports)
        lounge_name = f"{random.choice(lounge_names)} Lounge"
        terminal = random.choice(terminals)
        # Default description
        default_description = f"Experience comfort at {lounge_name} in {airport} ({terminal}). Enjoy {random.choice(amenities).lower()}."

        lounges.append({
            "id": i + 1,
            "airport": airport,
            "name": lounge_name,
            "terminal": terminal,
            "amenities": random.choice(amenities),
            "ai_description": default_description, # Start with default
            "rating": round(random.uniform(3.5, 5.0), 1)
        })
    return lounges

# --- Route with Search & AI ---
@app.route('/')
def home():
    all_lounges = generate_dummy_lounges(100)
    filtered_lounges = list(all_lounges) # Create a copy to modify
    search_active = True

    search_place = request.args.get('place', '').strip().upper()
    search_date = request.args.get('date', '').strip()
    search_time = request.args.get('time', '').strip()
    search_flight = request.args.get('flight', '').strip()

    search_terms = {
        'place': search_place,
        'date': search_date,
        'time': search_time,
        'flight': search_flight
    }

    # --- Basic Filtering Logic ---
    if search_place:
        search_active = True
        # Filter the copied list
        filtered_lounges = [
            lounge for lounge in filtered_lounges
            if lounge['airport'] == search_place
        ]
        # Optional: Further filter by terminal based on flight, check opening hours, etc.

    # --- AI Integration Point ---
    if search_active and filtered_lounges:
        # Sort to get the best candidate(s) first (e.g., by rating)
        filtered_lounges.sort(key=lambda x: x['rating'], reverse=True)

        # Select the top lounge (or maybe top 2-3) to highlight
        top_lounge = filtered_lounges[0]

        # --- Craft the prompt for Gemini ---
        prompt = f"""
        A traveler is looking for an airport lounge.
        Details:
        - Airport: {search_place}
        - Date: {search_date if search_date else 'Not specified'}
        - Time: {search_time if search_time else 'Not specified'}
        - Flight: {search_flight if search_flight else 'Not specified'}

        Here is the top recommended lounge based on initial filtering:
        - Name: {top_lounge['name']}
        - Terminal: {top_lounge['terminal']}
        - Rating: {top_lounge['rating']}/5.0
        - Amenities: {top_lounge['amenities']}

        Generate a short, appealing, and slightly enthusiastic description (1-2 sentences) for this lounge, highlighting why it might be a great choice for this traveler. Use emojis relevant to travel or luxury (like ✈️, ✨, 🥂, 🛋️). Make it sound like a helpful AI assistant's recommendation.
        """

        beautiful_description = "" # Initialize
        try:
            if GEMINI_ACTIVE:
                # --- Attempt to call the actual Gemini API ---
                response = model.generate_content(prompt) # Uncomment the import google.generativeai line too!
                beautiful_description = response.text
               
                pass # Placeholder: Remove this pass when uncommenting the line above
            else:
                # --- Fallback to SIMULATED Gemini Response ---
                print("--- SIMULATING GEMINI RESPONSE ---") # Log simulation
                amenity_highlight = top_lounge['amenities'].split(',')[0].strip()
                beautiful_description = f"✨ Jetsetter alert! For your stop at {search_place}, the **{top_lounge['name']}** ({top_lounge['terminal']}) is a top pick ({top_lounge['rating']}⭐)! Unwind with amenities like _{amenity_highlight}_ before flight {search_flight if search_flight else 'your next journey'}. Bon voyage! ✈️🛋️"


            # --- Update the top lounge's description if AI/Simulation was successful ---
            if beautiful_description:
                # Find the top lounge in the filtered list and update its description
                for i, lounge in enumerate(filtered_lounges):
                    if lounge['id'] == top_lounge['id']:
                        # Make a copy of the lounge dict to modify, to avoid altering the original list directly
                        lounge_copy = filtered_lounges[i].copy()
                        lounge_copy['ai_description'] = beautiful_description
                        filtered_lounges[i] = lounge_copy # Replace the original dict with the modified copy
                        break # Stop after updating the top one

        except Exception as e:
            print(f"Error during AI processing (or simulation): {e}")
            # Keep the default description if AI fails

    # Pass the potentially modified lounges to the template
    return render_template(
        'index.html',
        lounges=filtered_lounges,
        search_terms=search_terms,
        search_active=search_active
    )

if __name__ == '__main__':
    # For local development. Vercel uses its own server configuration.
    app.run(debug=True, port=5001)
