import streamlit as st
from openai import OpenAI

client = OpenAI(
    api_key = "YOUR_KEY_HERE_IM_NOT_SHARING_MINE"
)
st.write("This is the best email maker ever. I LOVE writing emails.\nLooks like you need help writing an email to someone. No problem!")

name = st.text_input("What is your name? ")

recipient = st.text_input("And who are you sending this to? ")

styles = st.selectbox(
    "Pick from one of these styles.",
    [
        "Angry",
        "Formal",
        "Casual",
        "Like a child wrote it"
    ]
)

subject = st.text_input(f"What do you want to talk to {recipient} about? ")

st.write(f"From: {name} To: {recipient} Subject: {subject}\nEmail:")

system_prompt = """
Help people write emails in different styles. Use this template:
Dear name,

content

Sincerley,
name
"""
    
    
submitted = st.button("Submit")

if submitted:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"My name is {name}. Help me write an email with to {recipient}. Use the writing style: {styles}. Here is my subject: {subject}."}
        ]
    )

    st.write(response.choices[0].message.content)