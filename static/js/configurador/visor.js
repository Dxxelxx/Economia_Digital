/*
 * Visor 3D basado en TUS modelos .glb (zapato, bolso y sombrero).
 *
 * Qué resuelve:
 *  - zapato.glb viene comprimido con EXT_meshopt_compression: sin el
 *    decodificador Meshopt, GLTFLoader falla y el modelo no aparece.
 *  - Los modelos vienen en escalas muy distintas (el sombrero mide ~300
 *    unidades, el zapato ~0.5): cada uno se escala, centra y apoya en el
 *    piso automáticamente.
 *  - El sombrero no trae normales: se calculan al cargar.
 *  - Los colores se aplican por "rol" (principal, secundario, herraje).
 */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";

const COLOR_HERRAJE = {
    dorado: "#d4a94f",
    plateado: "#cfd2d6",
    negro: "#1c1c1c"
};

// Tamaño (en unidades de la escena) de la dimensión mayor de cada modelo.
const TAMANO_OBJETIVO = 3;

// Dirección desde la que se mira el modelo al empezar (3/4 frontal).
const DIRECCION_INICIAL = new THREE.Vector3(0.78, 0.46, 1.0).normalize();

const VISTAS = {
    frente: new THREE.Vector3(0, 0.12, 1),
    lado: new THREE.Vector3(1, 0.12, 0),
    arriba: new THREE.Vector3(0.001, 1, 0.12),
    tres_cuartos: DIRECCION_INICIAL
};

/**
 * Decide qué parte de la personalización controla cada malla del GLB,
 * según el nombre de la malla o de su material.
 *   bolso.glb    -> materiales: Backpack / Silver / Brown2
 *   sombrero.glb -> mallas: Hat / ring (la cinta)
 *   zapato.glb   -> un único material con textura
 */
function rolDeMalla(clave, malla) {

    const nombres = [
        malla.material?.name,
        malla.name,
        malla.parent?.name
    ].filter(Boolean).join(" ").toLowerCase();

    if (clave === "zapato") return "textura";

    if (/silver|metal|hebilla|buckle|herraje|cierre|zipper/.test(nombres)) {
        return "herraje";
    }

    if (clave === "sombrero") {
        return /ring|cinta|banda|band/.test(nombres) ? "secundario" : "principal";
    }

    if (clave === "bolso") {
        return /brown2|asa|strap|correa|detalle/.test(nombres)
            ? "secundario"
            : "principal";
    }

    return "principal";
}

export class Visor3D {

