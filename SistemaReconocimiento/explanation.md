# Sistema de Reconocimiento Facial — Explicación del Sistema

## Visión General

Aplicación de escritorio para reconocimiento facial en tiempo real construida con Python, InsightFace, OpenCV, SQLite y Tkinter. Permite registrar personas con video de entrenamiento, generar embeddings faciales y reconocerlas en vivo a través de una cámara web, con registro automático de eventos, estadísticas y control de acceso por operador.

---

## Arquitectura

El sistema sigue una arquitectura modular con separación clara de responsabilidades:

```
SistemaReconocimiento/
├── app.py                  # Punto de entrada e inicialización
├── config/                 # Configuración centralizada
├── database/               # Acceso a datos SQLite
├── cv/                     # Visión por computadora (detección, reconocimiento, cámara)
├── models/                 # Entrenamiento de embeddings desde video
├── services/               # Lógica de negocio (servicios)
├── gui/                    # Interfaz gráfica (Tkinter)
├── utils/                  # Utilidades (logging, imagen, archivos)
├── data/                   # Almacenamiento de archivos (videos, fotos, capturas)
├── logs/                   # Archivos de log e imágenes de eventos
└── tests/                  # Pruebas unitarias
```

La comunicación entre capas sigue inyección de dependencias: `app.py` crea todos los objetos y los conecta manualmente, sin acoplamiento directo entre módulos.

---

## Directorio `config/`

### `settings.py`
Clase singleton `Settings` que gestiona toda la configuración del sistema.

| Método / Propiedad | Función |
|---|---|
| `get(clave, ...)` | Obtiene un valor anidado del JSON de configuración |
| `set(valor, clave, ...)` | Establece un valor anidado |
| `save()` | Guarda los cambios en `config.json` |
| `confidence_threshold` | Umbral mínimo de similitud para considerar una coincidencia (0.4 por defecto) |
| `min_log_interval_minutes` | Minutos mínimos entre registros consecutivos del mismo usuario (5) |
| `camera_device_id` | Índice del dispositivo de cámara (0 por defecto) |
| `model_name` | Nombre del modelo InsightFace a utilizar (`buffalo_s`) |
| `model_providers` | Lista de proveedores de inferencia (CUDA > CPU) |
| `new_videos_path` / `trained_videos_path` | Rutas para videos pendientes y entrenados |

### `config.json`
Archivo JSON con la configuración persistente. Se fusiona con los valores por defecto definidos en `settings.py`.

---

## Directorio `database/`

### `database.py`
Clase singleton `Database` que maneja toda la comunicación con SQLite.

| Método | Función |
|---|---|
| `add_user(código, nombres, apellidos, estado, foto)` | Inserta un nuevo usuario en la tabla `users` |
| `get_user(id, código)` | Obtiene un usuario por ID o código institucional |
| `get_all_users(solo_no_entrenados)` | Lista todos los usuarios, opcionalmente solo los que no tienen embedding |
| `get_all_embeddings()` | Recupera todos los usuarios con embedding, deserializando el BLOB a `numpy.float32` |
| `update_embedding(id_usuario, embedding)` | Almacena el embedding como BLOB y registra la fecha de entrenamiento |
| `update_user(id, **campos)` | Actualiza dinámicamente campos permitidos de un usuario |
| `delete_user(id)` | Elimina un usuario de la base de datos |
| `add_log(fecha, hora, ...)` | Inserta un registro de evento en la tabla `logs` |
| `get_last_log(código)` | Obtiene el último registro de log para un código (para la regla de 5 minutos) |
| `get_logs()` | Consulta logs con filtros opcionales (tipo, fecha) y paginación |
| `get_logs_by_day()` / `get_logs_by_month()` | Agrupa logs por día o mes para estadísticas |

### `schema.sql`
Define el esquema de la base de datos:

- **users**: `id`, `code` (único), `names`, `last_names`, `status`, `photo_path`, `embedding` (BLOB), `training_date`, `created_at`
- **logs**: `id`, `date`, `time`, `code`, `name`, `person_type`, `status`, `decision`, `confidence`, `image_path`, `created_at`
- **config**: `key` (PK), `value`

---

## Directorio `cv/` (Visión por Computadora)

### `detector.py` — `FaceDetector`

| Método | Función |
|---|---|
| `detect(imagen)` | Ejecuta InsightFace sobre la imagen. Devuelve lista de rostros detectados, cada uno con: `bbox`, `landmarks`, `det_score`, `embedding` |
| `detect_best(imagen)` | Retorna el rostro con mayor confianza (útil para entrenamiento) |

Dependencia: Recibe una instancia de `insightface.app.FaceAnalysis` ya inicializada.

### `recognizer.py` — `FaceRecognizer`

| Método | Función |
|---|---|
| `match(embedding, galería)` | Calcula similitud coseno contra todos los embeddings almacenados. Retorna el mejor match si supera el umbral configurado |
| `compare(emb1, emb2)` | Similitud coseno entre dos embeddings individuales |

La galería es una lista de diccionarios con embedding, cargada desde la base de datos y cachead en memoria.

### `camera.py` — `Camera`

| Método | Función |
|---|---|
| `start()` | Abre la cámara con OpenCV `VideoCapture` e inicia un hilo daemon de captura continua |
| `stop()` | Detiene el hilo y libera la cámara |
| `get_frame(timeout)` | Retorna una copia del último frame capturado (thread-safe) |
| `read()` | Lectura directa bloqueante (sin el hilo de captura) |

La cámara se ejecuta en un hilo separado para no bloquear la interfaz ni el reconocimiento.

### `preprocessing.py` — `Preprocessor`

| Método | Función |
|---|---|
| `normalize_illumination(imagen)` | Aplica CLAHE para normalizar iluminación |
| `denoise(imagen)` | Elimina ruido con fastNlMeansDenoising |
| `enhance(imagen)` | Compone denoising + normalización |
| `extract_frames_from_video(ruta, max_frames, intervalo)` | Extrae frames de un video saltando cada N frames, usando `grab()`/`retrieve()` para eficiencia |
| `crop_and_align(imagen, landmarks, tamaño)` | Alinea el rostro usando los ojos como referencia (rotación afín) y redimensiona |

---

## Directorio `models/`

### `trainer.py` — `Trainer`

| Método | Función |
|---|---|
| `train_user_from_video(id_usuario, ruta_video)` | Extrae frames del video, detecta rostros, promedia los embeddings, normaliza y almacena en base de datos |
| `train_new_users(callback_progreso)` | Itera sobre usuarios sin embedding, busca su video en `data/new_videos/`, entrena y mueve el video a `data/trained_videos/` |
| `_find_video(código)` | Busca el archivo de video por código del usuario en varios formatos (.mp4, .avi, .mov, .mkv, .webm) |

El entrenamiento:
1. Extrae hasta 100 frames del video (configurable)
2. Detecta rostros en cada frame (solo si `det_score >= 0.5`)
3. Acumula los embeddings
4. Calcula el embedding promedio
5. Normaliza y almacena en la base de datos
6. Mueve el video a `trained_videos` para no reprocesarlo

Solo se entrenan usuarios nuevos; los existentes no se ven afectados.

---

## Directorio `services/` (Lógica de Negocio)

### `user_service.py` — `UserService`

| Método | Función |
|---|---|
| `register_user(código, nombres, apellidos, estado, foto, ruta_foto)` | Valida unicidad, guarda la foto representativa, inserta en BD |
| `get_user(código, id)` | Consulta un usuario |
| `get_all_users()` | Lista todos los usuarios |
| `update_user(id, **campos)` | Actualiza datos del usuario |
| `delete_user(id)` | Elimina usuario |
| `user_exists(código)` | Verifica si ya existe |

### `training_service.py` — `TrainingService`

