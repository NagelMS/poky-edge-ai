# Bitacora Nagel Mejía Segura

## Día 28 de octubre del 2025

- **`Completado`**: Se siguió una guía para generar una imagen de poky para raspberry pi, se utilizó una layer especifica de raspberrypi. La imagen se quedó cocinando.

- **`Problemas`**: Se trató, de generar el bblayers de forma general para que cualquiera con el repositorio se dedicara simplemente a cocinar la receta, sin embargo, no se logró.

- **`Tareas próximas`**: Probar la imagen minima en la Raspberry Pi, y empezar con la aplicación principal para detectar autos, personas y animales.

- **`Referencias`**: https://www.packtpub.com/de-th/learning/how-to-tutorials/building-our-first-poky-image-raspberry-pi

## Día 29 de octubre del 2025

- **`Completado`**:
  - Se modificó bblayers general para uso compartido.
  - Se probó la imagen generada con Yocto en la Raspberry Pi 5, funcionando correctamente.
  - Se inició una investigación para seleccionar un modelo entrenado para tensorflow lite a utilizar para la detección.

- **`Tareas próximas`**: Es necesario utilizar y generar programas de prueba, para comparar el rendimiento de los modelos.

- **`Referencias`**:
  - https://www.kaggle.com/models/kaggle/yolo-v5
  - https://www.kaggle.com/models/tensorflow/ssd-mobilenet-v1
  - https://www.kaggle.com/models/tensorflow/efficientdet
  - https://www.kaggle.com/models/google/mobile-object-localizer-v1
 
## Día 10 de noviembre del 2025

- **`Completado`**:

  - Se incluyeron dependencias al local.conf para generar una imagen minima, con la imagen cocinada de Raspberry Pi se probó la funcionalidad de la camara, sin funcionar correctamente.
  - Se incorporó en el local.conf un modulo de kernel para video (uvcvideo) se dejó cocinando la imagen.

- **`Problemas`**: Si bien por medio de USB sí se reconoce que se conecta la camará, no se reconoce como dispositivo de video.

- **`Tareas próximas`**: Probar la imagen minima en la Raspberry Pi con la incorporación del modulo de kernel.

- **`Referencias`**: https://www.linuxtv.org/wiki/index.php/Uvcvideo

 
## Día 11 de noviembre del 2025

- **`Completado`**:

	- Apartir de la imagen generada se probó la cámara en la RPi, funcionando correctamente.
 	- Se procedió a generar formalmente la capa para la aplicación simple de detección. Se cocinó completamente, al haber problemas se procedió a cambiar de versión de poky.
  - Se generó una nueva imagen con las mismas dependencias anteriores.

- **`Problemas`**: Tensorflow-Lite fue compilado en Python 3.11 pero la versión de poky utilizada (scarthgap) usa 3.12, esto genera conflictos y hace imposible que se ejecute la aplicación. 

- **`Tareas próximas`**: Probar la imagen minima en la Raspberry Pi con la nuevo versión de poky.

## Dia 12 de noviembre del 2025

- **`Completado`**:

	- Se probó finalmente la aplicación de detección simple funcionando correctamente.

- **`Problemas`**: Si bien la aplicación no corre tan lento, se considera aceptable, se puede mejorar para que no se vea con el efecto de lag.

- **`Tareas próximas`**: Aplicar optimizaciones al código de detección, y generar una aplicación robusta con la funcionalidades requeridas.