    /**
     * @param {HTMLElement} contenedor
     * @param {{modelos: Object<string,string>}} opciones
     *        modelos: { zapato: "/static/models/zapato.glb", ... }
     */
    constructor(contenedor, opciones = {}) {

        this.contenedor = contenedor;
        this.rutas = opciones.modelos || {};
        this.producto = null;
        this.config = null;
        this.actual = null;           // { objeto, centro, radio, ... }
        this.cache = {};              // producto -> Promise
        this.meta = null;
        this.escalaAparicion = 1;
        this.texturaGrano = null;
        this.texturaGranoFino = null;
        this.placa = null;
        this.placaTexto = "";

        this.cargador = new GLTFLoader();
        this.cargador.setMeshoptDecoder(MeshoptDecoder);

        // ---------- RENDERER ----------
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.05;

        contenedor.appendChild(this.renderer.domElement);

        // ---------- ESCENA ----------
        this.escena = new THREE.Scene();
        this.escena.background = new THREE.Color("#e9e1d8");

        const pmrem = new THREE.PMREMGenerator(this.renderer);
        this.escena.environment =
            pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
        this.escena.environmentIntensity = 0.6;

        // ---------- LUCES ----------
        this.escena.add(new THREE.HemisphereLight("#ffffff", "#8a7461", 0.7));

        const luz = new THREE.DirectionalLight("#fff4e6", 2.4);
        luz.position.set(4, 7, 5);
        luz.castShadow = true;
        luz.shadow.mapSize.set(2048, 2048);
        luz.shadow.camera.left = -6;
        luz.shadow.camera.right = 6;
        luz.shadow.camera.top = 6;
        luz.shadow.camera.bottom = -6;
        luz.shadow.camera.near = 0.5;
        luz.shadow.camera.far = 25;
        luz.shadow.bias = -0.0004;
        luz.shadow.normalBias = 0.02;
        this.escena.add(luz);

        const relleno = new THREE.DirectionalLight("#d8b08a", 0.8);
        relleno.position.set(-5, 3, -4);
        this.escena.add(relleno);

        // ---------- PISO ----------
        const piso = new THREE.Mesh(
            new THREE.CircleGeometry(7, 72),
            new THREE.MeshStandardMaterial({
                color: "#e2d9cd",
                roughness: 0.95,
                metalness: 0
            })
        );
        piso.rotation.x = -Math.PI / 2;
        piso.position.y = -0.002;
        piso.receiveShadow = true;
        this.escena.add(piso);

        // ---------- CÁMARA Y CONTROLES ----------
        this.camara = new THREE.PerspectiveCamera(38, 1, 0.05, 200);
        this.camara.position.set(5, 3, 6);

        this.controles = new OrbitControls(this.camara, this.renderer.domElement);
        this.controles.enableDamping = true;
        this.controles.dampingFactor = 0.08;
        this.controles.screenSpacePanning = true;
        this.controles.maxPolarAngle = Math.PI * 0.495;
        this.controles.autoRotate = true;
        this.controles.autoRotateSpeed = 1.6;
        this.controles.target.set(0, 1, 0);

        this.controles.addEventListener("start", () => {
            this.meta = null;
            this.controles.autoRotate = false;
            this.alCambiarGiro?.(false);
        });

        // ---------- GRUPO DEL PRODUCTO ----------
        this.grupo = new THREE.Group();
        this.escena.add(this.grupo);

        // ---------- TAMAÑO ----------
        this.observador = new ResizeObserver(() => this.ajustarTamano());
        this.observador.observe(contenedor);
        this.ajustarTamano();

        // ---------- BUCLE ----------
        this.activo = true;
        this.bucle = this.bucle.bind(this);
        requestAnimationFrame(this.bucle);
    }

    // -----------------------------------------------------------
    // TAMAÑO Y BUCLE
    // -----------------------------------------------------------

    ajustarTamano() {

        const ancho = this.contenedor.clientWidth || 600;
        const alto = this.contenedor.clientHeight || 500;

        this.renderer.setSize(ancho, alto, false);
        this.camara.aspect = ancho / alto;
        this.camara.updateProjectionMatrix();
    }

    bucle() {

        if (!this.activo) return;

        requestAnimationFrame(this.bucle);

        if (this.meta) {
            this.camara.position.lerp(this.meta.pos, 0.12);
            this.controles.target.lerp(this.meta.target, 0.12);

            if (
                this.camara.position.distanceTo(this.meta.pos) < 0.01 &&
                this.controles.target.distanceTo(this.meta.target) < 0.01
            ) {
                this.meta = null;
            }
        }

        if (this.escalaAparicion < 1) {
            this.escalaAparicion = Math.min(1, this.escalaAparicion + 0.06);
            const s = 0.9 + 0.1 * (1 - Math.pow(1 - this.escalaAparicion, 3));
            this.grupo.scale.setScalar(s);
        }

        this.controles.update();
        this.renderer.render(this.escena, this.camara);
    }

    // -----------------------------------------------------------
    // CARGA DE MODELOS
    // -----------------------------------------------------------

    /** Carga (una sola vez) el .glb de un producto y lo normaliza. */
    cargarModelo(clave) {

        if (this.cache[clave]) return this.cache[clave];

        const ruta = this.rutas[clave];

        if (!ruta) {
            return Promise.reject(
                new Error(`No hay ruta de modelo 3D para "${clave}".`)
            );
        }

        this.cache[clave] = new Promise((resolver, rechazar) => {

            this.cargador.load(
                ruta,
                (gltf) => {
                    try {
                        resolver(this.prepararModelo(clave, gltf.scene));
                    } catch (error) {
                        rechazar(error);
                    }
                },
                undefined,
                (error) => {
                    delete this.cache[clave];
                    rechazar(
                        new Error(
                            `No se pudo cargar ${ruta}: ` +
                            (error?.message || error)
                        )
                    );
                }
            );
        });

        return this.cache[clave];
    }

