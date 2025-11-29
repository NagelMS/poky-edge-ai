SUMMARY = "Aplicación para detección de tránsito usando TensorFlow Lite"
DESCRIPTION = "Aplicación de Python para detección de tráfico usando visión por computador y TensorFlow Lite"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://traffic_detection_json.py \
    file://traffic_web_server.py \
    file://modelos/ \
    file://videos/ \
"

S = "${WORKDIR}"

RDEPENDS:${PN} = " \
    python3-core \
    python3-numpy \
    python3-opencv \
    python3-typing-extensions \
    python3-flask \
"


# Directorio de instalación
INSTALL_DIR = "/opt/traffic-detection"

do_install() {
    # Crear directorios
    install -d ${D}${INSTALL_DIR}
    install -d ${D}${INSTALL_DIR}/modelos
    install -d ${D}${INSTALL_DIR}/videos
    
    # Instalar todos los scripts Python
    for script in ${S}/*.py; do
        if [ -f "$script" ]; then
            install -m 0755 "$script" ${D}${INSTALL_DIR}/
        fi
    done
    
    # Instalar archivos del modelo
    if [ -d ${S}/modelos ]; then
        cp -r ${S}/modelos/* ${D}${INSTALL_DIR}/modelos/
        chmod -R 0644 ${D}${INSTALL_DIR}/modelos/*
    fi
    
    # Instalar videos de prueba
    if [ -d ${S}/videos ]; then
        cp -r ${S}/videos/* ${D}${INSTALL_DIR}/videos/
        chmod -R 0644 ${D}${INSTALL_DIR}/videos/*
    fi
    
    # Crear script de lanzamiento en /usr/bin
    install -d ${D}${bindir}
    cat > ${D}${bindir}/traffic-detection << 'EOF'
#!/bin/sh
cd /opt/traffic-detection || exit 1
exec python3 traffic_detection.py "$@"
EOF
    chmod 0755 ${D}${bindir}/traffic-detection
}

FILES:${PN} = " \
    ${INSTALL_DIR}/*.py \
    ${INSTALL_DIR}/modelos/ \
    ${INSTALL_DIR}/videos/ \
    ${bindir}/traffic-detection \
"

INSANE_SKIP:${PN} += "already-stripped"