| Método | Función |
|---|---|
| `train_new_users(callback_progreso, callback_final)` | Lanza el entrenamiento en un hilo separado para no bloquear la GUI |
| `is_running` | Indica si hay un entrenamiento en curso |

### `recognition_service.py` — `RecognitionService`

| Método | Función |
|---|---|
| `start()` | Inicia la cámara, carga la galería de embeddings, lanza el hilo de reconocimiento |
| `stop()` | Detiene cámara y el hilo |
| `reload_gallery()` | Recarga los embeddings desde la BD (útil después de entrenar) |
| `handle_decision(evento, decisión)` | Registra la decisión del operador en el log |
| `event_queue` | Cola FIFO thread-safe donde se publican los eventos de reconocimiento |

El flujo interno:
1. El hilo de reconocimiento captura frames de la cámara
2. Cada N frames (2), ejecuta detección facial
3. Por cada rostro detectado, extrae el embedding
4. Compara contra la galería usando similitud coseno
5. Si hay match y supera el umbral: crea evento `active` o `inactive`
6. Si no hay match: crea evento `unknown`
7. Publica el evento en la cola para que la GUI lo procese

### `log_service.py` — `LogService`

| Método | Función |
|---|---|
| `register_event(código, nombre, tipo, estado, decisión, confianza, imagen, forzar)` | Crea un registro de evento en BD con control de duplicados |
| `get_logs()` | Consulta logs con filtros |

Regla de duplicados:
- Para personal activo: si el último registro del mismo código ocurrió hace menos de 5 minutos, se descarta
- Para inactivos y desconocidos: siempre se registra (cuando el operador decide)

Guardado de imágenes:
- Activos: solo cuando se crea el registro (primera detección en la ventana de 5 min)
- Inactivos/Desconocidos: solo cuando el operador hace clic en Permitir/Denegar

### `statistics_service.py` — `StatisticsService`

| Método | Función |
|---|---|
| `get_summary()` | Totales: ingresos, activos, inactivos, desconocidos permitidos/denegados |
| `get_entries_by_day(días)` | Ingresos agrupados por día (últimos N días) |
| `get_entries_by_month(meses)` | Ingresos agrupados por mes |
| `export_to_csv(ruta)` | Exporta logs a CSV |

---

## Directorio `gui/` (Interfaz Gráfica)

### `main_window.py` — `MainWindow`

Ventana principal dividida en:

```
┌──────────────────────────────────────────────┐
│  Toolbar: Registrar | Entrenar | Iniciar    │
│           Ver logs | Estadísticas | Admin    │
├──────────────────────┬───────────────────────┤
│                      │  InfoPanel            │
│   VideoFeed          │  - Foto               │
│   (Cámara en vivo)   │  - Nombre             │
│                      │  - Código             │
│                      │  - Estado             │
│                      │  - Confianza          │
│                      │                       │
│                      │  ActionButtons        │
│                      │  [Permitir] [Denegar] │
├──────────────────────┴───────────────────────┤
│  Status bar                                   │
└──────────────────────────────────────────────┘
```

| Método | Función |
|---|---|
| `_start_recognition()` | Inicia cámara + reconocimiento, comienza a poller la cola de eventos |
| `_stop_recognition()` | Detiene todo y limpia la interfaz |
| `_poll_queue()` | Cada 50ms revisa la cola de eventos y actualiza la interfaz |
| `_process_event(evento)` | Según el tipo: activo (auto-permitir), inactivo (mostrar botones), desconocido (mostrar botones) |
| `_allow_entry()` / `_deny_entry()` | Maneja la decisión del operador |

### `register_window.py` — `RegisterWindow`

Formulario modal para registrar nuevos usuarios. Campos:
- Código institucional
- Nombres y apellidos
- Estado (Activo/Inactivo)
- Selección de fotografía (opcional)
- Selección de video de entrenamiento (obligatorio)

Al guardar: registra en BD y copia el video a `data/new_videos/`.

### `admin_window.py` — `AdminWindow`