    prepararModelo(clave, raiz) {

        raiz.traverse((o) => {

            if (!o.isMesh) return;

            // El sombrero.glb no trae normales: sin ellas el modelo
            // se vería negro o plano.
            if (!o.geometry.attributes.normal) {
                o.geometry.computeVertexNormals();
            }

            o.castShadow = true;
            o.receiveShadow = true;
            o.userData.rol = rolDeMalla(clave, o);
            o.userData.mapa = o.material?.map || null;
        });

        // --- escalar, centrar y apoyar en el piso ---
        const envoltura = new THREE.Group();
        envoltura.add(raiz);
        envoltura.updateMatrixWorld(true);

        let caja = new THREE.Box3().setFromObject(envoltura);
        const tam = caja.getSize(new THREE.Vector3());
        const mayor = Math.max(tam.x, tam.y, tam.z) || 1;

        raiz.scale.multiplyScalar(TAMANO_OBJETIVO / mayor);
        envoltura.updateMatrixWorld(true);

        caja = new THREE.Box3().setFromObject(envoltura);
        const centro = caja.getCenter(new THREE.Vector3());

        raiz.position.x -= centro.x;
        raiz.position.z -= centro.z;
        raiz.position.y -= caja.min.y;
        envoltura.updateMatrixWorld(true);

        caja = new THREE.Box3().setFromObject(envoltura);

        return {
            objeto: envoltura,
            caja,
            centro: caja.getCenter(new THREE.Vector3()),
            radio: 0.5 * caja.getSize(new THREE.Vector3()).length()
        };
    }

    // -----------------------------------------------------------
    // TEXTURAS Y MATERIALES
    // -----------------------------------------------------------

    crearGrano(celdas, tamano = 256) {

        const pequeno = document.createElement("canvas");
        pequeno.width = pequeno.height = celdas;

        const ctx = pequeno.getContext("2d");
        const datos = ctx.createImageData(celdas, celdas);

        for (let k = 0; k < datos.data.length; k += 4) {
            const v = 100 + Math.random() * 110;
            datos.data[k] = datos.data[k + 1] = datos.data[k + 2] = v;
            datos.data[k + 3] = 255;
        }

        ctx.putImageData(datos, 0, 0);

        const grande = document.createElement("canvas");
        grande.width = grande.height = tamano;

        const g = grande.getContext("2d");
        g.imageSmoothingEnabled = true;
        g.imageSmoothingQuality = "high";
        g.drawImage(pequeno, 0, 0, tamano, tamano);

        const textura = new THREE.CanvasTexture(grande);
        textura.wrapS = textura.wrapT = THREE.RepeatWrapping;
        textura.repeat.set(2, 2);

        return textura;
    }

    obtenerGrano(fino) {

        if (fino) {
            this.texturaGranoFino ||= this.crearGrano(96);
            return this.texturaGranoFino;
        }

        this.texturaGrano ||= this.crearGrano(28);
        return this.texturaGrano;
    }

    /** Luminosidad media (lineal) de una textura, para normalizar el tinte. */
    luminosidadMedia(textura) {

        if (textura.userData.lumMedia) return textura.userData.lumMedia;

        let media = 0.4;

        try {
            const lado = 32;
            const canvas = document.createElement("canvas");
            canvas.width = canvas.height = lado;

            const ctx = canvas.getContext("2d", { willReadFrequently: true });
            ctx.drawImage(textura.image, 0, 0, lado, lado);

            const datos = ctx.getImageData(0, 0, lado, lado).data;
            const lineal = (c) => Math.pow(c / 255, 2.2);
            let suma = 0;

            for (let k = 0; k < datos.length; k += 4) {
                suma +=
                    0.2126 * lineal(datos[k]) +
                    0.7152 * lineal(datos[k + 1]) +
                    0.0722 * lineal(datos[k + 2]);
            }

            media = Math.max(0.02, suma / (lado * lado));

        } catch (error) {
            console.warn("No se pudo medir la textura del zapato:", error);
        }

        textura.userData.lumMedia = media;
        return media;
    }

