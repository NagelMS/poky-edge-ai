SUMMARY = "Aplicación para detección de transito usando TensorFlow Lite"
DESCRIPTION = "Aplicación de python para detección de trafico usando vision por computador y TensorFlowLite"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://traffic_detection.py \
    file://modelos/ \
    file://videos/ \
"

S = "${WORKDIR}"

RDEPENDS:${PN} = " \
    python3 \
    python3-core \
    python3-numpy \
    python3-opencv \
    python3-typing-extensions \
"

# Directorio de instalación
INSTALL_DIR = "/opt/traffic-detection"

do_install() {
    # Crear directorios
    install -d ${D}${INSTALL_DIR}
    install -d ${D}${INSTALL_DIR}/modelos
    install -d ${D}${INSTALL_DIR}/videos
    
    # Instalar script principal
    install -m 0755 ${WORKDIR}/traffic_detection.py ${D}${INSTALL_DIR}/
    
    # Instalar archivos del modelo
    if [ -d ${WORKDIR}/modelo ]; then
        cp -r ${WORKDIR}/modelo/* ${D}${INSTALL_DIR}/modelos/
    fi
    
    # Instalar videos de prueba
    if [ -d ${WORKDIR}/videos ]; then
        cp -r ${WORKDIR}/videos/* ${D}${INSTALL_DIR}/videos/
    fi
    
    # Crear script de lanzamiento en /usr/bin
    install -d ${D}${bindir}
    cat > ${D}${bindir}/traffic-detection << 'EOF'
#!/bin/sh
cd /opt/traffic-detection
python3 traffic_detection.py "$@"
EOF
    chmod 0755 ${D}${bindir}/traffic-detection
}

FILES:${PN} += " \
    ${INSTALL_DIR} \
    ${INSTALL_DIR}/* \
    ${bindir}/traffic-detection \
"
