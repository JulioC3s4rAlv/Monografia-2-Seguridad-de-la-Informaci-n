# Sistema de Reconocimiento Facial

Aplicación de escritorio para reconocimiento facial en tiempo real utilizando InsightFace y visión por computadora.

## Requisitos

- Python 3.12+
- Cámara web
- Windows/Linux

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

## Estructura del proyecto

```
SistemaReconocimiento/
├── app.py                  # Punto de entrada
├── config/                 # Configuración
├── cv/                     # Visión por computadora
├── database/               # Base de datos SQLite
├── gui/                    # Interfaz gráfica
├── models/                 # Modelos y entrenamiento
├── services/               # Lógica de negocio
├── utils/                  # Utilidades
└── data/                   # Datos de usuario
```

## Funcionalidades

- **Registro**: Registrar personas con código, nombre, foto y video
- **Entrenamiento**: Extraer embeddings faciales desde video
- **Reconocimiento**: Identificar personas en tiempo real por cámara
- **Logs**: Registro detallado de todos los eventos
- **Estadísticas**: Reportes de ingresos y actividad