    /**
     * Zapato: conserva el relieve/sombras de la textura original pero
     * deja que el cliente elija CUALQUIER color. Se usa la luminosidad
     * de la textura y se multiplica por el color elegido.
     */
    materialConTextura(config, mapa) {

        const material = this.materialPrincipal(config, false);

        if (!mapa) return material;

        const norma = 0.55 / this.luminosidadMedia(mapa);

        material.map = mapa;
        material.customProgramCacheKey = () => "tinte-luminosidad";

        material.onBeforeCompile = (shader) => {

            shader.uniforms.uNormaLum = { value: norma };

            shader.fragmentShader =
                "uniform float uNormaLum;\n" +
                shader.fragmentShader.replace(
                    "#include <map_fragment>",
                    `
                    #ifdef USE_MAP
                        vec4 muestraColor = texture2D( map, vMapUv );
                        float lum = dot( muestraColor.rgb, vec3( 0.2126, 0.7152, 0.0722 ) );
                        diffuseColor.rgb *= clamp( lum * uNormaLum, 0.12, 1.9 );
                    #endif
                    `
                );
        };

        return material;
    }

    materialPrincipal(config, conRelieve = true) {

        if (config.material === "ante") {
            return new THREE.MeshPhysicalMaterial({
                color: config.color,
                roughness: 0.96,
                metalness: 0,
                sheen: 1,
                sheenRoughness: 0.85,
                sheenColor: new THREE.Color(config.color).offsetHSL(0, 0, 0.18),
                bumpMap: conRelieve ? this.obtenerGrano(true) : null,
                bumpScale: 0.35,
                side: THREE.DoubleSide
            });
        }

        if (config.material === "sintetico") {
            return new THREE.MeshPhysicalMaterial({
                color: config.color,
                roughness: 0.28,
                metalness: 0.05,
                clearcoat: 0.9,
                clearcoatRoughness: 0.18,
                side: THREE.DoubleSide
            });
        }

        return new THREE.MeshPhysicalMaterial({
            color: config.color,
            roughness: 0.5,
            metalness: 0,
            clearcoat: 0.3,
            clearcoatRoughness: 0.45,
            bumpMap: conRelieve ? this.obtenerGrano(false) : null,
            bumpScale: 0.9,
            side: THREE.DoubleSide
        });
    }

    crearMaterial(malla, config) {

        const rol = malla.userData.rol;
        const tieneUV = !!malla.geometry.attributes.uv;

        switch (rol) {

            case "textura":
                return this.materialConTextura(config, malla.userData.mapa);

            case "secundario":
                return new THREE.MeshStandardMaterial({
                    color: config.colorSecundario,
                    roughness: 0.6,
                    metalness: 0,
                    side: THREE.DoubleSide
                });

            case "herraje": {
                const negro = config.herrajes === "negro";

                return new THREE.MeshStandardMaterial({
                    color: COLOR_HERRAJE[config.herrajes] || COLOR_HERRAJE.dorado,
                    metalness: negro ? 0.6 : 0.95,
                    roughness: negro ? 0.4 : 0.22,
                    side: THREE.DoubleSide
                });
            }

            default:
                return this.materialPrincipal(config, tieneUV);
        }
    }

    aplicarColores(config) {

        if (!this.actual) return;

        this.actual.objeto.traverse((o) => {

            if (!o.isMesh) return;

            // Se desecha el material anterior que creamos nosotros,
            // nunca la textura original del modelo.
            if (o.userData.nuestro) {
                o.material.dispose();
            }

            o.material = this.crearMaterial(o, config);
            o.userData.nuestro = true;
        });
    }

    // -----------------------------------------------------------
    // INICIALES (grabadas sobre la superficie del propio modelo)
    // -----------------------------------------------------------

