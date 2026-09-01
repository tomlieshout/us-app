from flask import Blueprint, current_app, render_template, send_from_directory

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def index():
    return render_template("index.html")


@pages_bp.get("/sw.js")
def service_worker():
    # Served from the root path (not /static/) so its default scope covers
    # the whole app rather than just /static/.
    response = send_from_directory(current_app.static_folder + "/js", "service-worker.js")
    response.headers["Content-Type"] = "application/javascript"
    return response
