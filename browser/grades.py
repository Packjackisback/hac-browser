from api import main
import json
from datetime import datetime
from os import path

# get a dict of classes with a list of assignments for the year as the assignments, sorted by date, and weighting has the weighting
def get_grades(username, password, use_sample=False):
    if use_sample:
        f = open(path.relpath("./browser/sample.json"), 'r')
        grades_json = json.load(f)
    else:
        grades_json = json.loads(main.assignments(username, password))
        with open("sample.json", "w") as outfile:
            json.dump(grades_json, outfile, indent=4)
    classes = {}
    for class_name in grades_json:
        classes[class_name] = {}
        classes[class_name]['assignments'] = []
        for assignment in grades_json[class_name]['assignments'][1:]:
            classes[class_name]['assignments'].append(assignment)

        classes[class_name]['weighting'] = {}
        for weight in grades_json[class_name]['categories'][1:]:
            classes[class_name]['weighting'][weight[0]] = float(weight[4])

    for class_name in classes:
        classes[class_name]['assignments'] = sorted(classes[class_name]['assignments'], key=lambda assignment: datetime.strptime(assignment[0], '%m/%d/%Y'))
    return classes

# takes a list of assignments in the format:
# date graded, date assigned, name, category, grade, max, idk, grade, max, grade%
# and returns the grade percentage given the weight
def calculate_grades(assignments: list, major: float, minor: float, other: float, total: float) -> float | None:
    majors, minors, others = [], [], []

    for assignment in assignments:
        if assignment[3] == "Major" and assignment[4]:
            majors.append(float(assignment[4]))
        elif assignment[3] == "Minor" and assignment[4]:
            minors.append(float(assignment[4]))
        elif assignment[3] == "Other" and assignment[4]:
            others.append(float(assignment[4]))

    if len(others) > 1:
        others = sorted(others)[1:]

    major_avg = sum(majors) / len(majors) if majors else 0
    minor_avg = sum(minors) / len(minors) if minors else 0
    other_avg = sum(others) / len(others) if others else 0

    weights = {}
    if majors: weights['major'] = major
    if minors: weights['minor'] = minor
    if others: weights['other'] = other

    if not weights:
        return None 

    weight_sum = sum(weights.values())
    grade = 0
    if 'major' in weights: grade += major_avg * major
    if 'minor' in weights: grade += minor_avg * minor
    if 'other' in weights: grade += other_avg * other

    return grade / (weight_sum * 100)