Panel de administración con tabla de usuarios, filtros (código, nombre, estado) y acciones:
- Cambiar estado (Activo ↔ Inactivo)
- Editar nombres/apellidos
- Actualizar fotografía
- Eliminar usuario (con confirmación)

### `logs_window.py` — `LogsWindow`

Visualización de logs con filtro por tipo de persona. Tabla con: ID, fecha, hora, código, nombre, tipo, estado, decisión, confianza, ruta de imagen.

### `statistics_window.py` — `StatisticsWindow`

Panel de estadísticas con:
- Resumen numérico (totales)
- Gráfico de barras ASCII de ingresos por día (últimos 30 días)

### `widgets.py`

| Clase | Función |
|---|---|
| `VideoFeed` | Canvas de Tkinter que muestra frames de video en tiempo real |
| `InfoPanel` | Panel con foto del usuario reconocido y campos de información |
| `ActionButtons` | Botones Permitir/Denegar, ocultos por defecto |

---

## Directorio `utils/`

### `logger.py`
Configuración centralizada de logging con formato:
```
2025-01-01 12:00:00 | INFO     | sistema_reconocimiento.services.log | Log saved: Personal activo | 20224036C | auto | conf=0.923
```
Escribe a archivo (`logs/system.log`) y consola simultáneamente.

### `image_utils.py`
Utilidades de conversión y procesamiento de imágenes:
- `cv2_to_pil()` / `pil_to_cv2()`: conversión entre OpenCV y PIL
- `resize_image()`: redimensiona manteniendo aspecto
- `crop_face()`: recorta rostro usando bounding box con margen
- `draw_detection()`: dibuja rectángulo y etiqueta en el frame
- `frame_to_tk()`: convierte frame OpenCV a PhotoImage de Tkinter

### `file_utils.py`
Operaciones de archivos con creación automática de directorios:
- `ensure_dir()`: crea directorio si no existe
- `safe_copy()` / `safe_move()`: copia/mueve archivos
- `unique_filename()`: genera nombre único para evitar sobrescrituras

### `helpers.py`
Funciones matemáticas y de tiempo:
- `cosine_similarity()`: similitud coseno con normalización L2
- `normalize_vector()`: normalización L2 de vectores
- `timestamp_now()` / `date_now()` / `time_now()`: timestamps formateados
- `minutes_between()`: diferencia en minutos entre dos timestamps

---

## Flujo del Sistema

### 1. Inicio
```
app.py
  ├── Cargar configuración (Settings singleton)
  ├── Inicializar logging
  ├── Conectar base de datos SQLite (Database singleton)
  ├── Cargar modelo InsightFace (descarga automática si es primera vez)
  ├── Crear componentes CV: FaceDetector, FaceRecognizer, Camera
  ├── Crear servicios: UserService, TrainingService, RecognitionService, LogService, StatisticsService
  └── Lanzar MainWindow (Tkinter)
```

### 2. Registro de usuario
```
Usuario completa formulario →
RegisterWindow._save()
  ├── UserService.register_user() → INSERT en users
  ├── Copiar video a data/new_videos/{codigo}.mp4
  └── Cerrar ventana
```

### 3. Entrenamiento
```
Usuario hace clic en "Entrenar nuevos usuarios" →
TrainingService.train_new_users() [hilo separado]
  └── Trainer.train_new_users()
        ├── Obtener usuarios sin embedding (embedding IS NULL)
        ├── Por cada usuario:
        │     ├── Buscar video en data/new_videos/
        │     ├── Extraer frames (hasta 100, cada 5 frames)
        │     ├── Detectar rostros en cada frame
        │     ├── Promediar embeddings
        │     ├── Guardar embedding en base de datos
        │     └── Mover video a data/trained_videos/
        └── Mostrar resumen al usuario
```

