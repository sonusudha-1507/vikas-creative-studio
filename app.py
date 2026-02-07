from flask import Flask, render_template, request
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Upload configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "mov", "zip", "pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB limit

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template("home.html", year=datetime.now().year)


@app.route("/start-project", methods=["GET", "POST"])
def start_project():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        project_type = request.form.get("project_type")
        description = request.form.get("description")

        uploaded_file = request.files.get("project_file")

        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            uploaded_file.save(file_path)
        else:
            filename = None

        print("New Project Request:")
        print(name, email, project_type, description, filename)

        return render_template(
            "start_project.html",
            year=datetime.now().year,
            success=True
        )

    return render_template("start_project.html", year=datetime.now().year)


if __name__ == "__main__":
    app.run(debug=True)

