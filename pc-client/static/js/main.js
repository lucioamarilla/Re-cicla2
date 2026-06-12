const ESTADOS = {
    IDLE: "idle",
    VALIDANDO: "validando",
    LISTO: "listo",
    ANALIZANDO: "analizando",
    RESULTADO: "resultado",
};

let estadoActual = ESTADOS.IDLE;
let usuarioActual = { id: null, nombre: null };
let ultimaImagenBase64 = null;
let timerReset = null;

const el = {
    inputUid: document.getElementById("uidInput"),
    btnValidar: document.getElementById("btnValidar"),
    btnTomarFoto: document.getElementById("btnTomarFoto"),
    mensaje: document.getElementById("mensajeArea"),
    videoContainer: document.getElementById("videoContainer"),
    videoFeed: document.getElementById("videoFeed"),
    previewContainer: document.getElementById("previewContainer"),
    previewImage: document.getElementById("previewImage"),
    previewInfo: document.getElementById("previewInfo"),
    resultado: document.getElementById("resultadoPantalla"),
};

function cambiarEstado(nuevoEstado, datos) {
    if (timerReset) {
        clearTimeout(timerReset);
        timerReset = null;
    }

    estadoActual = nuevoEstado;
    document.body.className = "";
    el.resultado.style.display = "none";
    el.videoContainer.style.display = "none";
    el.previewContainer.style.display = "none";

    switch (nuevoEstado) {
        case ESTADOS.IDLE:
            document.body.classList.add("estado-idle");
            el.inputUid.disabled = false;
            el.btnValidar.disabled = false;
            el.btnTomarFoto.disabled = true;
            el.inputUid.value = "";
            usuarioActual = { id: null, nombre: null };
            ultimaImagenBase64 = null;
            el.mensaje.innerHTML = "Ingrese su UID de Firebase";
            el.inputUid.focus();
            break;

        case ESTADOS.VALIDANDO:
            document.body.classList.add("estado-validando");
            el.inputUid.disabled = true;
            el.btnValidar.disabled = true;
            el.btnTomarFoto.disabled = true;
            el.mensaje.innerHTML = '<span class="spinner"></span> Validando UID...';
            break;

        case ESTADOS.LISTO:
            document.body.classList.add("estado-listo");
            el.inputUid.disabled = true;
            el.btnValidar.disabled = true;
            el.btnTomarFoto.disabled = false;
            el.videoContainer.style.display = "block";
            el.videoFeed.src = "/video_feed?" + new Date().getTime();
            el.mensaje.innerHTML =
                'Bienvenido <strong>' +
                (datos && datos.nombre ? datos.nombre : "") +
                '</strong>. Depositá tu residuo frente a la cámara.';
            break;

        case ESTADOS.ANALIZANDO:
            document.body.classList.add("estado-analizando");
            el.btnTomarFoto.disabled = true;
            el.previewContainer.style.display = "block";
            el.mensaje.innerHTML = '<span class="spinner"></span> IA analizando residuo...';
            break;

        case ESTADOS.RESULTADO: {
            el.resultado.style.display = "block";
            if (datos && datos.puntos > 0) {
                document.body.classList.add("estado-resultado-aprobado");
                el.resultado.className = "resultado-exito";
                el.resultado.innerHTML = "¡Aprobado! +" + datos.puntos + " Punto";
                el.mensaje.innerHTML =
                    "Material: " +
                    datos.material +
                    " (" +
                    Math.round((datos.confianza || 0) * 100) +
                    "% confianza)";
            } else if (datos && datos.error) {
                document.body.classList.add("estado-error");
                el.resultado.className = "resultado-error";
                el.resultado.innerHTML = datos.mensaje || "Error de conexion";
                el.mensaje.innerHTML = "Intente nuevamente mas tarde";
            } else {
                document.body.classList.add("estado-resultado-rechazado");
                el.resultado.className = "resultado-rechazo";
                el.resultado.innerHTML = "Residuo rechazado o no reconocido";
                let razon = "0 puntos - ";
                if (datos && datos.material === "rechazo") {
                    razon += "Material no reciclable";
                } else {
                    razon += "Confianza baja (" + Math.round((datos && datos.confianza || 0) * 100) + "%)";
                }
                el.mensaje.innerHTML = razon;
            }
            timerReset = setTimeout(function () {
                cambiarEstado(ESTADOS.IDLE);
            }, 5000);
            break;
        }
    }
}

