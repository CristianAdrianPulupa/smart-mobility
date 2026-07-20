console.log("SCRIPT NUEVO CARGADO");
const form = document.getElementById("route-form");
const originInput = document.getElementById("origin");
const destinationsContainer = document.getElementById(
    "destinations-container"
);
const addDestinationButton = document.getElementById("add-destination");
const optimizeButton = document.getElementById("optimize-route");

const message = document.getElementById("message");
const resultsSection = document.getElementById("results");
const mapSection = document.getElementById("map-section");

const totalDistance = document.getElementById("total-distance");
const totalDuration = document.getElementById("total-duration");
const routeOrder = document.getElementById("route-order");

let destinationCount = 2;
let map = null;
let routeLayer = null;
let markersLayer = null;


function showMessage(text, type = "error") {
    message.textContent = text;
    message.classList.remove(
        "hidden",
        "message-error",
        "message-success"
    );

    if (type === "success") {
        message.classList.add("message-success");
    } else {
        message.classList.add("message-error");
    }
}


function hideMessage() {
    message.textContent = "";
    message.classList.add("hidden");
    message.classList.remove(
        "message-error",
        "message-success"
    );
}


function createDestinationField() {
    destinationCount += 1;

    const group = document.createElement("div");
    group.className = "field-group destination-group";

    const label = document.createElement("label");
    label.setAttribute(
        "for",
        `destination-${destinationCount}`
    );
    label.textContent = `Destino ${destinationCount}`;

    const input = document.createElement("input");
    input.id = `destination-${destinationCount}`;
    input.className = "destination-input";
    input.type = "text";
    input.placeholder = "Ingrese una dirección";
    input.autocomplete = "off";

    group.appendChild(label);
    group.appendChild(input);

    destinationsContainer.appendChild(group);
}


function getDestinations() {
    return Array.from(
        document.querySelectorAll(".destination-input")
    )
        .map((input) => input.value.trim())
        .filter((value) => value !== "");
}


function renderRouteOrder(addresses) {
    routeOrder.innerHTML = "";

    addresses.forEach((address) => {
        const item = document.createElement("li");
        item.textContent = address;
        routeOrder.appendChild(item);
    });
}


function renderMap(geometry, coordinates, addresses) {
    const mapElement = document.getElementById("map");

    if (!geometry || !Array.isArray(geometry.coordinates)) {
        throw new Error(
            "No se recibió una geometría válida para mostrar el mapa."
        );
    }

    if (!Array.isArray(coordinates) || coordinates.length === 0) {
        throw new Error(
            "No se recibieron coordenadas válidas para el mapa."
        );
    }

    if (!map) {
        // Elimina el texto “El mapa aparecerá aquí” solamente
        // durante la primera inicialización.
        mapElement.textContent = "";

        map = L.map("map");

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
                attribution: "&copy; OpenStreetMap contributors",
            }
        ).addTo(map);
    }

    if (routeLayer) {
        map.removeLayer(routeLayer);
        routeLayer = null;
    }

    if (markersLayer) {
        map.removeLayer(markersLayer);
        markersLayer = null;
    }

    routeLayer = L.geoJSON(
        {
            type: "Feature",
            properties: {},
            geometry: geometry,
        },
        {
            style: {
                weight: 6,
                opacity: 0.85,
            },
        }
    ).addTo(map);

    markersLayer = L.layerGroup();

    coordinates.forEach((coordinate, index) => {
        const longitude = coordinate[0];
        const latitude = coordinate[1];

        const title =
            index === 0
                ? "Punto de origen"
                : `Parada ${index}`;

        const marker = L.marker([
            latitude,
            longitude,
        ]);

        marker.bindPopup(
            `<strong>${title}</strong><br>${addresses[index]}`
        );

        marker.addTo(markersLayer);
    });

    markersLayer.addTo(map);

    const bounds = routeLayer.getBounds();

    if (bounds.isValid()) {
        map.fitBounds(bounds, {
            padding: [30, 30],
        });
    }

    setTimeout(() => {
        map.invalidateSize();
    }, 200);
}


addDestinationButton.addEventListener("click", () => {
    createDestinationField();
});


form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideMessage();

    const origin = originInput.value.trim();
    const destinations = getDestinations();

    if (!origin) {
        showMessage("Debe ingresar un punto de origen.");
        return;
    }

    if (destinations.length < 2) {
        showMessage("Debe ingresar al menos dos destinos.");
        return;
    }

    optimizeButton.disabled = true;
    optimizeButton.textContent = "Calculando...";

    try {
        const response = await fetch("/optimizar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                origen: origin,
                destinos: destinations,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "No fue posible optimizar la ruta."
            );
        }

        totalDistance.textContent =
            `${data.distancia_total_km} km`;

        totalDuration.textContent =
            `${data.tiempo_estimado_min} min`;

        renderRouteOrder(data.ruta_optimizada);

        resultsSection.classList.remove("hidden");
        mapSection.classList.remove("hidden");
        console.log("Geometría recibida:", data.geometria);
        console.log("Coordenadas recibidas:", data.coordenadas);

        renderMap(
            data.geometria,
            data.coordenadas,
            data.ruta_optimizada
        );

        showMessage(
            "La ruta fue optimizada correctamente.",
            "success"
        );

    } catch (error) {
        resultsSection.classList.add("hidden");
        mapSection.classList.add("hidden");

        showMessage(error.message);
    } finally {
        optimizeButton.disabled = false;
        optimizeButton.textContent = "Optimizar ruta";
    }
});