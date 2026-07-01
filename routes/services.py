from flask import Blueprint, render_template

services_bp = Blueprint("services", __name__)


@services_bp.route("/services")
def services():
    return render_template("services.html")


@services_bp.route("/services/<service_name>")
def service_detail(service_name):

    services = {
        "photo-editing": {
            "title": "Photo Editing",
            "description": "Professional photo editing and retouching."
        },
        "video-editing": {
            "title": "Video Editing",
            "description": "Professional cinematic video editing."
        },
        "reels-editing": {
            "title": "Reels Editing",
            "description": "Instagram reels and short-form content."
        },
        "thumbnail-design": {
            "title": "Thumbnail Design",
            "description": "YouTube thumbnails and posters."
        }
    }

    service = services.get(service_name)

    if service is None:
        return "Service not found", 404

    return render_template(
        "service_detail.html",
        service=service,
        service_slug=service_name
    )