async function validarUid() {
    if (estadoActual === ESTADOS.VALIDANDO) return;
    const uid = el.inputUid.value.trim();
    if (!uid || uid.length < 10) {
        el.mensaje.innerHTML = "Ingresa un UID válido (mínimo 10 caracteres)";
        return;
    }
    estadoActual = ESTADOS.VALIDANDO;
    cambiarEstado(ESTADOS.VALIDANDO);
    try {
        const response = await fetch("/validate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ uid: uid }),
        });
        const data = await response.json();
        if (data.valido) {
            usuarioActual = { id: uid, nombre: data.nombre };
            cambiarEstado(ESTADOS.LISTO, { nombre: data.nombre });
        } else {
            el.mensaje.innerHTML = "UID inválido";
            setTimeout(function () {
                el.inputUid.value = "";
                el.inputUid.focus();
                cambiarEstado(ESTADOS.IDLE);
            }, 2000);
        }
    } catch (error) {
        console.error(error);
        el.mensaje.innerHTML = "Error de conexion con el servidor";
        setTimeout(function () {
            cambiarEstado(ESTADOS.IDLE);
        }, 2000);
    }
}

async function capturarFoto() {
    if (!usuarioActual.id) {
        el.mensaje.innerHTML = "Primero valida un UID";
        return;
    }
    cambiarEstado(ESTADOS.ANALIZANDO);
    try {
        const capturaResp = await fetch("/capturar", { method: "POST" });
        const capturaData = await capturaResp.json();
        if (!capturaData.success) {
            el.mensaje.innerHTML = "Error de camara: " + (capturaData.error || "desconocido");
            setTimeout(function () {
                cambiarEstado(ESTADOS.LISTO, { nombre: usuarioActual.nombre });
            }, 2000);
            return;
        }
        el.previewImage.src = "data:image/jpeg;base64," + capturaData.image;
        el.previewInfo.textContent = "Resolucion: " + capturaData.width + "x" + capturaData.height;
        ultimaImagenBase64 = capturaData.image;
        await clasificarFoto(capturaData.image);
    } catch (error) {
        console.error(error);
        el.mensaje.innerHTML = "Error al capturar imagen";
        setTimeout(function () {
            cambiarEstado(ESTADOS.LISTO, { nombre: usuarioActual.nombre });
        }, 2000);
    }
}

async function clasificarFoto(imagenBase64) {
    try {
        const response = await fetch("/clasificar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                imagen_base64: imagenBase64,
                uid: usuarioActual.id,
                nombre: usuarioActual.nombre,
            }),
        });
        const data = await response.json();
        if (response.ok && data.success !== false) {
            cambiarEstado(ESTADOS.RESULTADO, {
                puntos: data.puntos || 0,
                material: data.material || "rechazo",
                confianza: data.confianza || 0,
            });
        } else if (data.error === "timeout") {
            cambiarEstado(ESTADOS.RESULTADO, {
                error: true,
                mensaje: "Tiempo de espera agotado al clasificar. Intenta de nuevo.",
            });
        } else if (data.error === "error_api") {
            cambiarEstado(ESTADOS.RESULTADO, {
                error: true,
                mensaje: "Error en API de clasificacion: " + (data.detalle || ""),
            });
        } else {
            cambiarEstado(ESTADOS.RESULTADO, {
                error: true,
                mensaje: data.mensaje || data.error || "Clasificacion fallida",
            });
        }
    } catch (error) {
        console.error(error);
        cambiarEstado(ESTADOS.RESULTADO, {
            error: true,
            mensaje: "Error de red al clasificar",
        });
    }
}

function activarDebugValidacion() {
    usuarioActual = { id: "DEBUG_UID", nombre: "Modo Debug" };
    el.inputUid.value = "DEBUG_UID";
    cambiarEstado(ESTADOS.LISTO, { nombre: "Modo Debug" });
}

function mockExito() {
    if (!ultimaImagenBase64) {
        el.mensaje.innerHTML = "Primero captura una foto con el boton 'Tomar foto'";
        return;
    }
    cambiarEstado(ESTADOS.RESULTADO, {
        puntos: 1,
        material: "plastico",
        confianza: 0.95,
    });
}

function mockRechazo() {
    if (!ultimaImagenBase64) {
        el.mensaje.innerHTML = "Primero captura una foto con el boton 'Tomar foto'";
        return;
    }
    var opciones = [
        { material: "rechazo", puntos: 0, confianza: 0.92 },
        { material: "plastico", puntos: 0, confianza: 0.45 },
    ];
    var elegido = opciones[Math.floor(Math.random() * opciones.length)];
    cambiarEstado(ESTADOS.RESULTADO, elegido);
}

el.inputUid.addEventListener("input", function (e) {
    e.target.value = e.target.value.trim();
});
el.inputUid.addEventListener("keypress", function (e) {
    if (e.key === "Enter") validarUid();
});
el.btnValidar.addEventListener("click", validarUid);
el.btnTomarFoto.addEventListener("click", capturarFoto);
document.getElementById("debugValidacionBtn").addEventListener("click", activarDebugValidacion);
document.getElementById("mockExitoBtn").addEventListener("click", mockExito);
document.getElementById("mockRechazoBtn").addEventListener("click", mockRechazo);

cambiarEstado(ESTADOS.IDLE);
