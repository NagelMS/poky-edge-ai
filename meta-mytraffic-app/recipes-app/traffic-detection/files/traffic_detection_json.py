#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
 Proyecto: Deteccion de Trafico en Tiempo Real
 File: traffic_detection.py
 Autores: Nagel Mejia Segura, Wilberth GutiI©rrez Montero, I“scar Gonzanez Cambronero.
 Fecha: 2025-11-09
Descripcion:
     Este script implementa un sistema de deteccion de objetos en tiempo real
     para monitoreo de tranico utilizando TensorFlow Lite. Detecta vehiculos,
     peatones, semanoros y otros objetos relacionados con el tranico en video
     en vivo o grabado.

 Dependencias de pip:
     - tensorflow
     - opencv-python
     - numpy
     - ai-edge-litert (Opcional, si no estanpresente hace fallback a tensorflow)

==========================================================
"""

import cv2
import numpy as np
from typing import List, Tuple
import os
import argparse
import json
from datetime import datetime
from collections import defaultdict
import threading

# Usar TensorFlow Lite interpreter (Compatible con Python 3.13), en caso de no estar disponible, usar TensorFlow.
try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter


class DetectionLogger:
    """Clase para registrar detecciones en formato JSON con actualizacion continua."""

    def __init__(self, output_file: str, update_interval: int = 1, max_frames: int = 300):
        """
        Inicializar el logger de detecciones.

        Args:
            output_file: Ruta del archivo JSON de salida
            update_interval: Intervalo de frames para actualizar el archivo (default: cada frame)
            max_frames: Maximo de frames a mantener en memoria (sliding window, default: 300 = 10s @ 30fps)
        """
        self.output_file = output_file
        self.update_interval = update_interval
        self.max_frames = max_frames
        self.frame_count = 0
        self.total_frames_processed = 0
        self.detections_log = {
            "metadatos": {
                "hora_inicio": datetime.now().isoformat(),
                "ultima_actualizacion": datetime.now().isoformat(),
                "version": "1.0",
                "descripcion": "Registro de deteccion de objetos de tranico",
                "estado": "ejecutandose",
                "max_frames_almacenados": max_frames,
                "total_frames_procesados": 0
            },
            "frames": [],
            "detecciones_actuales": []  # Detecciones del frame man reciente
        }

        # Crear archivo inicial
        self._write_to_file()

    def log_frame(self, frame_number: int, timestamp: float, detections: List[dict]):
        """
        Registrar detecciones de un frame y actualizar archivo si es necesario.

        Args:
            frame_number: Número del frame
            timestamp: Timestamp en segundos desde el inicio
            detections: Lista de detecciones
        """
        frame_data = {
            "numero_frame": frame_number,
            "tiempo_segundos": timestamp,
            "fecha_hora": datetime.now().isoformat(),
            "cantidad_detecciones": len(detections),
            "detecciones": detections
        }

        # Agregar frame y mantener ventana deslizante
        self.detections_log["frames"].append(frame_data)
        if len(self.detections_log["frames"]) > self.max_frames:
            self.detections_log["frames"].pop(0)  # Eliminar frame man antiguo

        # Actualizar detecciones actuales (frame man reciente)
        self.detections_log["detecciones_actuales"] = detections

        self.frame_count += 1
        self.total_frames_processed += 1

        # Actualizar archivo segÚn el intervalo
        if self.frame_count % self.update_interval == 0:
            self._write_to_file()

    def _write_to_file(self):
        """Escribir el log actual al archivo JSON."""
        self.detections_log["metadatos"]["ultima_actualizacion"] = datetime.now(
        ).isoformat()
        self.detections_log["metadatos"]["frames_en_ventana"] = len(
            self.detections_log["frames"])
        self.detections_log["metadatos"]["total_frames_procesados"] = self.total_frames_processed

        # Escribir de forma aiomica usando archivo temporal
        temp_file = self.output_file + ".tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.detections_log, f, indent=2, ensure_ascii=False)

            # Renombrar archivo temporal al archivo final (operacion aiomica)
            os.replace(temp_file, self.output_file)
        except Exception as e:
            print(f"Error escribiendo log: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def save(self):
        """Guardar el log final y marcar como completado."""
        self.detections_log["metadatos"]["hora_fin"] = datetime.now(
        ).isoformat()
        self.detections_log["metadatos"]["estado"] = "completado"
        self._write_to_file()

        print(f"\nLog guardado en: {self.output_file}")
        print(f"  Total de frames procesados: {self.total_frames_processed}")
        print(
            f"  Frames en ventana final: {len(self.detections_log['frames'])}")


class TrafficObjectDetector:
    """
    Clase para deteccion de objetos de trafico usando TensorFlow Lite.
    """

    def __init__(self, model_path: str = None, labels_path: str = None):
        """
        Constructor para inicializar el detector.

        Args:
            model_path: ruta del modelo TFLite
            labels_path: ruta al archivo de etiquetas
        """
        # Si el usuario no proporciona una ruta de modelo, usar la predeterminada
        if model_path is None:
            default_path = os.path.join("modelos", "detect.tflite")
            if not os.path.exists(default_path):
                raise FileNotFoundError(
                    f"\n{'='*60}\n"
                    f"ERROR: Modelo no encontrado!\n"
                    f"{'='*60}\n"
                    f"Ubicacion esperada: {default_path}\n\n"
                    f"Asegúrate de que el modelo está en la ubicacion correcta.\n\n"
                    f"O especifica una ruta de modelo personalizada:\n"
                    f"  detector = TrafficObjectDetector(model_path='ruta/al/modelo.tflite')\n"
                    f"{'='*60}\n"
                )
            model_path = default_path
            print(f"Modelo encontrado: {model_path}")

        self.model_path = model_path
        self.labels_path = labels_path or os.path.join(
            "modelos", "labelmap.txt")

        # Cargar etiquetas
        self.labels = self._load_labels()

        # Inicializar intI©rprete TFLite
        self.interpreter = Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()

        # Obtener detalles de entrada y salida
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Obtener dimensiones de entrada
        self.input_shape = self.input_details[0]['shape']
        self.height = self.input_shape[1]
        self.width = self.input_shape[2]

        # Especificar clases de trafico de interI©s
        self.traffic_classes = {
            0: 'persona',
            1: 'bicicleta',
            2: 'carro',
            3: 'motocicleta',
            5: 'autobús',
            7: 'camion',
            9: 'semaforo',
            11: 'señal de alto',
            12: 'parquimetro'
        }

        self.latest_frame = None
        self.frame_lock = threading.Lock()

    def get_latest_frame(self) -> np.ndarray:
        """Obtener el último frame procesado para streaming."""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None


    def _load_labels(self) -> List[str]:
        """Cargar etiquetas desde archivo."""
        if os.path.exists(self.labels_path):
            with open(self.labels_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
        else:
            return ['person', 'bicycle', 'car', 'motorcycle', 'airplane',
                    'bus', 'train', 'truck', 'boat', 'traffic light',
                    'fire hydrant', 'stop sign', 'parking meter']

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocesar el frame para la entrada del modelo."""
        img = cv2.resize(frame, (self.width, self.height))

        # Convertir a RGB si es necesario
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Agregar dimension de lote y convertir a uint8
        input_data = np.expand_dims(img, axis=0).astype(np.uint8)

        return input_data

    def detect_objects(self, frame: np.ndarray,
                       confidence_threshold: float = 0.5) -> List[dict]:
        """
        Detectar objetos en el frame dado.

        Args:
            frame: Frame de video como un array numpy
            confidence_threshold: Confianza minima para considerar una deteccion valida

        Returns:
            Lista de detecciones con formato:
            [
                {'class_id': int,
                 'nombre_clase': str,
                 'confianza': float,
                 'caja_delimitadora': {'x_min': int, 'y_min': int, 'x_max': int, 'y_max': int}
                },
        """
        input_data = self.preprocess_frame(frame)

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()

        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        classes = self.interpreter.get_tensor(
            self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(
            self.output_details[2]['index'])[0]

        h, w = frame.shape[:2]

        # Filtrar detecciones por umbral de confianza
        detections = []
        for i in range(len(scores)):
            if scores[i] > confidence_threshold:
                class_id = int(classes[i])

                # Centrar solo en clases de tranico
                if class_id in self.traffic_classes:
                    ymin, xmin, ymax, xmax = boxes[i]

                    detection = {
                        'id_clase': class_id,
                        'nombre_clase': self.traffic_classes[class_id],
                        'confianza': float(scores[i]),
                        'caja_delimitadora': {
                            'x_min': int(xmin * w),
                            'y_min': int(ymin * h),
                            'x_max': int(xmax * w),
                            'y_max': int(ymax * h)
                        }
                    }
                    detections.append(detection)

        return detections

    def draw_detections(self, frame: np.ndarray,
                        detections: List[dict]) -> np.ndarray:
        """Dibujar las detecciones en el frame."""
        output_frame = frame.copy()

        # Mapa de colores para diferentes clases
        colors = {
            'persona': (0, 255, 0),      # Verde
            'carro': (255, 0, 0),        # Azul
            'camion': (255, 100, 0),     # Azul oscuro
            'autobús': (255, 150, 0),    # Azul claro
            'motocicleta': (0, 255, 255),  # Amarillo
            'bicicleta': (0, 200, 255),  # Naranja
            'semaforo': (0, 0, 255),     # Rojo
            'señal de alto': (0, 0, 200),  # Rojo oscuro
        }

        for det in detections:
            bbox = det['caja_delimitadora']
            class_name = det['nombre_clase']
            confidence = det['confianza']

            # Obtener color
            color = colors.get(class_name, (255, 255, 255))

            # Dibujar caja
            cv2.rectangle(output_frame,
                          (bbox['x_min'], bbox['y_min']),
                          (bbox['x_max'], bbox['y_max']),
                          color, 2)

            # Dibujar etiqueta
            label = f"{class_name}: {confidence:.2f}"
            label_size, _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)

            cv2.rectangle(output_frame,
                          (bbox['x_min'], bbox['y_min'] - label_size[1] - 10),
                          (bbox['x_min'] + label_size[0], bbox['y_min']),
                          color, -1)

            cv2.putText(output_frame, label,
                        (bbox['x_min'], bbox['y_min'] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return output_frame

    def process_video(self, video_source: str = 0,
                      output_path: str = None,
                      show_window: bool = True,
                      confidence_threshold: float = 0.5,
                      log_detections: str = None,
                      log_interval: int = 1,
                      max_frames: int = 300):
        """
        Procesar video para deteccion de objetos.

        Args:
            video_source: Ruta del archivo de video o indice del dispositivo de cámara
            output_path: Ruta del archivo de video de salida (opcional)
            show_window: Booleano para mostrar ventana de video
            confidence_threshold: Umbral de confianza para detecciones
            log_detections: Ruta del archivo JSON para guardar detecciones (opcional)
            log_interval: Intervalo de frames para actualizar el JSON (default: 1 = cada frame)
            max_frames: Maximo de frames a mantener en JSON (sliding window)
        """
        # Abrir fuente de video
        cap = cv2.VideoCapture(video_source)

        if not cap.isOpened():
            raise ValueError(
                f"No se pudo abrir recurso de video: {video_source}")

        # Obtener propiedades del video
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps == 0:
            fps = 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Propiedades del video: {width}x{height} @ {fps} fps")

        # Inicializar logger si se especifiio
        logger = DetectionLogger(
            log_detections, log_interval, max_frames) if log_detections else None
        if logger:
            print(f"Registrando detecciones en: {log_detections}")
            print(f"Actualizando JSON cada {log_interval} frame(s)")
            print(
                f"Ventana deslizante: Últimos {max_frames} frames ({max_frames/fps:.1f}s @ {fps}fps)")

        # Configurar escritor de video si se proporciona una ruta de salida
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            print(f"Grabando en: {output_path}")

        # Crear ventana si es necesario
        if show_window:
            cv2.namedWindow('Detector de Tranico', cv2.WINDOW_NORMAL)

        print("Iniciando deteccion... Presiona 'q' para salir")

        frame_count = 0
        start_time = cv2.getTickCount()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Calcular timestamp
                current_time = (cv2.getTickCount() - start_time) / \
                    cv2.getTickFrequency()

                # Detectar objetos
                detections = self.detect_objects(frame, confidence_threshold)

                # Registrar detecciones si el logger estanactivo
                if logger:
                    logger.log_frame(frame_count, current_time, detections)

                # Dibujar detecciones
                output_frame = self.draw_detections(frame, detections)

                # AI±adir estadisticas
                stats_text = f"Cuadro: {frame_count} | Objetos: {len(detections)}"
                cv2.putText(output_frame, stats_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                with self.frame_lock:
                    self.latest_frame = output_frame.copy()

                # Escribir cuadro en archivo de salida
                if writer:
                    writer.write(output_frame)

                try:
                    cv2.imwrite('latest_frame.jpg', output_frame, 
                                [cv2.IMWRITE_JPEG_QUALITY, 85])
                except Exception as e:
                    pass 

                # Mostrar ventana
                if show_window:
                    cv2.imshow('Detector de Trafico', output_frame)

                    # Esperar tecla 'q' para salir
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                frame_count += 1

                # Estadisticas cada 30 cuadros
                if frame_count % 30 == 0:
                    print(f"Procesados {frame_count} cuadros...", end='\r')

        finally:
            cap.release()
            if writer:
                writer.release()
            if show_window:
                cv2.destroyAllWindows()

            # Guardar log si estanactivo
            if logger:
                logger.save()

            print(f"\nProcesados {frame_count} cuadros en total")


def parse_detections_log(log_file: str,
                         summary: bool = False,
                         filter_class: str = None,
                         min_confidence: float = None,
                         frame_range: Tuple[int, int] = None):
    """
    Parsear y mostrar datos de detecciones desde archivo JSON.

    Args:
        log_file: Ruta del archivo JSON
        summary: Mostrar solo resumen estadistico
        filter_class: Filtrar por clase de objeto especifica
        min_confidence: Confianza minima para filtrar
        frame_range: Tupla (inicio, fin) para rango de frames
    """
    if not os.path.exists(log_file):
        print(f"Error: Archivo no encontrado: {log_file}")
        return

    with open(log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("="*70)
    print("ANILISIS DE DETECCIONES DE TRAFICO")
    print("="*70)
    print(f"\nArchivo: {log_file}")
    print(f"Inicio: {data['metadatos']['hora_inicio']}")
    print(f"Fin: {data['metadatos'].get('hora_fin', 'N/A')}")

    # Actualizar para mostrar informacion de ventana deslizante
    metadata = data.get('metadatos', {})
    print(
        f"Total frames procesados: {metadata.get('total_frames_procesados', 'N/A')}")
    print(
        f"Frames en ventana: {metadata.get('frames_en_ventana', len(data.get('frames', [])))}")
    print(
        f"TamaI±o de ventana: {metadata.get('max_frames_almacenados', 'N/A')} frames")

    frames = data['frames']

    # Aplicar filtros
    if frame_range:
        start, end = frame_range
        frames = [f for f in frames if start <= f['numero_frame'] <= end]
        print(f"Filtrado por rango de frames: {start}-{end}")

    if not frames:
        print("\nNo hay frames que coincidan con los filtros.")
        return

    # Calcular estadisticas
    total_detections = 0
    class_counts = defaultdict(int)
    confidence_stats = defaultdict(list)
    frames_with_detections = 0

    for frame in frames:
        detections = frame['detecciones']

        # Aplicar filtros de clase y confianza
        if filter_class:
            detections = [
                d for d in detections if d['nombre_clase'] == filter_class]
        if min_confidence:
            detections = [
                d for d in detections if d['confianza'] >= min_confidence]

        if detections:
            frames_with_detections += 1

        for det in detections:
            total_detections += 1
            class_counts[det['nombre_clase']] += 1
            confidence_stats[det['nombre_clase']].append(det['confianza'])

    # Mostrar resumen
    print(f"\n{'='*70}")
    print("RESUMEN ESTADISTICO")
    print("="*70)
    print(f"Frames analizados: {len(frames)}")
    print(f"Frames con detecciones: {frames_with_detections}")
    print(f"Total de detecciones: {total_detections}")

    if filter_class:
        print(f"Filtrado por clase: {filter_class}")
    if min_confidence:
        print(f"Confianza minima: {min_confidence:.2f}")

    print(f"\n{'Clase':<20} {'Cantidad':<10} {'Confianza Prom':<15}")
    print("-"*70)

    for class_name in sorted(class_counts.keys()):
        count = class_counts[class_name]
        avg_conf = np.mean(confidence_stats[class_name])
        print(f"{class_name:<20} {count:<10} {avg_conf:.3f}")

    # Mostrar detalle de frames si no es solo resumen
    if not summary and len(frames) <= 50:
        print(f"\n{'='*70}")
        print("DETALLE POR FRAME")
        print("="*70)

        for frame in frames:
            detections = frame['detecciones']

            # Aplicar filtros
            if filter_class:
                detections = [
                    d for d in detections if d['nombre_clase'] == filter_class]
            if min_confidence:
                detections = [
                    d for d in detections if d['confianza'] >= min_confidence]

            if not detections:
                continue

            print(
                f"\nFrame #{frame['numero_frame']} (t={frame['tiempo_segundos']:.2f}s)")
            print(f"  Tiempo: {frame['fecha_hora']}")
            print(f"  Objetos detectados: {len(detections)}")

            for i, det in enumerate(detections, 1):
                bbox = det['caja_delimitadora']
                print(
                    f"    {i}. {det['nombre_clase']} - Confianza: {det['confianza']:.3f}")
                print(
                    f"       Ubicacion: ({bbox['x_min']}, {bbox['y_min']}) -> ({bbox['x_max']}, {bbox['y_max']})")

    elif not summary:
        print(
            f"\nHay {len(frames)} frames para mostrar. Use --summary para ver solo estadisticas.")
        print("  O use --frame-range para limitar el rango de frames.")


# ==================== MAIN ====================

if __name__ == "__main__":
    # Parser principal
    parser = argparse.ArgumentParser(
        description='Deteccion de Objetos de Tranico usando TensorFlow Lite',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(
        dest='command', help='Subcomandos disponibles')

    # Subcomando: detect (deteccion de objetos)
    detect_parser = subparsers.add_parser(
        'detect',
        help='Ejecutar deteccion de objetos en video',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Procesar video y guardar detecciones en JSON
  python traffic_detection.py detect video.mp4 --log detections.json
  
  # Usar cámara USB
  python traffic_detection.py detect --d /dev/video0 --log detections.json
  
  # Procesar video, guardar salida y log
  python traffic_detection.py detect video.mp4 -o output.mp4 --log detections.json
        """
    )

# Ejecucion principal
if __name__ == "__main__":
    # Parser principal
    parser = argparse.ArgumentParser(
        description='Deteccion de Objetos de Tranico usando TensorFlow Lite',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(
        dest='command', help='Subcomandos disponibles')

    # Subcomando: detect (deteccion de objetos)
    detect_parser = subparsers.add_parser(
        'detect',
        help='Ejecutar deteccion de objetos en video',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Procesar video y guardar detecciones en JSON
  python script.py detect video.mp4 --log detections.json
  
  # Usar cámara USB
  python script.py detect --d /dev/video0 --log detections.json
  
  # Procesar video, guardar salida y log
  python script.py detect video.mp4 -o output.mp4 --log detections.json
        """
    )

    detect_parser.add_argument(
        'input',
        nargs='?',
        default=None,
        help='Archivo de video de entrada (.mp4)'
    )

    detect_parser.add_argument(
        '--d',
        dest='device',
        type=str,
        default=None,
        help='Archivo de dispositivo de cámara USB (ej., /dev/video0)'
    )

    detect_parser.add_argument(
        '--output',
        '-o',
        type=str,
        default=None,
        help='Ruta del archivo de video de salida (opcional)'
    )

    detect_parser.add_argument(
        '--log',
        '-l',
        type=str,
        default=None,
        help='Ruta del archivo JSON para guardar log de detecciones'
    )

    detect_parser.add_argument(
        '--log-interval',
        type=int,
        default=1,
        help='Intervalo de frames para actualizar el JSON (default: 1 = cada frame, 30 = cada segundo a 30fps)'
    )

    detect_parser.add_argument(
        '--max-frames',
        type=int,
        default=300,
        help='Manimo de frames a mantener en JSON - ventana deslizante (default: 300 = 10s @ 30fps)'
    )

    detect_parser.add_argument(
        '--confidence',
        '-c',
        type=float,
        default=0.5,
        help='Umbral de confianza para detecciones (por defecto: 0.5)'
    )

    detect_parser.add_argument(
        '--no-display',
        action='store_true',
        help='No mostrar ventana de video'
    )

    # Subcomando: parse (analizar logs JSON)
    parse_parser = subparsers.add_parser(
        'parse',
        help='Analizar archivo JSON de detecciones',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Ver resumen estadistico
  python script.py parse detections.json --summary
  
  # Filtrar por clase especifica
  python script.py parse detections.json --class carro
  
  # Filtrar por confianza minima
  python script.py parse detections.json --min-confidence 0.8
  
  # Ver frames especificos
  python script.py parse detections.json --frame-range 100 200
        """
    )

    parse_parser.add_argument(
        'log_file',
        type=str,
        help='Archivo JSON de detecciones a analizar'
    )

    parse_parser.add_argument(
        '--summary',
        '-s',
        action='store_true',
        help='Mostrar solo resumen estadistico'
    )

    parse_parser.add_argument(
        '--class',
        dest='filter_class',
        type=str,
        default=None,
        help='Filtrar por clase de objeto especifica'
    )

    parse_parser.add_argument(
        '--min-confidence',
        type=float,
        default=None,
        help='Confianza minima para filtrar detecciones'
    )

    parse_parser.add_argument(
        '--frame-range',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        default=None,
        help='Rango de frames a analizar (inicio fin)'
    )

    # Subcomando: parse (analizar logs JSON)
    parse_parser = subparsers.add_parser(
        'parse1',
        help='Analizar archivo JSON de detecciones',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Ver resumen estadistico
  python traffic_detection.py parse detections.json --summary
  
  # Filtrar por clase especifica
  python traffic_detection.py parse detections.json --class carro
  
  # Filtrar por confianza minima
  python traffic_detection.py parse detections.json --min-confidence 0.8
  
  # Ver frames especificos
  python traffic_detection.py parse detections.json --frame-range 100 200
        """
    )

    parse_parser.add_argument(
        'log_file',
        type=str,
        help='Archivo JSON de detecciones a analizar'
    )

    parse_parser.add_argument(
        '--summary',
        '-s',
        action='store_true',
        help='Mostrar solo resumen estadistico'
    )

    parse_parser.add_argument(
        '--class',
        dest='filter_class',
        type=str,
        default=None,
        help='Filtrar por clase de objeto especifica'
    )

    parse_parser.add_argument(
        '--min-confidence',
        type=float,
        default=None,
        help='Confianza minima para filtrar detecciones'
    )

    parse_parser.add_argument(
        '--frame-range',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        default=None,
        help='Rango de frames a analizar (inicio fin)'
    )

    args = parser.parse_args()

    # Si no se especifica subcomando, mostrar ayuda
    if args.command is None:
        parser.print_help()
        print("\n" + "="*70)
        print("Por favor, especifique un subcomando: 'detect' o 'parse'")
        print("="*70)
        print("\nEjemplos:")
        print("  python traffic_detection.py detect video.mp4 --log detections.json")
        print("  python traffic_detection.py parse detections.json --summary")
        exit(0)

    # Ejecutar subcomando correspondiente
    if args.command == 'detect':
        # Validar entradas
        if args.device is None and args.input is None:
            detect_parser.error(
                "Debe proporcionar un archivo de video o usar --d para especificar un dispositivo de cámara")

        if args.device and args.input:
            detect_parser.error(
                "No se puede usar ambos --d (dispositivo de cámara) y archivo de video simultaneamente")
            detect_parser.error(
                "Debe proporcionar un archivo de video o usar --d para especificar un dispositivo de cámara")

        if args.device and args.input:
            detect_parser.error(
                "No se puede usar ambos --d (dispositivo de cámara) y archivo de video simultaneamente")

        # Determinar fuente de video
        if args.device:
            print(f"Usando dispositivo de cámara: {args.device}")
            video_source = args.device
        else:
            if not os.path.exists(args.input):
                print(f"Error: Archivo de video no encontrado: {args.input}")
                exit(1)
            print(f"Usando archivo de video: {args.input}")
            video_source = args.input

        # Inicializar detector
        print("\nInicializando detector de objetos...")
        try:
            detector = TrafficObjectDetector()
        except FileNotFoundError as e:
            print(e)
            exit(1)

        # Procesar video
        print(
            f"\nIniciando detección (umbral de confianza: {args.confidence})...")
        print("Presiona 'q' para salir\n")

        try:
            detector.process_video(
                video_source=video_source,
                output_path=args.output,
                show_window=not args.no_display,
                confidence_threshold=args.confidence,
                log_detections=args.log,
                log_interval=args.log_interval,
                max_frames=args.max_frames
            )
        except KeyboardInterrupt:
            print("\n\nInterrumpido por el usuario")
        except Exception as e:
            print(f"\nError durante el procesamiento: {e}")
            exit(1)

        print("\nFin de la ejecución.")

    elif args.command == 'parse':
        frame_range = tuple(args.frame_range) if args.frame_range else None
        parse_detections_log(
            args.log_file,
            summary=args.summary,
            filter_class=args.filter_class,
            min_confidence=args.min_confidence,
            frame_range=frame_range
        )