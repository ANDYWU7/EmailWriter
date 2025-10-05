import streamlit as st
import json
from openai import OpenAI

client = OpenAI(
    api_key = "KEY"
)

system_prompt = """
You are to act like a Pokedex from the Pokemon franchise. A user will come to
you and give you the name of a Pokemon. If the request is for an
official Pokemon, then give them a description of the Pokemon that matches
the official Pokedex entry. If you don't recognize the Pokemon, then act as
if it was a Pokemon and describe it.

For Pokedex entries, you will return a JSON of the following:

{
    "name": name of pokemon,
    "entry_number": # followed by 4 sequence number. Use official Pokedex number where possible.
    "stats": {
        "hp": integer from 0 to 15 inclusive,
        "attack": integer from 0 to 15 inclusive,
        "defense": integer from 0 to 15 inclusive,
        "special attack": integer from 0 to 15 inclusive,
        "special defense": integer from 0 to 15 inclusive,
        "speed": integer from 0 to 15 inclusive
    },
    "description": one sentence describing its behavior. Use the official Pokedex wherever possible,
    "details": {
        "height": foot-pound quotation notation,
        "weight": float rounded to one decimal point followed by "lbs",
        "gender": male or female,
        "category": type of creature,
        "abilities": [list of moves that it can do]
    }
    "type": [list of types],
    "weaknesses": [list of weakness types],
    "evolutions": for example, "caterpie #0010 --> metapod #0011 --> butterfree #0012"
}
"""
def show_pokedex_entry(page_json):
    st.write(page_json["name"] + " " + page_json["entry_number"])
    st.write()
    st.write("## STATS")
    st.write("\tHP:" + str(page_json["stats"]["hp"]) + "/15")
    st.write("\tAttack:" + str(page_json["stats"]["attack"]) + "/15")
    st.write("\tDefense:" + str(page_json["stats"]["defense"]) + "/15")
    st.write("\tSpecial Attack:" + str(page_json["stats"]["special attack"]) + "/15")
    st.write("\tSpecial Defense:" + str(page_json["stats"]["special defense"]) + "/15")
    st.write("\tSpeed:" + str(page_json["stats"]["speed"]) + "/15")
    st.write()
    st.write(page_json["description"])
    st.write()
    st.write("## DETAILS")
    st.write("\tHeight:", page_json["details"]["height"])
    st.write("\tWeight:", page_json["details"]["weight"])
    st.write("\tGender:", page_json["details"]["gender"])
    st.write("\tCategory:", page_json["details"]["category"])
    st.write("\tAbilities:")
    for ability in page_json["details"]["abilities"]:
        st.write("\t\t" + ability)
    st.write()
    st.write("## TYPE")
    for type in page_json["type"]:
        st.write("\t" + type)
    st.write()
    st.write("## WEAKNESSES")
    for weakness in page_json["weaknesses"]:
        st.write("\t" + weakness)
    st.write()
    st.write("## EVOLUTIONS")
    st.write(page_json["evolutions"])

if "entries" not in st.session_state:
    st.session_state["entries"] = {"Pikachu": "VALUE"}

'''
# Welcome to the Pokedex!
'''
view = st.selectbox(
    "View generated Pokedex entries",
    list(st.session_state["entries"])
)

with st.form("my_form"):

    user_prompt = st.text_input(f"Enter a Pokemon name to generate an entry for").title()

    submitted = st.form_submit_button("Submit")
    if submitted and user_prompt.strip():
        
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
                ]
        )

        entry = json.loads(response.choices[0].message.content)
        show_pokedex_entry(entry)