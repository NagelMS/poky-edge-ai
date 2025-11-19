#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
 Proyecto: Deteccion de Trafico en Tiempo Real - Servidor Web
 File: traffic_web_server.py
 Autores: Nagel Mejía Segura, Wilberth Gutiérrez Montero, Óscar González Cambronero.
 Fecha: 2025-11-09
Descripción:
     Este script implementa un servidor web HTTP para monitorear en tiempo real
     las detecciones de tráfico. Lee continuamente el archivo JSON generado por
     el sistema de detección y expone los datos mediante una API REST accesible
     desde navegadores web.

 Dependencias de pip:
     - flask
     - flask-cors

==========================================================
"""

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import json
import os
import threading
import time
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

app = Flask(__name__)
CORS(app)  # Permitir acceso desde otros orígenes

# Variables globales
detection_data = None
last_read_time = None
data_lock = threading.Lock()


class TrafficDataMonitor:
    """Clase para monitorear y procesar datos de detecciones."""

    def __init__(self, json_file: str, refresh_interval: float = 1.0):
        """
        Inicializar monitor de datos.

        Args:
            json_file: Ruta del archivo JSON a monitorear
            refresh_interval: Intervalo de actualización en segundos
        """
        self.json_file = json_file
        self.refresh_interval = refresh_interval
        self.running = False
        self.monitor_thread = None

    def start(self):
        """Iniciar monitoreo en segundo plano."""
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(
            f"Monitor iniciado - actualizando cada {self.refresh_interval}s")

    def stop(self):
        """Detener monitoreo."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("Monitor detenido")

    def _monitor_loop(self):
        """Loop principal de monitoreo."""
        global detection_data, last_read_time
        file_found = False
        last_modified = None

        while self.running:
            try:
                if os.path.exists(self.json_file):
                    if not file_found:
                        print(f"Archivo JSON encontrado: {self.json_file}")
                        file_found = True

                    # Check if file was modified
                    current_modified = os.path.getmtime(self.json_file)
                    if last_modified is None or current_modified > last_modified:
                        last_modified = current_modified

                        with open(self.json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        with data_lock:
                            detection_data = data
                            last_read_time = datetime.now()
                            print(
                                f"Datos actualizados - Frames: {len(data.get('frames', []))}, Detecciones actuales: {len(data.get('detecciones_actuales', []))}")
                else:
                    if file_found:
                        print(
                            f"ADVERTENCIA: Archivo JSON no encontrado: {self.json_file}")
                        file_found = False
                        with data_lock:
                            detection_data = None
                            last_read_time = None

            except json.JSONDecodeError as e:
                print(f"ADVERTENCIA: Error JSON (archivo siendo escrito): {e}")
                # Archivo siendo escrito, intentar de nuevo
                pass
            except Exception as e:
                print(f"ERROR: Error leyendo JSON: {e}")

            time.sleep(self.refresh_interval)

    @staticmethod
    def get_statistics(data: dict) -> dict:
        """
        Calcular estadísticas de las detecciones.

        Args:
            data: Datos de detecciones

        Returns:
            Diccionario con estadísticas
        """
        if not data or 'frames' not in data:
            return {}

        frames = data['frames']
        metadata = data.get('metadatos', {})

        # Estadísticas basadas en ventana deslizante actual
        total_detections = 0
        class_counts = defaultdict(int)
        confidence_stats = defaultdict(list)
        frames_with_detections = 0

        for frame in frames:
            detections = frame.get('detecciones', [])

            if detections:
                frames_with_detections += 1

            for det in detections:
                total_detections += 1
                class_name = det['nombre_clase']
                class_counts[class_name] += 1
                confidence_stats[class_name].append(det['confianza'])

        # Calcular promedios de confianza
        class_stats = []
        for class_name in sorted(class_counts.keys()):
            avg_conf = sum(confidence_stats[class_name]) / \
                len(confidence_stats[class_name])
            class_stats.append({
                'class_name': class_name,
                'count': class_counts[class_name],
                'avg_confidence': round(avg_conf, 3)
            })

        # Obtener detecciones actuales (frame más reciente)
        current_detections = data.get('detecciones_actuales', [])

        return {
            'frames_in_window': len(frames),
            'total_frames_processed': metadata.get('total_frames_processed', len(frames)),
            'frames_with_detections': frames_with_detections,
            'total_detections_in_window': total_detections,
            'class_statistics': class_stats,
            'last_frame': frames[-1] if frames else None,
            'current_detections': current_detections,
            'current_detection_count': len(current_detections)
        }


# ==================== RUTAS API ====================

@app.route('/')
def index():
    """Página principal con dashboard."""
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Monitor de Tráfico - Panel de Control</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                background: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                text-align: center;
            }
            
            .header h1 {
                color: #333;
                font-size: 2em;
                margin-bottom: 10px;
            }
            
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
                margin-top: 10px;
            }
            
            .status.running {
                background: #4caf50;
                color: white;
            }
            
            .status.completed {
                background: #757575;
                color: white;
            }
            
            .status.offline {
                background: #f44336;
                color: white;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .card {
                background: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .card h2 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.2em;
                border-bottom: 2px solid #4caf50;
                padding-bottom: 5px;
            }
            
            .stat {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            
            .stat:last-child {
                border-bottom: none;
            }
            
            .stat-label {
                color: #666;
                font-weight: 500;
            }
            
            .stat-value {
                color: #333;
                font-weight: bold;
            }
            
            .table-container {
                overflow-x: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            
            th, td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            
            th {
                background: #f9f9f9;
                color: #333;
                font-weight: 600;
            }
            
            tr:hover {
                background: #f9f9f9;
            }
            
            .refresh-info {
                text-align: center;
                color: #666;
                margin-top: 20px;
                font-size: 0.9em;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
            }
            
            .error {
                background: #ffebee;
                color: #c62828;
                padding: 15px;
                border-radius: 3px;
                margin: 20px 0;
            }
            
            .json-container {
                background: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 15px;
                margin: 10px 0;
                max-height: 400px;
                overflow: auto;
            }
            
            .json-key {
                color: #2e7d32;
                font-weight: 600;
                font-size: 0.9em;
            }
            
            .json-value {
                color: #333;
                margin-left: 8px;
                font-family: 'Courier New', monospace;
                font-size: 0.85em;
            }
            
            .detection-item {
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 12px;
                margin: 8px 0;
                border-left: 4px solid #4caf50;
            }
            
            .detection-title {
                font-weight: bold;
                color: #2e7d32;
                margin-bottom: 8px;
                font-size: 0.95em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Monitor de Tráfico en Tiempo Real</h1>
                <h3 style="color: #666; margin-bottom: 15px; font-weight: normal;">Proyecto 3 Taller de Sistemas Embebidos</h3>
                <div id="status" class="status offline">Sin Datos</div>
                <p id="lastUpdate" style="margin-top: 10px; color: #666;">Esperando datos...</p>
            </div>
            
            <div id="content" class="loading">
                <p>Cargando datos...</p>
            </div>
            
            <div class="refresh-info">
                El servidor se actualiza cada 2 segundos.
            </div>
            <div class="refresh-info">
                Hecho por: Nagel Mejía, Wilberth Guitérrez y Óscar González.
            </div>
        </div>
        
        <script>
            function formatDateTime(isoString) {
                const date = new Date(isoString);
                return date.toLocaleString('es-ES');
            }
            
            function renderJsonData(obj, level = 0) {
                let html = '';
                for (const [key, value] of Object.entries(obj)) {
                    if (level === 0) {
                        // Top level items as stat rows
                        html += '<div class="stat">';
                        html += '<span class="stat-label">' + key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase()) + ':</span>';
                        
                        if (value === null) {
                            html += '<span class="stat-value" style="color: #999;">null</span>';
                        } else if (typeof value === 'object' && !Array.isArray(value)) {
                            // Special handling for bounding box coordinates
                            if (key === 'caja_delimitadora' && value.x_min !== undefined) {
                                html += '<span class="stat-value">(' + value.x_min + ', ' + value.y_min + ') → (' + value.x_max + ', ' + value.y_max + ')</span>';
                            } else {
                                html += '<span class="stat-value">[Objeto]</span>';
                            }
                        } else if (Array.isArray(value)) {
                            html += '<span class="stat-value">' + value.length + ' elementos</span>';
                        } else if (typeof value === 'string' && value.includes('T') && value.includes(':')) {
                            // Format datetime strings
                            html += '<span class="stat-value">' + formatDateTime(value) + '</span>';
                        } else if (typeof value === 'number') {
                            html += '<span class="stat-value">' + (value % 1 === 0 ? value : value.toFixed(3)) + '</span>';
                        } else {
                            html += '<span class="stat-value">' + value + '</span>';
                        }
                        html += '</div>';
                    } else {
                        // Nested items with indentation
                        html += '<div style="margin-left: ' + (level * 15) + 'px; padding: 3px 0; border-left: 2px solid #e0e0e0; padding-left: 10px;">';
                        html += '<span class="json-key" style="font-size: 0.9em;">' + key + ':</span> ';
                        
                        if (value === null) {
                            html += '<span class="json-value" style="color: #999;">null</span>';
                        } else if (typeof value === 'object' && !Array.isArray(value)) {
                            // Special handling for bounding box coordinates at nested level
                            if (key === 'caja_delimitadora' && value.x_min !== undefined) {
                                html += '<span class="json-value">(' + value.x_min + ', ' + value.y_min + ') → (' + value.x_max + ', ' + value.y_max + ')</span>';
                            } else {
                                html += '<br>' + renderJsonData(value, level + 1);
                            }
                        } else if (Array.isArray(value)) {
                            html += '<span class="json-value">[' + value.length + ' elementos]</span>';
                            if (value.length > 0 && level < 3) {
                                html += '<br>' + renderJsonData(value[0], level + 1);
                                if (value.length > 1) {
                                    html += '<div style="margin-left: ' + ((level + 1) * 15) + 'px; color: #999; font-size: 0.85em;">... y ' + (value.length - 1) + ' más</div>';
                                }
                            }
                        } else {
                            html += '<span class="json-value">' + value + '</span>';
                        }
                        html += '</div>';
                    }
                }
                return html;
            }
            
            function updateDashboard() {
                fetch('/api/raw')
                    .then(response => {
                        console.log('Response status:', response.status);
                        return response.json();
                    })
                    .then(data => {
                        console.log('Received data:', data);
                        
                        if (data.error || !data) {
                            console.log('No data available:', data.error || 'No data');
                            document.getElementById('content').innerHTML = 
                                '<div class="error">No hay datos disponibles. Asegúrate de que el detector esté ejecutándose y haya generado el archivo JSON.<br><br>Error: ' + (data.error || 'Sin datos') + '</div>';
                            return;
                        }
                        
                        const metadata = data.metadatos || {};
                        
                        // Update status
                        const statusEl = document.getElementById('status');
                        statusEl.className = 'status ' + (metadata.estado || 'ejecutandose');
                        statusEl.textContent = metadata.estado === 'ejecutandose' ? 'Activo' : 
                                              metadata.estado === 'completado' ? 'Completado' : 'Activo';
                        
                        document.getElementById('lastUpdate').textContent = 
                            'Última actualización: ' + (metadata.ultima_actualizacion ? formatDateTime(metadata.ultima_actualizacion) : new Date().toLocaleString('es-ES'));
                        
                        // Build content
                        let html = '';
                        
                        // Metadata section
                        if (metadata && Object.keys(metadata).length > 0) {
                            html += '<div class="card">';
                            html += '<h2>Metadatos</h2>';
                            html += '<div class="json-container">';
                            html += renderJsonData(metadata);
                            html += '</div>';
                            html += '</div>';
                        }
                        
                        // Current detections section
                        html += '<div class="card">';
                        html += '<h2>Detecciones Actuales</h2>';
                        if (data.detecciones_actuales && data.detecciones_actuales.length > 0) {
                            html += '<div class="stat">';
                            html += '<span class="stat-label">Total detecciones:</span>';
                            html += '<span class="stat-value">' + data.detecciones_actuales.length + '</span>';
                            html += '</div>';
                            html += '<div class="json-container">';
                            data.detecciones_actuales.forEach((detection, index) => {
                                html += '<div class="detection-item">';
                                html += '<div class="detection-title">Detección ' + (index + 1) + '</div>';
                                html += renderJsonData(detection, 0);
                                html += '</div>';
                            });
                            html += '</div>';
                        } else {
                            html += '<div class="stat">';
                            html += '<span class="stat-label">Estado:</span>';
                            html += '<span class="stat-value" style="color: #999;">Sin detecciones actuales</span>';
                            html += '</div>';
                        }
                        html += '</div>';
                        
                        // Frames section (last 5 frames)
                        html += '<div class="card">';
                        html += '<h2>Frames Recientes</h2>';
                        if (data.frames && data.frames.length > 0) {
                            const recentFrames = data.frames.slice(-5);
                            html += '<div class="stat">';
                            html += '<span class="stat-label">Total de frames:</span>';
                            html += '<span class="stat-value">' + data.frames.length + '</span>';
                            html += '</div>';
                            html += '<div class="stat">';
                            html += '<span class="stat-label">Mostrando:</span>';
                            html += '<span class="stat-value">Últimos ' + recentFrames.length + ' frames</span>';
                            html += '</div>';
                            html += '<div class="json-container">';
                            recentFrames.forEach((frame, index) => {
                                html += '<div class="detection-item">';
                                html += '<div class="detection-title">Frame ' + frame.numero_frame + '</div>';
                                html += renderJsonData(frame, 0);
                                html += '</div>';
                            });
                            html += '</div>';
                        } else {
                            html += '<div class="stat">';
                            html += '<span class="stat-label">Estado:</span>';
                            html += '<span class="stat-value" style="color: #999;">No hay frames procesados</span>';
                            html += '</div>';
                        }
                        html += '</div>';

                        
                        document.getElementById('content').innerHTML = html;
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('content').innerHTML = 
                            '<div class="error">Error de conexión con el servidor.</div>';
                    });
            }
            
            // Update immediately and then every 2 seconds
            updateDashboard();
            setInterval(updateDashboard, 2000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/api/status')
def api_status():
    """Obtener estado actual y estadísticas."""
    with data_lock:
        if detection_data is None:
            return jsonify({
                'data_available': False,
                'message': 'No hay datos disponibles'
            })

        stats = TrafficDataMonitor.get_statistics(detection_data)

        return jsonify({
            'data_available': True,
            'metadata': detection_data.get('metadatos', {}),
            'statistics': stats,
            'server_time': datetime.now().isoformat()
        })


@app.route('/api/frames')
def api_frames():
    """Obtener lista de frames con detecciones."""
    with data_lock:
        if detection_data is None:
            return jsonify({'error': 'No hay datos disponibles'}), 404

        # Parámetros de paginación
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)

        frames = detection_data.get('frames', [])

        # Aplicar paginación
        total = len(frames)
        paginated_frames = frames[offset:offset + limit]

        return jsonify({
            'total': total,
            'offset': offset,
            'limit': limit,
            'frames': paginated_frames
        })


@app.route('/api/frames/<int:frame_number>')
def api_frame_detail(frame_number):
    """Obtener detalle de un frame específico."""
    with data_lock:
        if detection_data is None:
            return jsonify({'error': 'No hay datos disponibles'}), 404

        frames = detection_data.get('frames', [])

        # Buscar frame
        frame = next(
            (f for f in frames if f['numero_frame'] == frame_number), None)

        if frame is None:
            return jsonify({'error': f'Frame {frame_number} no encontrado'}), 404

        return jsonify(frame)


@app.route('/api/class/<class_name>')
def api_class_detections(class_name):
    """Obtener todas las detecciones de una clase específica."""
    with data_lock:
        if detection_data is None:
            return jsonify({'error': 'No hay datos disponibles'}), 404

        frames = detection_data.get('frames', [])
        class_detections = []

        for frame in frames:
            frame_detections = [
                {**det, 'numero_frame': frame['numero_frame'],
                    'tiempo_segundos': frame['tiempo_segundos']}
                for det in frame.get('detecciones', [])
                if det['nombre_clase'] == class_name
            ]
            class_detections.extend(frame_detections)

        return jsonify({
            'class_name': class_name,
            'total_detections': len(class_detections),
            'detections': class_detections
        })


@app.route('/api/raw')
def api_raw():
    """Obtener datos JSON completos."""
    with data_lock:
        if detection_data is None:
            return jsonify({
                'error': 'No hay datos disponibles',
                'message': 'El archivo JSON no ha sido generado o no se puede leer'
            }), 404

        return jsonify(detection_data)


# ==================== MAIN ====================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Servidor Web para Monitoreo de Detecciones de Tráfico',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Iniciar servidor en puerto predeterminado (5000)
  python traffic_web_server.py detections.json
  
  # Especificar puerto personalizado
  python traffic_web_server.py detections.json --port 8080
  
  # Escuchar en todas las interfaces (accesible desde red)
  python traffic_web_server.py detections.json --host 0.0.0.0
  
  # Actualización más frecuente
  python traffic_web_server.py detections.json --refresh 0.5

Acceso desde navegador:
  - Dashboard: http://<raspberry-pi-ip>:5000/
  - API Status: http://<raspberry-pi-ip>:5000/api/status
  - API Frames: http://<raspberry-pi-ip>:5000/api/frames
        """
    )

    parser.add_argument(
        'json_file',
        type=str,
        help='Ruta del archivo JSON de detecciones a monitorear'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Dirección IP para escuchar (default: 0.0.0.0 - todas las interfaces)'
    )

    parser.add_argument(
        '--port',
        '-p',
        type=int,
        default=5000,
        help='Puerto del servidor (default: 5000)'
    )

    parser.add_argument(
        '--refresh',
        '-r',
        type=float,
        default=1.0,
        help='Intervalo de actualización en segundos (default: 1.0)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Ejecutar en modo debug'
    )

    args = parser.parse_args()

    # Validar archivo JSON
    if not os.path.exists(args.json_file):
        print(f"ADVERTENCIA: Archivo JSON no encontrado: {args.json_file}")
        print("El servidor se iniciará y esperará a que el detector genere el archivo JSON.")
        print("Para generar datos, ejecuta:")
        print(
            f"  python traffic_detection_json.py detect video.mp4 --log {args.json_file}")
        print()

    # Inicializar y arrancar monitor
    print("="*70)
    print("SERVIDOR WEB DE MONITOREO DE TRÁFICO")
    print("="*70)
    print(f"\nArchivo monitoreado: {args.json_file}")
    print(f"Actualización: cada {args.refresh}s")
    print(f"Servidor: http://{args.host}:{args.port}/")

    # Obtener IP local para mostrar al usuario
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"\nAccede desde tu navegador en:")
        print(f"  - Local: http://localhost:{args.port}/")
        print(f"  - Red: http://{local_ip}:{args.port}/")
    except:
        pass

    print("\nAPI Endpoints disponibles:")
    print(f"  - Dashboard: /")
    print(f"  - Status: /api/status")
    print(f"  - Frames: /api/frames")
    print(f"  - Frame específico: /api/frames/<number>")
    print(f"  - Por clase: /api/class/<class_name>")
    print(f"  - Datos raw: /api/raw")
    print("\nPresiona Ctrl+C para detener el servidor")
    print("="*70 + "\n")

    # Iniciar monitor
    monitor = TrafficDataMonitor(args.json_file, args.refresh)
    monitor.start()

    try:
        # Iniciar servidor Flask
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\nDeteniendo servidor...")
    finally:
        monitor.stop()
        print("Servidor detenido.")