    /**
     * Busca con un rayo el punto del modelo donde van las iniciales:
     * por el lado "plano" (el eje horizontal más delgado), a una altura
     * propia de cada producto. Devuelve posición y normal.
     */
    puntoParaIniciales() {

        const { caja, objeto } = this.actual;

        // El cálculo se hace con escala 1 (la animación de aparición
        // escala temporalmente el grupo).
        const escalaGuardada = this.grupo.scale.x;
        this.grupo.scale.setScalar(1);
        this.grupo.updateMatrixWorld(true);

        const tam = caja.getSize(new THREE.Vector3());
        const centro = caja.getCenter(new THREE.Vector3());

        const alLargoDeX = tam.x <= tam.z;
        const dir = alLargoDeX
            ? new THREE.Vector3(1, 0, 0)
            : new THREE.Vector3(0, 0, 1);

        const fraccion = { zapato: 0.4, bolso: 0.55, sombrero: 0.5 }[this.producto] ?? 0.5;
        const y = caja.min.y + tam.y * fraccion;

        const origen = new THREE.Vector3(centro.x, y, centro.z)
            .addScaledVector(dir, Math.max(tam.x, tam.z));

        const malla = [];
        objeto.traverse((o) => { if (o.isMesh) malla.push(o); });

        const rayo = new THREE.Raycaster(origen, dir.clone().negate());
        const golpes = rayo.intersectObjects(malla, false);

        let punto;
        let normal;

        if (golpes.length) {

            const g = golpes[0];
            punto = g.point.clone();
            normal = g.face.normal.clone().transformDirection(g.object.matrixWorld);

            // La normal debe mirar hacia fuera (hacia el rayo).
            if (normal.dot(dir) < 0) normal.negate();

        } else {

            // Sin impacto: se apoya en la cara de la caja.
            punto = new THREE.Vector3(centro.x, y, centro.z)
                .addScaledVector(dir, (alLargoDeX ? tam.x : tam.z) / 2);
            normal = dir.clone();
        }

        this.grupo.scale.setScalar(escalaGuardada);
        this.grupo.updateMatrixWorld(true);

        return { punto, normal };
    }

    quitarPlaca() {

        if (!this.placa) return;

        this.grupo.remove(this.placa);
        this.placa.geometry.dispose();
        this.placa.material.map?.dispose();
        this.placa.material.dispose();
        this.placa = null;
    }

    actualizarPlaca(config) {

        const texto = (config.iniciales || "").trim().toUpperCase().slice(0, 3);
        const colorBase = COLOR_HERRAJE[config.herrajes] || COLOR_HERRAJE.dorado;
        const color = `#${new THREE.Color(colorBase).offsetHSL(0, 0, 0.1).getHexString()}`;
        const firma = `${texto}|${color}|${this.producto}`;

        if (firma === this.placaFirma) return;
        this.placaFirma = firma;

        if (this.placa) {
            this.grupo.remove(this.placa);
            this.placa.geometry.dispose();
            this.placa.material.map?.dispose();
            this.placa.material.dispose();
            this.placa = null;
        }

        if (!texto || !this.actual) return;

        const ancho = 512;
        const alto = 256;
        const canvas = document.createElement("canvas");
        canvas.width = ancho;
        canvas.height = alto;

        const ctx = canvas.getContext("2d");
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        let fuente = alto * 0.7;
        ctx.font = `700 ${fuente}px Georgia, "Times New Roman", serif`;

        const medida = ctx.measureText(texto).width;
        if (medida > ancho * 0.94) {
            fuente *= (ancho * 0.94) / medida;
            ctx.font = `700 ${fuente}px Georgia, "Times New Roman", serif`;
        }

        // Relieve: sombra oscura + brillo + color del herraje.
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillText(texto, ancho / 2 + 4, alto / 2 + 5);
        ctx.fillStyle = color;
        ctx.fillText(texto, ancho / 2, alto / 2);

        const textura = new THREE.CanvasTexture(canvas);
        textura.colorSpace = THREE.SRGBColorSpace;
        textura.anisotropy = 4;

        const anchoPlano = Math.min(1.3, 0.45 + 0.22 * texto.length);

        this.placa = new THREE.Mesh(
            new THREE.PlaneGeometry(anchoPlano, anchoPlano * (alto / ancho)),
            new THREE.MeshStandardMaterial({
                map: textura,
                transparent: true,
                roughness: 0.35,
                metalness: 0.4,
                depthWrite: false,
                polygonOffset: true,
                polygonOffsetFactor: -4,
                polygonOffsetUnits: -4
            })
        );

        const { punto, normal } = this.puntoParaIniciales();

        this.placa.position.copy(punto).addScaledVector(normal, 0.012);
        this.placa.lookAt(punto.clone().add(normal));
        this.placa.renderOrder = 5;

        this.grupo.add(this.placa);
    }

