# Smart Mobility

## Descripción

Smart Mobility es un sistema web desarrollado en Python y Flask que permite optimizar rutas de entrega mediante el ingreso de un punto de origen y múltiples destinos. La aplicación calcula el recorrido más eficiente y muestra la ruta sobre un mapa interactivo, además de estimar la distancia y el tiempo de viaje.

## Características

- Optimización de rutas de entrega.
- Ingreso dinámico de múltiples destinos.
- Visualización de la ruta en un mapa interactivo.
- Cálculo de distancia total.
- Estimación del tiempo de recorrido.
- Interfaz web sencilla e intuitiva.

## Tecnologías utilizadas

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- Leaflet
- OpenStreetMap
- OpenRouteService
-Google Maps API 

## Estructura del proyecto

```text
smart-mobility/
│
├── services/
├── static/
├── templates/
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/CristianAdrianPulupa/smart-mobility.git
```

Ingresar al proyecto:

```bash
cd smart-mobility
```

Crear el entorno virtual:

```bash
python -m venv venv
```

Activarlo:

Windows

```bash
venv\Scripts\activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Crear el archivo `.env`:

```env
GoogleMaps_API_KEY=********************
```

Ejecutar la aplicación:

```bash
python app.py
```

Abrir en el navegador:

```
http://127.0.0.1:5000
```

## Autores

Cristian Pulupa

Universidad Central del Ecuador

Carrera de Ingeniería en Sistemas

2026