from flask import Flask, jsonify, render_template, request

from services.route_service import (
    RouteServiceError,
    build_optimized_route,
)


app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(
        {
            "estado": "Online",
            "proyecto": "Smart Mobility",
        }
    )


@app.post("/optimizar")
def optimizar():
    data = request.get_json(silent=True) or {}

    origin = str(data.get("origen", "")).strip()
    destinations = data.get("destinos", [])

    if not origin:
        return jsonify(
            {"error": "Debe ingresar un punto de origen."}
        ), 400

    if not isinstance(destinations, list):
        return jsonify(
            {"error": "El campo destinos debe ser una lista."}
        ), 400

    clean_destinations = [
        str(destination).strip()
        for destination in destinations
        if str(destination).strip()
    ]

    if len(clean_destinations) < 2:
        return jsonify(
            {"error": "Debe ingresar al menos dos destinos."}
        ), 400

    try:
        result = build_optimized_route(
            origin=origin,
            destinations=clean_destinations,
        )

        return jsonify(result)

    except RouteServiceError as exc:
        return jsonify({"error": str(exc)}), 502

    except Exception:
        app.logger.exception(
            "Error inesperado al optimizar la ruta"
        )

        return jsonify(
            {
                "error": (
                    "Ocurrió un error inesperado al procesar la ruta."
                )
            }
        ), 500


if __name__ == "__main__":
    app.run(debug=True)