# Bitacora Wilberth Gutiérrez Montero

## Día 28 de octubre del 2025
- **`Completado`**: Inicio del entorno Yocto con poky kirkstone + meta-raspberrypi.
- **`Problemas`**: Conflictos python3-native al incluir OpenCV.
- **`Tareas próximas`**: Crear capas meta-tensorflow y meta-display.
- **`Referencias`**: https://docs.yoctoproject.org/

## Día 30 de octubre del 2025
- **`Completado`**: Estructura inicial meta-tensorflow con bbappend para TFLite.
- **`Problemas`**: Rutas incorrectas en SRC_URI.
- **`Tareas próximas`**: Validar build de core-image-base.
- **`Referencias`**: https://www.yoctoproject.org/software-overview/

## Día 01 de noviembre del 2025
- **`Completado`**: Receta OpenCV compilada con soporte V4L2.
- **`Problemas`**: Compilación extensa.
- **`Tareas próximas`**: Habilitar optimización NEON ARM.
- **`Referencias`**: https://docs.opencv.org/

## Día 05 de noviembre del 2025
- **`Completado`**: TensorFlow Lite disponible SSTATE + deploy.
- **`Problemas`**: falló flatbuffers-native.
- **`Tareas próximas`**: Parchear flatbuffers.
- **`Referencias`**: https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite

## Día 10 de noviembre del 2025
- **`Completado`**: Imagen mínima bootea en Raspberry Pi.
- **`Problemas`**: No se detectó cámara.
- **`Tareas próximas`**: Agregar soporte GStreamer + UVC.
- **`Referencias`**: https://gstreamer.freedesktop.org/

## Día 15 de noviembre del 2025
- **`Completado`**: OpenCV + GStreamer integrados.
- **`Problemas`**: tamaño rootfs >3GB.
- **`Tareas próximas`**: read-only-rootfs + compression.
- **`Referencias`**: https://docs.yoctoproject.org/dev-manual/reproducible-builds.html

## Día 20 de noviembre del 2025
- **`Completado`**: Build casi reproducible.
- **`Problemas`**: hashes variables en dependencias.
- **`Tareas próximas`**: activar reproducible_build.
- **`Referencias`**: https://reproducible-builds.org/

## Día 25 de noviembre del 2025
- **`Completado`**: Imagen release-candidate R1.0 generada.
- **`Problemas`**: módulo V4L2 no autocarga.
- **`Tareas próximas`**: udev rule y systemd service.
- **`Referencias`**: https://www.freedesktop.org/software/systemd/

## Día 28 de noviembre del 2025
- **`Completado`**: Imagen final reproducible empaquetada.
- **`Problemas`**: Ninguno crítico.
- **`Tareas próximas`**: Validación final con pruebas finales.
- **`Referencias`**: https://github.com/yoctoproject/meta-raspberrypi

