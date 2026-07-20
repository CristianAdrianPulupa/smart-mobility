from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENROUTESERVICE_API_KEY")

BASE_URL = "https://api.openrouteservice.org"
GEOCODING_URL = f"{BASE_URL}/geocode/search"
OPTIMIZATION_URL = f"{BASE_URL}/optimization"
DIRECTIONS_URL = (
    f"{BASE_URL}/v2/directions/driving-car/geojson"
)

REQUEST_TIMEOUT = 30


class RouteServiceError(Exception):
    """Error controlado al comunicarse con OpenRouteService."""


def _get_headers() -> dict[str, str]:
    if not API_KEY:
        raise RouteServiceError(
            "No se encontró OPENROUTESERVICE_API_KEY en el archivo .env."
        )

    return {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def geocode_address(address: str) -> dict[str, Any]:
    """
    Convierte una dirección en coordenadas geográficas.

    OpenRouteService devuelve las coordenadas en el orden:
    [longitud, latitud].
    """
    clean_address = address.strip()

    if not clean_address:
        raise RouteServiceError("La dirección está vacía.")

    if not API_KEY:
        raise RouteServiceError(
            "No se encontró OPENROUTESERVICE_API_KEY en el archivo .env."
        )

    try:
        response = requests.get(
            GEOCODING_URL,
            headers={
                "Authorization": API_KEY,
                "Accept": "application/json",
            },
            params={
                "text": clean_address,
                "boundary.country": "EC",
                "size": 1,
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        detail = ""

        if exc.response is not None:
            detail = exc.response.text

        raise RouteServiceError(
            f"No fue posible localizar la dirección "
            f"'{clean_address}'. Detalle: {detail}"
        ) from exc

    try:
        data = response.json()
        
    except ValueError as exc:
        raise RouteServiceError(
            "OpenRouteService devolvió una respuesta inválida."
        ) from exc

    features = data.get("features", [])

    if not features:
        raise RouteServiceError(
            f"No se encontró la dirección: {clean_address}"
        )

    feature = features[0]
    geometry = feature.get("geometry", {})
    coordinates = geometry.get("coordinates")

    if not coordinates or len(coordinates) != 2:
        raise RouteServiceError(
            f"La dirección no devolvió coordenadas válidas: "
            f"{clean_address}"
        )

    properties = feature.get("properties", {})

    return {
        "direccion_ingresada": clean_address,
        "direccion_encontrada": properties.get(
            "label",
            clean_address,
        ),
        "coordenadas": coordinates,
    }


def geocode_addresses(
    addresses: list[str],
) -> list[dict[str, Any]]:
    """Geocodifica todas las direcciones ingresadas."""
    if len(addresses) < 3:
        raise RouteServiceError(
            "Se requiere un origen y al menos dos destinos."
        )

    return [
        geocode_address(address)
        for address in addresses
    ]


def optimize_delivery_order(
    locations: list[dict[str, Any]],
) -> list[int]:
    """
    Calcula el orden de entrega.

    El índice 0 corresponde al punto de origen.
    Los demás índices corresponden a los destinos.
    """
    if len(locations) < 3:
        raise RouteServiceError(
            "No existen suficientes ubicaciones para optimizar."
        )

    origin_coordinates = locations[0]["coordenadas"]

    jobs: list[dict[str, Any]] = []

    for index, location in enumerate(
        locations[1:],
        start=1,
    ):
        jobs.append(
            {
                "id": index,
                "location": location["coordenadas"],
                "description": location["direccion_encontrada"],
            }
        )

    payload = {
        "jobs": jobs,
        "vehicles": [
            {
                "id": 1,
                "profile": "driving-car",
                "start": origin_coordinates,
            }
        ],
    }

    try:
        response = requests.post(
            OPTIMIZATION_URL,
            headers=_get_headers(),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        detail = ""

        if exc.response is not None:
            detail = exc.response.text

        raise RouteServiceError(
            f"No fue posible optimizar la ruta. "
            f"Detalle: {detail}"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RouteServiceError(
            "El servicio de optimización devolvió "
            "una respuesta inválida."
        ) from exc

    routes = data.get("routes", [])

    if not routes:
        raise RouteServiceError(
            "El servicio no devolvió una ruta optimizada."
        )

    optimized_indices = [0]

    for step in routes[0].get("steps", []):
        if step.get("type") == "job":
            optimized_indices.append(step["job"])

    if len(optimized_indices) != len(locations):
        raise RouteServiceError(
            "No fue posible ordenar todos los destinos."
        )

    return optimized_indices


def calculate_route(
    ordered_locations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Obtiene el recorrido real, la distancia, el tiempo
    y la geometría GeoJSON.
    """
    coordinates = [
        location["coordenadas"]
        for location in ordered_locations
    ]

    payload = {
        "coordinates": coordinates,
        "instructions": False,
    }

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/geo+json",
    }

    try:
        response = requests.post(
            DIRECTIONS_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        detail = ""

        if exc.response is not None:
            detail = exc.response.text

        raise RouteServiceError(
            f"No fue posible calcular el recorrido. "
            f"Detalle: {detail}"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RouteServiceError(
            "El servicio devolvió una respuesta inválida."
        ) from exc

    features = data.get("features", [])

    if not features:
        raise RouteServiceError(
            "No se obtuvo la geometría del recorrido."
        )

    feature = features[0]
    properties = feature.get("properties", {})
    summary = properties.get("summary", {})
    geometry = feature.get("geometry", {})

    if not geometry.get("coordinates"):
        raise RouteServiceError(
            "La geometría recibida está vacía."
        )

    distance_meters = float(summary.get("distance", 0))
    duration_seconds = float(summary.get("duration", 0))

    return {
        "distancia_total_km": round(
            distance_meters / 1000,
            2,
        ),
        "tiempo_estimado_min": round(
            duration_seconds / 60,
        ),
        "geometria": geometry,
    }


def build_optimized_route(
    origin: str,
    destinations: list[str],
) -> dict[str, Any]:
    """Ejecuta el proceso completo de optimización."""
    addresses = [origin, *destinations]

    locations = geocode_addresses(addresses)

    optimized_indices = optimize_delivery_order(
        locations
    )

    ordered_locations = [
        locations[index]
        for index in optimized_indices
    ]

    route_data = calculate_route(
        ordered_locations
    )

    return {
        "ruta_optimizada": [
            location["direccion_encontrada"]
            for location in ordered_locations
        ],
        "coordenadas": [
            location["coordenadas"]
            for location in ordered_locations
        ],
        **route_data,
    }