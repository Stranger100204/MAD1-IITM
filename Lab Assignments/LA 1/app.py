import csv
import matplotlib.pyplot as plt
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=["GET", "POST"])
def index():

    if request.method == "GET":
        return render_template("index.html")

    if request.method == "POST":

        selected_id = request.form.get("ID")
        entered_value = request.form.get("id_value")

        if entered_value is None or entered_value.strip() == "":
            return render_template("error.html")

        rows = []

        with open("data.csv", "r", newline="") as file:
            reader = csv.reader(file)
            next(reader)

            for row in reader:
                row = [item.strip() for item in row]
                rows.append(row)

        if selected_id == "student_id":

            student_rows = []
            total_marks = 0

            for row in rows:
                if row[0] == entered_value:
                    student_rows.append(row)
                    total_marks += int(row[2])

            if len(student_rows) == 0:
                return render_template("error.html")

            return render_template(
                "student.html",
                data=student_rows,
                total=total_marks
            )

        elif selected_id == "course_id":

            course_marks = []

            for row in rows:
                if row[1] == entered_value:
                    course_marks.append(int(row[2]))

            if len(course_marks) == 0:
                return render_template("error.html")

            avg_marks = sum(course_marks) / len(course_marks)
            max_marks = max(course_marks)

            plt.hist(course_marks)
            plt.xlabel("Marks")
            plt.ylabel("Frequency")
            plt.title("Marks Distribution")

            plt.savefig("static/histogram.png")
            plt.close()

            return render_template(
                "course.html",
                average=avg_marks,
                maximum=max_marks
            )

        return render_template("error.html")


if __name__ == "__main__":
    app.run(debug=True)