    // -----------------------------------------------------------
    // ACTUALIZAR (punto de entrada principal)
    // -----------------------------------------------------------

    /**
     * config: { producto, color, colorSecundario, material, estilo,
     *           herrajes, iniciales }
     */
    actualizar(config) {

        this.config = { ...config };

        if (config.producto === this.producto && this.actual) {
            this.aplicarColores(this.config);
            this.actualizarPlaca(this.config);
            return;
        }

        if (config.producto === this.pendiente) return;

        this.pendiente = config.producto;
        this.alEstado?.("Cargando modelo 3D…");

        this.cargarModelo(config.producto)
            .then((modelo) => {

                // Si el cliente cambió de producto mientras cargaba, se ignora.
                if (this.pendiente !== config.producto) return;
                this.pendiente = null;

                this.quitarPlaca();

                if (this.actual) {
                    this.grupo.remove(this.actual.objeto);
                }

                this.actual = modelo;
                this.producto = config.producto;
                this.grupo.add(modelo.objeto);

                this.aplicarColores(this.config);
                this.anclaje = null;
                this.placaFirma = null;
                this.actualizarPlaca(this.config);

                this.escalaAparicion = 0;
                this.grupo.scale.setScalar(0.9);
                this.encuadrar(true);

                this.alEstado?.(null);

                if (!this.primerRender) {
                    this.primerRender = true;
                    this.alListo?.();
                }
            })
            .catch((error) => {
                this.pendiente = null;
                console.error("Visor 3D:", error);
                this.alError?.(error.message || String(error));
            });
    }

    // -----------------------------------------------------------
    // CÁMARA
    // -----------------------------------------------------------

    posicionPara(direccion) {

        const { centro, radio } = this.actual;
        const fov = (this.camara.fov * Math.PI) / 180;

        let distancia = (radio / Math.sin(fov / 2)) * 0.95;

        if (this.camara.aspect < 1) {
            distancia /= this.camara.aspect;
        }

        return {
            pos: centro.clone().add(
                direccion.clone().normalize().multiplyScalar(distancia)
            ),
            target: centro.clone()
        };
    }

    limitarZoom() {
        this.controles.minDistance = this.actual.radio * 0.9;
        this.controles.maxDistance = this.actual.radio * 6;
    }

    encuadrar(inmediato = false) {

        if (!this.actual) return;

        this.limitarZoom();

        const { pos, target } = this.posicionPara(DIRECCION_INICIAL);

        if (inmediato) {
            this.camara.position.copy(pos);
            this.controles.target.copy(target);
            this.meta = null;
        } else {
            this.meta = { pos, target };
        }

        this.controles.update();
    }

    restablecerVista() {
        this.encuadrar(false);
    }

    irAVista(nombre) {

        const direccion = VISTAS[nombre];

        if (!direccion || !this.actual) return;

        this.meta = this.posicionPara(direccion);
    }

    girar(activo) {
        this.controles.autoRotate = !!activo;
        if (activo) this.meta = null;
    }

    estaGirando() {
        return this.controles.autoRotate;
    }

    capturar() {
        this.renderer.render(this.escena, this.camara);
        return this.renderer.domElement.toDataURL("image/png");
    }

    destruir() {
        this.activo = false;
        this.observador.disconnect();
        this.controles.dispose();
        this.renderer.dispose();
        this.renderer.domElement.remove();
    }
}