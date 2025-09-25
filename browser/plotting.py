import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import grades
from datetime import datetime

st.set_page_config(page_title="HAC PLOTTER", layout="wide")

@st.cache_data
def get_grades_cached(username: str, password: str, use_sample=False):
    return grades.get_grades(username, password, use_sample=use_sample)

def calculate_grade_over_time(assignments, major, minor, other, total):
    dates = []
    grade_values = []

    for i in range(len(assignments)):
        current_assignments = assignments[: i + 1]
        grade = grades.calculate_grades(current_assignments, major, minor, other, total)
        date_str = current_assignments[-1][0]
        try:
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            continue 
        dates.append(date_obj)
        grade_values.append(grade * 100)

    return dates, grade_values

st.title("Grade Trend Viewer")
use_sample = st.checkbox("Use Sample Grades", value=False)

if not use_sample:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
else:
    username = ""
    password = ""
if (username and password) or use_sample:
    grade_object = get_grades_cached(username, password, use_sample)

    classes = [c for c in grade_object if grade_object[c]["assignments"]]
    if not classes:
        st.warning("No classes with assignments found.")
        st.stop()

    selected_classes = st.multiselect("Select classes to plot", classes, default=classes)

    if not selected_classes:
        st.warning("Select at least one class to plot.")
        st.stop()

    fig, ax = plt.subplots(figsize=(10, 6))

    for class_name in selected_classes:
        assignments = grade_object[class_name]["assignments"]
        weighting = grade_object[class_name].get("weighting", {})

        major = weighting.get("Major", 0)
        minor = weighting.get("Minor", 0)
        other = weighting.get("Other", 0)
        total = weighting.get("Total Points:", 100)

        dates, grades_list = calculate_grade_over_time(assignments, major, minor, other, total)
        if not dates:
            continue

        ax.plot(dates, grades_list, marker="o", label=class_name)

    ax.set_xlabel("Date")
    ax.set_ylabel("Grade (%)")
    ax.set_title("Grade Trend Over Time")
    ax.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()

    st.pyplot(fig)

