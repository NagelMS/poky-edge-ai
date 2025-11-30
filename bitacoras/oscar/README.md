# Bitacora Oscar Gonzales Cambronero

## Día 28 de octubre del 2025
- **`Completado`**: Se estableció el entorno Python dentro de una Raspberry Pi 5, confirmando compatibilidad con TensorFlow Lite y OpenCV. Se inició el diseño base del script principal para captura de video y preprocesamiento.
- **`Problemas`**: Dificultades iniciales al vincular dependencias de OpenCV y TFLite debido a incompatibilidades de versiones.
- **`Tareas próximas`**: Realizar pruebas de lectura de cámara en tiempo real y validar latencia por frame dentro del límite esperado.
- **`Referencias`**: https://www.tensorflow.org/lite/

## Día 30 de octubre del 2025
- **`Completado`**: Se programó el módulo de preprocesamiento, conversión a tensores y normalización de frames para modelos TFLite.
- **`Problemas`**: Desajustes entre formatos RGB/BGR causaron resultados inconsistentes en inferencia.
- **`Tareas próximas`**: Implementar y probar detecciones parciales usando un modelo preliminar.
- **`Referencias`**: https://docs.opencv.org/

## Día 01 de noviembre del 2025
- **`Completado`**: Primer test de inferencia completado; el modelo logró identificar vehículos en imagen estática.
- **`Problemas`**: Latencia sobre 300ms por frame.
- **`Tareas próximas`**: Optimizar tamaño de input y buffering de frames.
- **`Referencias`**: https://www.tensorflow.org/lite/performance

## Día 05 de noviembre del 2025
- **`Completado`**: Mejoras en threading para lectura paralela de frames.
- **`Problemas`**: Sincronización entre threads provocó jitter en FPS.
- **`Tareas próximas`**: Ajustar workers y cola de frames.
- **`Referencias`**: https://docs.python.org/3/library/threading.html

## Día 10 de noviembre del 2025
- **`Completado`**: Se añadió submódulo de tracking basado en distancia de bounding boxes.
- **`Problemas`**: IDs se pierden cambiando iluminación.
- **`Tareas próximas`**: Probar filtros Kalman / DeepSORT.
- **`Referencias`**: https://github.com/nwojke/deep_sort

## Día 15 de noviembre del 2025
- **`Completado`**: Módulo de visualización con overlay funcional.
- **`Problemas`**: CPU alta por modelo FP32.
- **`Tareas próximas`**: Cuantización a int8.
- **`Referencias`**: https://www.tensorflow.org/lite/convert

## Día 20 de noviembre del 2025
- **`Completado`**: Versión estable ejecutándose en 15 FPS.
- **`Problemas`**: Fallos eventuales al perder la cámara.
- **`Tareas próximas`**: Agregar watchdog automático.
- **`Referencias`**: https://www.kernel.org/doc/html/latest/admin-guide/watchdog/

## Día 25 de noviembre del 2025
- **`Completado`**: Integración de telemetría en terminal (FPS, CPU, RAM).
- **`Problemas`**: Logging excesivo degradando rendimiento.
- **`Tareas próximas`**: Rotación de logs.
- **`Referencias`**: https://www.freedesktop.org/software/systemd/man/journalctl.html

## Día 28 de noviembre del 2025
- **`Completado`**: Script final listo para integración Yocto.
- **`Problemas`**: Ninguno.
- **`Tareas próximas`**: Pruebas con imagen release.
- **`Referencias`**: -