### 4. Reconocimiento en tiempo real
```
Usuario hace clic en "Iniciar reconocimiento" →
RecognitionService.start()
  ├── Camera.start() → hilo de captura continua
  ├── reload_gallery() → carga embeddings desde BD
  └── Hilo de reconocimiento:
        while activo:
          frame = camera.get_frame()
          faces = detector.detect(frame)
          for cada rostro:
            embedding = extraer de face
            match = recognizer.match(embedding, gallery)
            if match:
              Si estado = Activo → evento "active"
              Si estado = Inactivo → evento "inactive"
            else:
              evento "unknown"
            publicar evento en cola

  GUI (main thread, cada 50ms):
    _poll_queue():
      evento = cola.get()
      actualizar VideoFeed con el frame
      si evento == "active":
        InfoPanel: mostrar datos
        LogService: registrar "Permitir automático"
        (no mostrar botones)
      si evento == "inactive":
        InfoPanel: mostrar datos
        ActionButtons: mostrar [Permitir] [Denegar]
      si evento == "unknown":
        InfoPanel: mostrar "Desconocido"
        ActionButtons: mostrar [Permitir] [Denegar]
```

### 5. Decisión del operador (inactivos y desconocidos)
```
Operador hace clic en "Permitir ingreso":
  RecognitionService.handle_decision(evento, "Permitir")
    └── LogService.register_event(... force=True)
          ├── Guardar imagen del rostro (solo en decisión)
          └── INSERT en tabla logs

Operador hace clic en "Denegar ingreso":
  RecognitionService.handle_decision(evento, "Denegar")
    └── (mismo flujo, cambia decisión)
```

### 6. Regla de duplicación
```
Para personal activo:
  register_event() →
    if no force AND person_type == "Personal activo":
      último_log = get_last_log(código)
      if minutos_desde_último_log < 5:
        return None (no guardar)
    (guardar normalmente)
```

---

## Modelo de IA y Embeddings

El sistema utiliza **InsightFace** con el modelo **buffalo_s**, que proporciona:
- Detección de rostros (modelo `det_500m.onnx`)
- Extracción de landmarks faciales (modelo `1k3d68.onnx`, `2d106det.onnx`)
- Embeddings faciales de 512 dimensiones (modelo `w600k_mbf.onnx`)

Los embeddings se almacenan en SQLite como BLOBs de `numpy.float32`. La comparación usa similitud coseno con un umbral configurable (0.4 por defecto).

**Ventaja de este diseño**: cambiar el modelo de reconocimiento solo implica reemplazar el modelo ONNX y ajustar el extractor de embeddings; el resto del sistema (BD, GUI, servicios, lógica de logs) permanece intacto.

---

## Hilos y Concurrencia

| Hilo | Propósito |
|---|---|
| **Principal (GUI)** | Tkinter mainloop, eventos de usuario, polling de cola |
| **Cámara** (daemon) | Captura continua de frames, actualiza frame más reciente |
| **Reconocimiento** (daemon) | Procesa frames, detecta rostros, compara embeddings, publica eventos en cola |
| **Entrenamiento** (daemon) | Procesa videos y genera embeddings, creado bajo demanda |

La comunicación entre hilos usa:
- `queue.Queue` para eventos de reconocimiento → GUI
- `threading.Lock` para acceso seguro al frame de cámara
- `threading.Event` para notificar disponibilidad de frame
- `root.after()` para integrar el polling con el event loop de Tkinter

---

## Archivos de Configuración Clave

| Archivo | Propósito |
|---|---|
| `config/config.json` | Configuración persistente (BD, cámara, umbrales, rutas) |
| `database/schema.sql` | Esquema de la base de datos SQLite |
| `.gitignore` | Exclusiones para el repositorio (modelos grandes, BD, videos, logs) |
| `requirements.txt` | Dependencias Python |

---

## Dependencias

```
opencv-python       # Captura de video y procesamiento de imágenes
insightface         # Detección y reconocimiento facial
onnxruntime         # Motor de inferencia para modelos ONNX
numpy               # Operaciones numéricas y vectores
Pillow              # Conversión de imágenes para Tkinter
pandas              # Agregación de datos para estadísticas
scikit-learn        # Utilidades adicionales (cosine_similarity备用)
```
