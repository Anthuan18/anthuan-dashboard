import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import json
import os

st.set_page_config(
    page_title="EDRA - Pre UNI", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicialización de estados de visualización
if "mensaje_guardado" not in st.session_state:
    st.session_state["mensaje_guardado"] = False
    
# ============================================
# CONFIGURACIÓN DE FIREBASE
# ============================================

# Inicializar Firebase Admin SDK (solo una vez)
if not firebase_admin._apps:
    # Intentar cargar desde Secrets de Streamlit (producción)
    if 'firebase_credentials' in st.secrets:
        cred_dict = dict(st.secrets['firebase_credentials'])
        cred = credentials.Certificate(cred_dict)
    else:
        # Cargar desde archivo local (desarrollo)
        cred = credentials.Certificate("firebase_credentials.json")
    
    firebase_admin.initialize_app(cred)

# Inicializar cliente de Firestore
db = firestore.client()

def guardar_datos_ciclo_automatico():
    """Consolida la configuración actual (incluyendo evaluaciones) y la guarda de forma segura."""
    try:
        user_id = st.session_state['user_id']
        key_lista_cursos = f"lista_cursos_config_{user_id}"
        
        # 1. Consolidar el horario semanal
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        horario_consolidado = {}
        for dia in dias_semana:
            key_estado_dia = f"items_horario_{dia}_{user_id}"
            if key_estado_dia in st.session_state:
                horario_consolidado[dia] = st.session_state[key_estado_dia]
            else:
                horario_consolidado[dia] = config_actual.get("horario", {}).get(dia, [])

        # 2. Recuperar de forma segura los valores de la pestaña 1
        tipo_prep = st.session_state.get("input_tipo_preparacion", config_actual.get("tipo_preparacion", "Semestral"))
        proc_adm = st.session_state.get("input_proces_admision", config_actual.get("proceso_admision", ""))
        
        # Reconstruir nombre del ciclo
        nombre_ciclo_completo = f"{tipo_prep} {proc_adm}".strip()

        # 3. Manejar las fechas de forma segura
        f_inicio = st.session_state.get("input_fecha_inicio")
        if f_inicio:
            fecha_inicio_str = f_inicio.strftime("%Y/%m/%d")
        else:
            fecha_inicio_str = config_actual.get("fecha_inicio", "2026/01/01")

        f_fin = st.session_state.get("input_fecha_fin")
        if f_fin:
            fecha_fin_str = f_fin.strftime("%Y/%m/%d")
        else:
            fecha_fin_str = config_actual.get("fecha_fin", "2026/12/31")

        # 4. NUEVO: Recuperar configuración de evaluaciones de forma segura
        config_evals_actual = config_actual.get("evaluaciones", {})
        
        # Leemos el input de la pantalla, si no está renderizado en ese momento, mantenemos el que ya existía
        preguntas_semanal_val = st.session_state.get("input_preguntas_semanal", config_evals_actual.get("preguntas_semanal", 60))
        preguntas_simulacro_val = st.session_state.get("input_preguntas_simulacro", config_evals_actual.get("preguntas_simulacro", 100))

        # 5. Armar estructura JSON completa con la nueva sección 'evaluaciones'
        nueva_config = {
            'ciclo': nombre_ciclo_completo,
            'universidad': config_actual.get("universidad", "UNI"),
            'tipo_preparacion': tipo_prep,
            'proceso_admision': proc_adm,
            'fecha_inicio': fecha_inicio_str,
            'fecha_fin': fecha_fin_str,
            'catalogo_cursos': st.session_state.get(key_lista_cursos, config_actual.get("catalogo_cursos", [])),
            'horario': horario_consolidado,
            'evaluaciones': {
                'preguntas_semanal': int(preguntas_semanal_val),
                'preguntas_simulacro': int(preguntas_simulacro_val)
            }
        }

        # 6. Guardar en Firestore
        db.collection('usuarios').document(user_id).set({'config': nueva_config}, merge=True)
        
        # 7. Actualizar caché y variables locales de forma segura
        config_actual.update(nueva_config)
        
        key_cache = f"cached_datos_{user_id}"
        datos_locales = st.session_state.get(key_cache, {})
        datos_locales["config"] = nueva_config
        st.session_state[key_cache] = datos_locales
        
        return True
    except Exception as e:
        st.error(f"Error al guardar automáticamente: {e}")
        return False
# ============================================
# SISTEMA DE LOGIN
# ============================================

def crear_usuario(username, password):
    """Crea un nuevo usuario usando el truco del email fantasma"""
    try:
                # Validar username
        username = username.strip()
        if not username:
            return None, "El nombre de usuario no puede estar vacío"
        if len(username) < 3:
            return None, "El nombre de usuario debe tener al menos 3 caracteres"
        if "@" in username:
            return None, "El nombre de usuario no puede contener @"
        if " " in username:
            return None, "El nombre de usuario no puede contener espacios"
        # Truco: convertir username en email fantasma
        email_fantasma = f"{username}@unidashboard.com"
        
        # Crear usuario en Firebase Auth
        user = auth.create_user(
            email=email_fantasma,
            password=password,
            display_name=username
        )
        
        # Crear documento del usuario en Firestore
        db.collection('usuarios').document(user.uid).set({
            'username': username,
            'fecha_creacion': firestore.SERVER_TIMESTAMP,
            'config': {
                'universidad': 'UNI',
                'ciclo': 'Sin configurar',
                'materias': [],
                'horario': {}
            },
            'diario': [],
            'semanal': []
        })
        
        return user.uid, username
    except Exception as e:
        return None, str(e)
def login_usuario(username, password):
    """Verifica las credenciales del usuario usando Firebase REST API"""
    import requests

        # Validar username
    username = username.strip()
    if not username:
        return None, "El nombre de usuario no puede estar vacío"
    if len(username) < 3:
        return None, "El nombre de usuario debe tener al menos 3 caracteres"
    if "@" in username:
        return None, "El nombre de usuario no puede contener @"
    if " " in username:
        return None, "El nombre de usuario no puede contener espacios"
    
    try:
        email_fantasma = f"{username}@unidashboard.com"
        
        # Obtener la API Key de Streamlit Secrets
        api_key = st.secrets.get("firebase_api_key")
        if not api_key:
            st.error("🔐 Falta configurar 'firebase_api_key' en los Secrets de Streamlit")
            st.stop()        
        # URL de la API REST de Firebase para verificar contraseña
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        
        # Datos a enviar
        payload = {
            "email": email_fantasma,
            "password": password,
            "returnSecureToken": True
        }
        
        # Hacer la petición
        response = requests.post(url, json=payload)
        
        # Verificar si fue exitoso
        if response.status_code == 200:
            data = response.json()
            user_id = data["localId"]
            
            # Obtener información del usuario desde Firebase Admin
            user = auth.get_user(user_id)
            return user.uid, user.display_name
        else:
            # Credenciales incorrectas
            return None, "Usuario o contraseña incorrectos"
            
    except Exception as e:
        return None, "Usuario o contraseña incorrectos"

def pantalla_login():
    """Muestra la pantalla de login con pestañas organizadas"""
    st.set_page_config(page_title="EDRA - Pre UNI", layout="wide")
    
    st.title("🎓 EDRA - Preu")
    st.markdown("### Tu camino hacia la universidad")
    st.markdown("Estadísticas de rendimiento académico (EDRA) para estudiantes preuniversitarios")
    st.divider()
    
    # Creamos las dos pestañas para organizar la pantalla
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta"])
    
    with tab1:
        st.markdown("#### Acceso a tu cuenta")
        
        # Google Sign-In (Preparado para la futura implementación)
        if st.button("🔴🟡🟢🔵 Iniciar sesión con Google", use_container_width=True, key="btn_google"):
            st.warning("⚠️ Esta función estará disponible pronto")
        
        st.divider()

        st.markdown("#### 👤 Iniciar sesión con nombre de usuario")
        
        # Formulario Login
        username_login = st.text_input("Nombre de usuario", key="username_login")
        password_login = st.text_input("Contraseña", type="password", key="password_login")
        
        if st.button("🚀 Entrar", type="primary", use_container_width=True):
            if username_login and password_login:
                user_id, username = login_usuario(username_login, password_login)
                if user_id:
                    st.session_state['user_id'] = user_id
                    st.session_state['username'] = username
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error(username) # Aquí se muestra el error de login_usuario
            else:
                st.warning("⚠️ Completa todos los campos")
                    
    with tab2:
        st.markdown("#### Crea tu cuenta")
        
        username_register = st.text_input("Elige un nombre de usuario", key="username_register")
        password_register = st.text_input("Elige una contraseña", type="password", key="password_register")
        password_confirm = st.text_input("Confirma tu contraseña", type="password", key="password_confirm")

        if st.button("🎯 Registrarme", type="primary", use_container_width=True):
            username_register = username_register.strip()
            password_register = password_register.strip()
            password_confirm = password_confirm.strip()
            
            if username_register and password_register and password_confirm:
                if len(password_register) < 6:
                    st.error("❌ La contraseña debe tener al menos 6 caracteres")
                elif password_register == password_confirm:
                    user_id, result = crear_usuario(username_register, password_register)
                    if user_id:
                        st.success("¡Cuenta creada!")
                        st.session_state['user_id'] = user_id
                        st.session_state['username'] = username_register
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else:
                        st.error(f"Error: {result}")
                else:
                    st.error("❌ Las contraseñas no coinciden.")
            else:
                st.warning("⚠️ Completa todos los campos")


# ============================================
# CONTROL DE ACCESO
# ============================================

# Inicializar estado de sesión
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Si no está logueado, mostrar pantalla de login
if not st.session_state['logged_in']:
    pantalla_login()
    st.stop()  # Detiene la ejecución del resto del código

# Si está logueado, continuar con el dashboard
username = st.session_state.get('username', 'Usuario')
st.sidebar.markdown(f"### 👤 {username}")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state['logged_in'] = False
    st.rerun()
# ========================================================
# 📂 PASO 2: SELECTOR HISTÓRICO EN LA BARRA LATERAL
# ========================================================
# 1. Cargamos los nombres de los ciclos archivados desde Firestore
ciclos_pasados = ["Ciclo Activo (Actual)"]
try:
    historial_ref = db.collection('usuarios').document(user_id).collection('historial_ciclos').stream()
    for doc_historia in historial_ref:
        data_h = doc_historia.to_dict()
        if "nombre_ciclo" in data_h:
            ciclos_pasados.append(data_h["nombre_ciclo"])
except Exception:
    pass  # Si no hay historial todavía, se queda solo con el Activo

# 2. Dibujamos el selector en la barra lateral
ciclo_elegido = st.sidebar.selectbox(
    "📂 Ver Periodo:", 
    options=ciclos_pasados, 
    key="selector_ciclo_historico"
)

# 3. EL INTERRUPTOR LÓGICO: Si seleccionas un ciclo pasado, cambiamos los datos en memoria
if ciclo_elegido != "Ciclo Activo (Actual)":
    historial_ref = db.collection('usuarios').document(user_id).collection('historial_ciclos').where("nombre_ciclo", "==", ciclo_elegido).limit(1).stream()
    for doc_historia in historial_ref:
        data_h = doc_historia.to_dict()
        # Interceptamos temporalmente los datos que alimentan tus gráficos
        datos["diario"] = data_h.get("diario", [])
        datos["semanal"] = data_h.get("semanal", [])
        datos["config"] = data_h.get("config_ciclo", {})


# ============================================
# AQUÍ VA EL RESTO DE TU DASHBOARD ACTUAL
# ============================================
import streamlit as st
import json
import os
from datetime import datetime
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
# Hora actual en Perú (GMT-5)
def hora_peru():
    return datetime.now(timezone(timedelta(hours=-5)))

def fecha_hoy_peru():
    return hora_peru().strftime("%Y-%m-%d")
# ============================================
# CONFIGURACIÓN INICIAL
# ============================================
st.set_page_config(
    page_title="EDRA - Pre UNI", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Personalizado
st.markdown("""
<style>
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    .stButton > button { border-radius: 10px; }
    .js-plotly-plot .plotly { width: 100% !important; }
    
    .modebar-btn[data-title="Pan"] { background-color: #0099ff !important; border-radius: 5px !important; padding: 5px !important; }
    .modebar-btn[data-title="Pan"] svg { fill: white !important; }
    
    /* Casita (Reset axes) SIN COLOR */
    .modebar-btn[data-title="Reset axes"] { background-color: transparent !important; }
    .modebar-btn[data-title="Reset axes"] svg { fill: #8b949e !important; } /* Gris claro */

    /* Autoscale (Flechitas cruzadas) VERDE */
    .modebar-btn[data-title="Autoscale"] { background-color: #00d4aa !important; border-radius: 5px !important; padding: 5px !important; }
    .modebar-btn[data-title="Autoscale"] svg { fill: white !important; }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURACIÓN Y DATOS
# ============================================

# ==========================================================
# CONFIGURACIÓN Y DATOS DE RESPALDO (FALLBACK)
# ==========================================================

CATALOGO_PREDETERMINADO = []
HORARIO_PREDETERMINADO = {}

NOMBRES_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

def cargar_datos():
    """Carga los datos del usuario actual desde Firestore (con cache en session_state)"""
    if 'user_id' not in st.session_state:
        return {"diario": [], "semanal": [], "config": {}}
    
    user_id = st.session_state['user_id']
    cache_key = f"cached_datos_{user_id}"
    
    # CACHE: Si ya cargamos en esta sesión, devolver desde memoria (¡instantáneo!)
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # Primera carga: leer de Firestore
    try:
        doc_ref = db.collection('usuarios').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            datos = doc.to_dict()
            if 'diario' not in datos:
                datos['diario'] = []
            if 'semanal' not in datos:
                datos['semanal'] = []
            if 'config' not in datos or not isinstance(datos['config'], dict):
                datos['config'] = {}
            
            # Asegurar campos clave dentro de config para evitar fallos de lectura
            if 'catalogo_cursos' not in datos['config']:
                datos['config']['catalogo_cursos'] = []
            if 'horario' not in datos['config']:
                datos['config']['horario'] = {}
            
            # ========================================================
            # VERIFICACIÓN AUTOMÁTICA DE FIN DE CICLO (POR FECHA)
            # ========================================================
            config_actual = datos.get("config", {})
            fecha_fin_str = config_actual.get("fecha_fin", "2026/12/31")
            nombre_ciclo_actual = config_actual.get("ciclo", "Ciclo sin configurar")
    
            # Obtenemos el día de hoy usando tu función nativa del sistema
            hoy = fecha_hoy_peru()
            if hasattr(hoy, "strftime"):
                hoy_str = hoy.strftime("%Y/%m/%d")
                hoy_date = hoy
            else:
                # Si fecha_hoy_peru() ya devuelve un string tipo "2026-07-18"
                hoy_str = str(hoy).replace("-", "/")
                try:
                    hoy_date = datetime.strptime(hoy_str, "%Y/%m/%d").date()
                except ValueError:
                    hoy_date = datetime.now().date()
    
            # Parsear la fecha de fin del ciclo para comparar objetos .date()
            try:
                fecha_fin_ciclo = datetime.strptime(fecha_fin_str, "%Y/%m/%d").date()
            except ValueError:
                try:
                    fecha_fin_ciclo = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
                except ValueError:
                    fecha_fin_ciclo = hoy_date
    
            # 🔥 DESACTIVACIÓN TEMPORAL DE EMERGENCIA (Para que no borre tus datos)
            # Solo se ejecuta el archivo automático si se cumplen TODAS estas condiciones:
            if (hoy_date > fecha_fin_ciclo and 
                len(datos.get("diario", [])) > 0 and 
                "sin configurar" not in nombre_ciclo_actual.lower() and 
                "nuevo ciclo" not in nombre_ciclo_actual.lower() and
                fecha_fin_str != "2026/12/31" and  # Evita que se active con la fecha por defecto
                nombre_ciclo_actual.strip() != "" and False):
                
                ciclo_vencido = nombre_ciclo_actual
                
                # 1. Guardamos el respaldo histórico
                historial_registro = {
                    "nombre_ciclo": ciclo_vencido,
                    "config_ciclo": config_actual,
                    "diario": datos.get("diario", []),
                    "semanal": datos.get("semanal", []),
                    "fecha_archivado": hoy_str
                }
                db.collection('usuarios').document(user_id).collection('historial_ciclos').add(historial_registro)
                
                # 2. Reseteamos el horario y actualizamos fechas tentativas a futuro
                config_actual["horario"] = {dia: [] for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]}
                config_actual["fecha_inicio"] = hoy_str
                # Proyectamos el siguiente ciclo a 4 meses en el futuro
                futuro = hoy_date + timedelta(days=120)
                config_actual["fecha_fin"] = futuro.strftime("%Y/%m/%d")
                config_actual["ciclo"] = "Nuevo Ciclo Configurable"
                
                # 3. Limpiamos las colecciones activas en la BD principal
                datos["diario"] = []
                datos["semanal"] = []
                datos["config"] = config_actual
                db.collection('usuarios').document(user_id).set(datos, merge=True)
                
                st.rerun()
    
            # Guardar en cache para próximas lecturas
            st.session_state[cache_key] = datos
            return datos
        else:
            # Estructura por defecto para usuarios completamente nuevos
            default = {
                "diario": [], 
                "semanal": [], 
                "config": {
                    "ciclo": "",
                    "universidad": "UNI",
                    "tipo_preparacion": "",
                    "proceso_admision": "",
                    "fecha_inicio": "",
                    "fecha_fin": "",
                    "catalogo_cursos": [], # Vacío para saber que es un usuario nuevo
                    "horario": {}
                }
            }
            st.session_state[cache_key] = default
            return default
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return {"diario": [], "semanal": [], "config": {}}

def guardar_datos(datos):
    """Guarda los datos del usuario actual en Firestore"""
    if 'user_id' not in st.session_state:
        st.error("No hay usuario logueado")
        return False
    
    user_id = st.session_state['user_id']
    
    try:
        doc_ref = db.collection('usuarios').document(user_id)
        
        # Primero, leer los datos actuales para no perder nada
        doc = doc_ref.get()
        datos_actuales = doc.to_dict() if doc.exists else {}
        
        # Actualizar solo los campos que queremos modificar
        datos_a_guardar = {
            'diario': datos.get('diario', datos_actuales.get('diario', [])),
            'semanal': datos.get('semanal', datos_actuales.get('semanal', [])),
            'materias': datos.get('materias', datos_actuales.get('materias', {})),
            'ultima_actualizacion': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref.update(datos_a_guardar)

                # ACTUALIZAR CACHE: Guardar datos frescos en session_state
        # para que las próximas cargas sean instantáneas
        cache_key = f"cached_datos_{user_id}"
        
        # Recuperamos la configuración que ya existía en caché para no perderla
        config_existente = st.session_state.get(cache_key, {}).get('config', {})
        
        st.session_state[cache_key] = {
            'diario': datos_a_guardar['diario'],
            'semanal': datos_a_guardar['semanal'],
            'materias': datos_a_guardar.get('materias', {})
            'config': config_existente
        }
        
        st.success("✅ Datos guardados correctamente")
        return True
        
    except Exception as e:
        st.error(f"Error al guardar datos: {e}")
        return False
        
# ============================================
# ESTADO DE LA APLICACIÓN
# ============================================
if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = 'inicio'
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# ==========================================================
# ENCEBEZADO Y NAVEGACIÓN
# ==========================================================

# Obtener el nombre del usuario logueado
usuario_actual = st.session_state.get('username', 'Usuario')
datos_usuario = cargar_datos()

# Intentamos obtener la configuración
config_actual = datos_usuario.get("config", {})
catalogo_cursos = config_actual.get("catalogo_cursos", [])

# Si no hay cursos, el ciclo se muestra como no configurado
if not catalogo_cursos:
    nombre_cycle_display = "Ciclo sin configurar"
else:
    nombre_cycle_display = config_actual.get("ciclo", "Semestral básico 2027-1")

st.title(f"🎓 EDRA de {usuario_actual} - Ciclo {nombre_cycle_display}")

# ------------------------------------------------------
# MENSAJE DE BIENVENIDA DINÁMICO
# ------------------------------------------------------
if not catalogo_cursos:
    st.markdown(f"### 👋 ¡Hola {usuario_actual}! Bienvenido a tu panel de preparación.")
    st.info(
        "💡 **Consejo:** Para empezar a medir tu rendimiento y llevar un control exacto de tu disciplina diario, "
        "ve a la sección de **Configuración del Ciclo** para registrar las materias y horas que les dedicarás a solas."
    )
else:
    st.markdown(f"### 👋 Hola {usuario_actual}, aquí verás tus estadísticas de rendimiento académico.")

st.divider()

# ------------------------------------------------------
# ACCESO LIBRE Y UNIFICADO A TODAS LAS VISTAS
# ------------------------------------------------------
if st.session_state.vista_actual == 'inicio':
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 RENDIMIENTO GENERAL", use_container_width=True, key="btn_general"):
            st.session_state.vista_actual = 'general'
            st.rerun()
    with col2:
        if st.button("📘 RENDIMIENTO POR CURSO", use_container_width=True, key="btn_curso"):
            st.session_state.vista_actual = 'curso'
            st.rerun()
            
    # --- 🛡️ FILTRO PROTECTOR DE BOTONES ---
    # Capturamos cuál ciclo está seleccionado en la barra lateral
    ciclo_en_pantalla = st.session_state.get("selector_ciclo_historico", "Ciclo Activo (Actual)")

    # Solo si estamos en el Ciclo Activo se muestran los botones de modificar e ingresar datos
    if ciclo_en_pantalla == "Ciclo Activo (Actual)":
        st.divider()
    
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 REGISTRO DIARIO/EXAMEN", use_container_width=True, key="btn_registro"):
                st.session_state.vista_actual = 'registro'
                st.rerun()
                
            if st.button("⚙️ Configuración del Ciclo", use_container_width=True, key="btn_config_normal"):
                st.session_state.vista_actual = 'configuracion'
                st.rerun()
                
        st.divider()
# ============================================
# VISTA: RENDIMIENTO GENERAL
# ============================================
if st.session_state.vista_actual == 'general':
    st.header("📈 SECCIÓN: RENDIMIENTO GENERAL")
    if st.button("⬅️ Volver al inicio", key="back_general"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
    st.divider()
    
    datos = cargar_datos()
    
    if datos["diario"]:
        # ============================================
        # DETECTAR DÍAS FALTANTES Y AGREGARLOS COMO 0%
        # ============================================
        fechas_registradas = set()
        for dia in datos["diario"]:
            fechas_registradas.add(dia["fecha"])
        
        # Obtener la fecha del primer registro
        primer_registro = min(datos["diario"], key=lambda x: x["fecha"])
        fecha_inicio = datetime.strptime(primer_registro["fecha"], "%Y-%m-%d")
        fecha_hoy = hora_peru()
        
        # Traer el horario del config actual del usuario (o el de respaldo si no hay)
        horario_usuario = config_actual.get("horario", {})
        
        # Generar lista completa de días respetando la fecha de inicio real del ciclo
        dias_completos = []
        dia_actual = fecha_inicio
        
        # Recuperamos la fecha de inicio del ciclo configurada en la base de datos
        try:
            inicio_ciclo_real = datetime.strptime(config_actual.get("fecha_inicio", "2026/07/30"), "%Y/%m/%d").date()
        except Exception:
            try:
                inicio_ciclo_real = datetime.strptime(config_actual.get("fecha_inicio", "2026-07-30"), "%Y-%m-%d").date()
            except Exception:
                inicio_ciclo_real = fecha_inicio.date()

        while dia_actual.date() <= fecha_hoy.date():
            fecha_str = dia_actual.strftime("%Y-%m-%d")
    
            # Verificar si esta fecha ya existe (evitar duplicados)
            if any(d["fecha"] == fecha_str for d in dias_completos):
                 dia_actual += timedelta(days=1)
                 continue
            
            if fecha_str in fechas_registradas:
                # Día registrado, usar datos reales
                dia_data = next(d for d in datos["diario"] if d["fecha"] == fecha_str)
                dias_completos.append(dia_data)
            else:
                # --- 🛡️ EL ESCUDO PROTECTOR ---
                # Si el día actual evaluado es MENOR que la fecha en que inicia tu ciclo,
                # NO creamos ningún registro ficticio en 0% (así no te ensucia el gráfico).
                if dia_actual.date() < inicio_ciclo_real:
                    dia_actual += timedelta(days=1)
                    continue
                
                # Si ya empezó el ciclo, entonces sí se considera falta si no registraste nada:
                dia_semana = dia_actual.weekday()
                nombre_dia = NOMBRES_DIAS[dia_semana]
                
                materias_dia = horario_usuario.get(nombre_dia, [])
                if not materias_dia:
                    materias_dia = HORARIO_PREDETERMINADO.get(nombre_dia, [])
                
                horas_disponibles = sum(int(m.get("horas", 0)) for m in materias_dia)
                if horas_disponibles <= 0:
                    horas_disponibles = 4
                
                registro_ficticio = {
                    "fecha": fecha_str,
                    "dia": nombre_dia,
                    "horas_disponibles_total": horas_disponibles,
                    "materias": {},
                    "Total_Ejercicios_Resueltos_Dia": 0,
                    "Total_Horas_Estudiadas": 0,
                    "es_ficticio": True
                }
                dias_completos.append(registro_ficticio)
            
            dia_actual += timedelta(days=1)
        
        # Eliminar duplicados manteniendo el orden
        dias_vistos = {}
        for dia in dias_completos:
            fecha = dia["fecha"]
            if fecha not in dias_vistos:
                dias_vistos[fecha] = dia
        dias_completos = list(dias_vistos.values())
        
        # ============================================
        # MÉTRICAS BÁSICAS (SOLO CON DÍAS REALES)
        # ============================================
        dias_reales = [d for d in dias_completos if not d.get("es_ficticio", False)]
        total_dias = len(dias_reales)
        total_ejercicios = sum(d["Total_Ejercicios_Resueltos_Dia"] for d in dias_reales)
        total_horas = sum(d["Total_Horas_Estudiadas"] for d in dias_reales)
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("📅 Días registrados", total_dias)
        with col2: st.metric("📝 Ejercicios resueltos", total_ejercicios)
        with col3: st.metric("⏰ Horas de estudio", f"{int(total_horas)}h")
        st.divider()

        # ============================================
        # GRÁFICOS CON TODOS LOS DÍAS (INCLUYENDO 0%)
        # ============================================
        fechas, disc_prom, vel_prom, horas_prom, ejercicios_prom, materias_str_prom = [], [], [], [], [], []
        
        # Eliminar duplicados por fecha
        fechas_vistas = set()
        dias_unicos = []
        for dia in dias_completos:
            if dia["fecha"] not in fechas_vistas:
                 fechas_vistas.add(dia["fecha"])
                 dias_unicos.append(dia)

        # Extraemos el horario del config del usuario para las etiquetas
        horario_usuario = config_actual.get("horario", {})

        for dia in dias_unicos[-30:]:
        
            f = datetime.strptime(dia["fecha"], "%Y-%m-%d")
            fechas.append(f)
                        
            if dia.get("es_ficticio", False):
                # Día no registrado = 0% disciplina, 0 velocidad, 0 horas
                disc_prom.append(0)
                vel_prom.append(0)
                horas_prom.append(0)
                ejercicios_prom.append(0)
                
                # DINÁMICO: Obtener materias programadas usando el nombre del día
                nombre_dia = dia.get("dia", NOMBRES_DIAS[f.weekday()])
                materias_dia_config = horario_usuario.get(nombre_dia, [])
                
                # Si está vacío el config, usamos el respaldo predeterminado
                if not materias_dia_config:
                    materias_dia_config = HORARIO_PREDETERMINADO.get(nombre_dia, [])
                
                # Extraemos solo los nombres de los cursos para armar el texto
                materias_programadas = [m["curso"] for m in materias_dia_config if m.get("curso")]
                
                if materias_programadas:
                    materias_str = "<br>+ ".join(materias_programadas)
                    materias_str_prom.append(f"️ Día no registrado<br>Materias programadas:<br>+ {materias_str}")
                else:
                    materias_str_prom.append("ℹ️ Día no registrado")
            else:
                # Día registrado, calcular valores reales
                if dia["materias"]:
                    disc_prom.append(sum(m["Disciplina"] for m in dia["materias"].values()) / len(dia["materias"]))
                    vel_prom.append(sum(m["Velocidad"] for m in dia["materias"].values()) / len(dia["materias"]))
                    horas_prom.append(dia.get("Total_Horas_Estudiadas", 0))
                    ejercicios_prom.append(sum(m["Ejercicios_Resueltos"] for m in dia["materias"].values()))

                    # Guardar nombres de las materias estudiadas
                    materias_list = list(dia["materias"].keys())
                    materias_str = "<br>+ ".join(materias_list)
                    materias_str_prom.append(materias_str)
                
                else:
                    disc_prom.append(0)
                    vel_prom.append(0)
                    horas_prom.append(0)
                    ejercicios_prom.append(0)
                    materias_str_prom.append("Sin registro")

        promedio_disc = sum(disc_prom) / len(disc_prom) if disc_prom else 0
        st.subheader(f"🔥 DISCIPLINA: {promedio_disc:.1f}%")      
        fig_disc = go.Figure()
        fig_disc.add_trace(go.Scatter(x=fechas, y=disc_prom, mode='lines+markers', name='Disciplina', 
            line=dict(color='#FF4500', width=3), 
            marker=dict(size=8, color='#FF4500'), 
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>🔥 %{y:.1f}% 🔥<br>%{customdata[0]}h de <br>+%{customdata[1]}<extra></extra>',
            customdata=list(zip(horas_prom, materias_str_prom))))        
        fig_disc.update_layout(yaxis_title='Disciplina (%)', yaxis=dict(range=[0, 150]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='closest', height=400, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_disc, use_container_width=True)
        st.divider()

        promedio_vel = sum(vel_prom) / len(vel_prom) if vel_prom else 0
        st.subheader(f"⚡ VELOCIDAD: {promedio_vel:.1f} ejercicios/h")
        fig_vel = go.Figure()
        if vel_prom:
            fig_vel.add_trace(go.Scatter(x=fechas, y=vel_prom, mode='lines+markers', name='Velocidad', 
                line=dict(color='gold', width=3),
                marker=dict(size=8, color='gold'),
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>⚡%{y:.1f}ejer/h⚡ <br> %{customdata[0]} ejer en %{customdata[1]}h de<br>+%{customdata[2]}<extra></extra>',
                customdata=list(zip(ejercicios_prom, horas_prom, materias_str_prom))))
            fig_vel.update_layout(yaxis_title='Velocidad (ejer/h)', yaxis=dict(range=[0, max(30, max(vel_prom)*1.2)]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='closest', height=400, margin=dict(l=50, r=20, t=20, b=50))
            st.plotly_chart(fig_vel, use_container_width=True)
        else:
            st.warning("️ No hay datos de velocidad disponibles")

        # --- EXÁMENES ---
        st.subheader("📄 EXÁMENES")
        prom_sem, prom_uni, cnt_sem, cnt_uni = 0, 0, 0, 0
        prec_sem_total, prec_uni_total = 0, 0
        fechas_sim, notas_sim, tipos_sim = [], [], []
        
        if datos["semanal"]:
            # Ordenamos por fecha asegurándonos de que no falle la comparación
            for sim in sorted(datos["semanal"], key=lambda x: x["fecha"]):
                f = datetime.strptime(sim["fecha"], "%Y-%m-%d")
                fechas_sim.append(f)
                
                # Caso 1: Examen Semanal
                if sim["tipo"] == "Semanal":
                    notas_sim.append(sim["Puntaje_Simulacro"])
                    prom_sem += sim["Puntaje_Simulacro"]
                    cnt_sem += 1
                    tipos_sim.append("Semanal")
                    if "Precisión" in sim: 
                        prec_sem_total += sim["Precisión"]
                
                # Caso 2: Examen Simulacro (Maneja formato nuevo "Simulacro" y formato antiguo "UNI")
                else:
                    # Soporte flexible para la nota: busca "Puntaje_Simulacro" o "Promedio_Notas" como respaldo
                    nota_val = sim.get("Puntaje_Simulacro", sim.get("Promedio_Notas", 0))
                    notas_sim.append(nota_val)
                    prom_uni += nota_val
                    cnt_uni += 1
                    
                    # Lo guardamos internamente como "UNI" para que la lógica de gráficos de abajo siga funcionando igual
                    tipos_sim.append("UNI")
                    
                    # Soporte flexible para la precisión
                    precision_val = sim.get("Precisión", sim.get("Promedio_Precision", 0))
                    prec_uni_total += precision_val
        
        if cnt_sem: prom_sem /= cnt_sem
        if cnt_uni: prom_uni /= cnt_uni
        prec_sem_prom = prec_sem_total / cnt_sem if cnt_sem > 0 else 0
        prec_uni_prom = prec_uni_total / cnt_uni if cnt_uni > 0 else 0

        col1, col2 = st.columns(2)
        with col1: 
            st.metric("🥇 Promedio Semanales", f"{prom_sem:.1f}")
            st.metric("🎯 Precisión", f"{int(prec_sem_prom)}%")
        with col2: 
            # Cambiamos la etiqueta a "Simulacros" para que coincida con tu nueva terminología
            st.metric("🏆 Promedio Simulacros", f"{prom_uni:.1f}")
            st.metric("🎯 Precisión", f"{int(prec_uni_prom)}%")
            
        if fechas_sim:
            fechas_sem = [f for f, t in zip(fechas_sim, tipos_sim) if t == "Semanal"]
            notas_sem = [n for n, t in zip(notas_sim, tipos_sim) if t == "Semanal"]
            fechas_uni = [f for f, t in zip(fechas_sim, tipos_sim) if t == "UNI"]
            notas_uni = [n for n, t in zip(notas_sim, tipos_sim) if t == "UNI"]
            
            fig_exam = go.Figure()
            # Línea de tendencia general
            fig_exam.add_trace(go.Scatter(x=fechas_sim, y=notas_sim, mode='lines', line=dict(color='green', width=2), showlegend=False))
            
            if fechas_sem:
                fig_exam.add_trace(go.Scatter(
                    x=fechas_sem, 
                    y=notas_sem, 
                    mode='markers', 
                    name='Semanal', 
                    marker=dict(size=10, color='blue', symbol='circle'), 
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Semanal: %{y:.1f}<extra></extra>'
                ))
            if fechas_uni:
                fig_exam.add_trace(go.Scatter(
                    x=fechas_uni, 
                    y=notas_uni, 
                    mode='markers', 
                    name='Simulacro', 
                    marker=dict(size=10, color='red', symbol='square'), 
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Simulacro: %{y:.1f}<extra></extra>'
                ))
            
            fig_exam.update_layout(
                yaxis_title='Nota (0-20)', 
                yaxis=dict(range=[0, 20]), 
                xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), 
                hovermode='closest', 
                height=400, 
                margin=dict(l=50, r=20, t=20, b=50)
            )
            st.plotly_chart(fig_exam, use_container_width=True)
        else:
            st.info("⚠️ Aún no hay datos de exámenes registrados.")

# ============================================
# VISTA: RENDIMIENTO POR CURSO (AISLADO Y DINÁMICO)
# ============================================
elif st.session_state.vista_actual == 'curso':
    st.header("📚 SECCIÓN: RENDIMIENTO POR CURSO")
    if st.button("⬅️ Volver al inicio", key="back_curso"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
    st.divider()
    
    # Obtenemos el user_id para un aislamiento limpio
    user_id = st.session_state.get('user_id', 'anonimo')
    
    datos = cargar_datos()
    config_actual = datos.get("config", {})
    
    # Forzamos la lectura de los cursos desde la sesión blindada o desde la base de datos
    key_lista_cursos = f"lista_cursos_config_{user_id}"
    if key_lista_cursos in st.session_state:
        catalogo_usuario = [c for c in st.session_state[key_lista_cursos] if c.get("nombre", "").strip()]
    else:
        catalogo_usuario = config_actual.get("catalogo_cursos", [])
        
    horario_usuario = config_actual.get("horario", {})
    
    if datos.get("diario"):
        st.subheader("📖 ESTADÍSTICAS POR CURSO")
        
        # 1. Fechas límite para calcular el "Universo de Días"
        primer_registro = min(datos["diario"], key=lambda x: x["fecha"])
        fecha_inicio_global = datetime.strptime(primer_registro["fecha"], "%Y-%m-%d")
        fecha_hoy = hora_peru()

        # 2. Generar los expanders de forma estrictamente dinámica sin fallback molesto
        if not catalogo_usuario:
            st.info("💡 No tienes cursos registrados en tu catálogo actual. Configúralos en la sección de Configuración.")
            mats_datos = []
        else:
            mats_datos = catalogo_usuario
        
        for i, curso_info in enumerate(mats_datos):
            mat = curso_info.get("nombre", "Curso")
            color_mat = curso_info.get("color", "#FF4500")  # Color guardado o naranja por defecto
            simbolo = "📖"
            
            with st.expander(f" {simbolo} {mat}", expanded=False):
                
                # --- CÁLCULO ESTRICTO ---
                fechas_mat = []
                disc_mat = []
                vel_mat = []
                horas_mat = []      
                ejercicios_mat = [] 
                temas_mat = []
                
                total_ejercicios = 0
                total_horas = 0
                dias_reales_estudiados = 0
                
                dia_actual = fecha_inicio_global
                while dia_actual.date() <= fecha_hoy.date():
                    dia_semana = dia_actual.weekday()
                    nombre_dia = NOMBRES_DIAS[dia_semana]
                    fecha_str = dia_actual.strftime("%Y-%m-%d")
                    
                    # Verificamos si el curso estaba programado para este día
                    materias_programadas_dia = horario_usuario.get(nombre_dia, [])
                    nombres_programados = [m["curso"] for m in materias_programadas_dia if m.get("curso")]
                    
                    # Buscamos si el usuario registró datos reales para este curso hoy
                    registro_dia = next((d for d in datos["diario"] if d["fecha"] == fecha_str), None)
                    tiene_registro_real = registro_dia and mat in registro_dia.get("materias", {})

                    # OPTIMIZACIÓN: Si estuvo programado O si el usuario de verdad lo estudió y registró ese día
                    if mat in nombres_programados or tiene_registro_real:
                        fechas_mat.append(dia_actual)
                        
                        if tiene_registro_real:
                            stats_mat = registro_dia["materias"][mat]
                            disc_mat.append(stats_mat["Disciplina"])
                            vel_mat.append(stats_mat["Velocidad"])
                            horas_mat.append(stats_mat.get("horas_estudiadas", 0))
                            ejercicios_mat.append(stats_mat.get("Ejercicios_Resueltos", 0))
                            temas_mat.append(stats_mat.get("Temas", "Sin tema"))
                            
                            total_ejercicios += stats_mat.get("Ejercicios_Resueltos", 0)
                            total_horas += stats_mat.get("horas_estudiadas", 0)
                            dias_reales_estudiados += 1
                        else:
                            # Estaba programado pero no se registró (Falta)
                            disc_mat.append(0)
                            vel_mat.append(0)
                            horas_mat.append(0)
                            ejercicios_mat.append(0)
                            temas_mat.append("-")
                            
                    dia_actual += timedelta(days=1)

                # --- MOSTRAR MÉTRICAS ---
                universo_dias = len(fechas_mat)
                
                if universo_dias > 0:
                    promedio_disc = sum(disc_mat) / universo_dias
                    promedio_vel = sum(vel_mat) / universo_dias
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"📅 Cumplimiento: {dias_reales_estudiados} de {universo_dias} días obligatorios")
                        st.write(f"📝 Ejercicios totales: {total_ejercicios}")
                        st.write(f"⏰ Horas totales: {int(total_horas)}h")
                    with c2:
                        st.write(f"🔥 Disciplina: {promedio_disc:.1f}%")
                        st.write(f"⚡ Velocidad: {promedio_vel:.1f} ejer/h")
                else:
                    st.info(f"Por el momento no hay registro programado de {mat}.")
                
                st.divider()
                
                # --- BOTÓN PARA VER GRÁFICOS ---
                estado_btn = f"ver_graficos_{mat}"
                if estado_btn not in st.session_state:
                    st.session_state[estado_btn] = False
                
                if st.button(f"📊 Ver gráficos de {mat}", key=f"btn_{mat}", use_container_width=True):
                    st.session_state[estado_btn] = not st.session_state[estado_btn]
                
                # --- DIBUJAR GRÁFICOS SI ESTÁ ACTIVO ---
                if st.session_state[estado_btn] and universo_dias > 0:

                    # 1. Creamos las pestañas aquí
                    tab_disc, tab_vel = st.tabs(["🔥 Disciplina", "⚡ Velocidad"])
                    
                    # Gráfico Disciplina
                    with tab_disc:
                        fig_disc = go.Figure()
                        fig_disc.add_trace(go.Scatter(
                            x=fechas_mat, y=disc_mat, mode='lines+markers', name='Disciplina',
                            line=dict(color=color_mat, width=3), marker=dict(size=8),
                            customdata=list(zip(horas_mat, temas_mat)),
                            hovertemplate='<b>%{x|%Y-%m-%d}</b><br><b>%{customdata[1]}</b><br>🔥%{y:.1f}%🔥<br> %{customdata[0]}h<extra></extra>'
                        ))
                        fig_disc.update_layout(title=f"🔥Disciplina - {mat}", yaxis_title="Disciplina (%)", yaxis=dict(range=[0, 150]), margin=dict(l=20, r=20, t=40, b=20), height=300)
                        st.plotly_chart(fig_disc, use_container_width=True, key=f"plot_disc_{mat}")
                    
                    # Gráfico Velocidad
                    with tab_vel:
                        fig_vel = go.Figure()
                        max_vel = max(vel_mat) if vel_mat else 10
                        fig_vel.add_trace(go.Scatter(
                            x=fechas_mat, y=vel_mat, mode='lines+markers', name='Velocidad',
                            line=dict(color=color_mat, width=3), marker=dict(size=8),
                            customdata=list(zip(ejercicios_mat, horas_mat, temas_mat)),
                            hovertemplate='<b>%{x|%Y-%m-%d}</b><br><b>%{customdata[2]}</b><br>⚡%{y:.1f} ejer/h⚡<br>%{customdata[0]} ejer en %{customdata[1]}h<extra></extra>'
                        ))
                        fig_vel.update_layout(title=f"⚡Velocidad - {mat}", yaxis_title="Ejercicios/h", yaxis=dict(range=[0, max(20, max_vel*1.2)]), margin=dict(l=20, r=20, t=40, b=20), height=300)
                        st.plotly_chart(fig_vel, use_container_width=True, key=f"plot_vel_{mat}")

        # ==========================================
        # GRÁFICOS COMPARATIVOS: LÍNEAS MÚLTIPLES
        # ==========================================
        st.divider()
        st.subheader("📈 COMPARACIÓN DE TODOS LOS CURSOS")
        
        fig_disc_global = go.Figure()
        fig_vel_global = go.Figure()
        
        # 1. Definimos los cursos a comparar a partir del catálogo dinámico
        mats_datos = catalogo_usuario if catalogo_usuario else CATALOGO_PREDETERMINADO
        
        for i, curso_info in enumerate(mats_datos):
            mat = curso_info.get("nombre", "Curso")
            color_mat = curso_info.get("color", "#FF4500")
            simbolo = "📖"  # Símbolo unificado y elegante
            
            fechas_mat = []
            disc_mat = []
            vel_mat = []
            horas_mat = []
            ejercicios_mat = []
            
            dia_actual = fecha_inicio_global
            while dia_actual.date() <= fecha_hoy.date():
                dia_semana = dia_actual.weekday()
                nombre_dia = NOMBRES_DIAS[dia_semana]
                fecha_str = dia_actual.strftime("%Y-%m-%d")
                
                # Verificamos si este curso estaba programado en el horario dinámico
                materias_programadas_dia = horario_usuario.get(nombre_dia, [])
                nombres_programados = [m["curso"] for m in materias_programadas_dia if m.get("curso")]
                
                # Buscamos si el usuario registró datos reales para este curso hoy
                registro_dia = next((d for d in datos["diario"] if d["fecha"] == fecha_str), None)
                tiene_registro_real = registro_dia and mat in registro_dia.get("materias", {})
                
                # OPTIMIZACIÓN: Si el curso estaba programado O si de verdad se registraron datos reales (Ej: Aritmética recién creado)
                if mat in nombres_programados or tiene_registro_real:
                    # Guardamos la fecha como string para que Plotly fuerce el renderizado del eje temporal correcto
                    fechas_mat.append(fecha_str)
                    
                    if tiene_registro_real:
                        stats_mat = registro_dia["materias"][mat]
                        disc_mat.append(stats_mat["Disciplina"])
                        vel_mat.append(stats_mat["Velocidad"])
                        horas_mat.append(stats_mat.get("horas_estudiadas", 0))
                        ejercicios_mat.append(stats_mat.get("Ejercicios_Resueltos", 0))
                    else:
                        # Estaba programado pero no se estudió (Falta de disciplina)
                        disc_mat.append(0)
                        vel_mat.append(0)
                        horas_mat.append(0)
                        ejercicios_mat.append(0)
                
                dia_actual += timedelta(days=1)
            
            # Solo graficamos si el curso tiene al menos un punto de registro o programación
            if fechas_mat:
                fig_disc_global.add_trace(go.Scatter(
                    x=fechas_mat, y=disc_mat, mode='lines+markers', name=f"{simbolo} {mat}",
                    line=dict(color=color_mat, width=2), marker=dict(size=6),
                    customdata=horas_mat,
                    hovertemplate='<b>%{x}</b><br>' + mat + '<br>🔥%{y:.1f}%🔥<br> %{customdata}h<extra></extra>'
                ))
                
                fig_vel_global.add_trace(go.Scatter(
                    x=fechas_mat, y=vel_mat, mode='lines+markers', name=f"{simbolo} {mat}",
                    line=dict(color=color_mat, width=2), marker=dict(size=6),
                    customdata=list(zip(ejercicios_mat, horas_mat)),
                    hovertemplate='<b>%{x}</b><br>' + mat + '<br>⚡%{y:.1f} ejer/h⚡<br>%{customdata[0]} ejer en %{customdata[1]}h<extra></extra>'
                ))

        # Determinar el rango de la velocidad dinámicamente
        max_vel_global = 20
        for trace in fig_vel_global.data:
            if trace.y:
                max_vel_global = max(max_vel_global, max(trace.y) * 1.2)

        # Configuramos los layouts obligando a Plotly a tratar el eje X como categoría temporal limpia
        fig_disc_global.update_layout(
            xaxis=dict(type='category', tickangle=45),
            yaxis_title="Disciplina (%)", yaxis=dict(range=[0, 150]), 
            hovermode='x', margin=dict(l=20, r=20, t=20, b=20), height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig_vel_global.update_layout(
            xaxis=dict(type='category', tickangle=45),
            yaxis_title="Velocidad (Ejercicios/h)", yaxis=dict(range=[0, max_vel_global]),
            hovermode='x', margin=dict(l=20, r=20, t=20, b=20), height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        tab1, tab2 = st.tabs(["🔥 Disciplina", "⚡ Velocidad"])
        with tab1:
            st.plotly_chart(fig_disc_global, use_container_width=True, key="plot_global_disc")
        with tab2:
            st.plotly_chart(fig_vel_global, use_container_width=True, key="plot_global_vel")


        # ==========================================
        # GRÁFICO GENERAL: EJERCICIOS VS HORAS
        # ==========================================
        st.divider()
        st.subheader("📊 EJERCICIOS Y HORAS EN TOTAL")
        
        # Inicializamos los diccionarios acumuladores de forma dinámica
        mats_nombres_dinamicos = [curso_info.get("nombre", "Curso") for curso_info in mats_datos]
        
        ej_tot = {m: 0 for m in mats_nombres_dinamicos}
        hr_tot = {m: 0 for m in mats_nombres_dinamicos}
        
        for dia in datos["diario"]:
            for m, s in dia.get("materias", {}).items():
                if m in ej_tot:
                    ej_tot[m] += s.get("Ejercicios_Resueltos", 0)
                    hr_tot[m] += s.get("horas_estudiadas", 0)
        
        etiquetas = [f"📖 {m}" for m in mats_nombres_dinamicos]
        
        fig_barras = go.Figure()
        fig_barras.add_trace(go.Bar(
            name='Ejercicios', 
            x=etiquetas, y=[ej_tot[m] for m in mats_nombres_dinamicos], 
            marker_color='#3498DB', hovertemplate='<b>%{x}</b><br>Ejercicios: %{y}<extra></extra>'
        ))
        
        fig_barras.add_trace(go.Bar(
            name='Horas', 
            x=etiquetas, y=[hr_tot[m] for m in mats_nombres_dinamicos], 
            marker_color='#E74C3C', hovertemplate='<b>%{x}</b><br>Horas: %{y:.1f}h<extra></extra>'
        ))
        
        max_y = max(max(ej_tot.values(), default=0), max(hr_tot.values(), default=0))
        
        fig_barras.update_layout(
            barmode='group', yaxis_title='Cantidad', yaxis=dict(range=[0, (max_y * 1.2) if max_y > 0 else 10]), 
            xaxis_title='Materia', height=500, margin=dict(l=50, r=20, t=20, b=50)
        )
        
        st.plotly_chart(fig_barras, use_container_width=True)
                    
    else:
        st.warning("⚠️ No hay materias registradas.")

    # ============================================
    # VISTA: REGISTRO
    # ============================================
elif st.session_state.vista_actual == 'registro':
    st.header("\U0001F4E5 REGISTRAR DATOS")
    if st.button("\u2B05\uFE0F Volver al inicio", key="back_registro"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
    st.divider()
    
    # Ya no necesitamos validación de contraseña porque tenemos login con Firebase
    # El usuario ya está autenticado desde el inicio

    st.divider()
    
    # ============================================
    # VERIFICAR REGISTROS DE HOY
    # ============================================
    datos = cargar_datos()
    config_actual = datos.get("config", {})
    horario_usuario = config_actual.get("horario", {})
    catalogo_usuario = config_actual.get("catalogo_cursos", [])
    
    fecha_hoy = fecha_hoy_peru()

    ya_registro_hoy = any(d["fecha"] == fecha_hoy for d in datos["diario"])
    examen_hoy = [e for e in datos["semanal"] if e["fecha"] == fecha_hoy]
    ya_registro_examen_hoy = len(examen_hoy) > 0
    
    # ============================================
    # REGISTRO DIARIO
    # ============================================
    st.subheader("📝 Registro Diario")
    
    if ya_registro_hoy:
        registro_hoy = next(d for d in datos["diario"] if d["fecha"] == fecha_hoy)
        st.success("✅ ¡Misión Diaria Completada!")
        st.info(f"Ya registraste tus datos de hoy. ¡Descansa y vuelve mañana! 🌙")
        st.divider()
        st.write(f"**📝 Ejercicios:** {registro_hoy['Total_Ejercicios_Resueltos_Dia']}")
        st.write(f"**⏰ Horas:** {int(registro_hoy['Total_Horas_Estudiadas'])}h")
    else:
        ds = hora_peru().weekday()
        nd = NOMBRES_DIAS[ds]
        
        # Obtener dinámicamente las materias configuradas para el día de hoy
        materias_programadas_dia = horario_usuario.get(nd, [])
        
        # Calculamos el total de horas disponibles sumando las horas asignadas de cada curso programado hoy
        hd = sum(float(m.get("horas", 0)) for m in materias_programadas_dia if m.get("horas"))
        
        # Ajustamos el mensaje informativo según la existencia de cursos reales
        if not catalogo_usuario:
            st.info("💡 **Aún no tienes cursos registrados en tu catálogo.** Ve a la sección de **Configuración del Ciclo** para registrar tus materias.")
        else:
            st.info(f"📅 Hoy es **{nd}**. Tienes **{hd:.1f} horas** totales programadas para estudiar.")
        
        reg_mat = {}
        tot_ej, tot_hr = 0, 0
        
        # Si no hay materias asignadas para hoy (o no hay catálogo)
        if not catalogo_usuario:
            st.warning("⚠️ Debes configurar al menos un curso en el catálogo para poder registrar datos diarios.")
        elif not materias_programadas_dia:
            st.warning("⚠️ No tienes cursos programados para estudiar el día de hoy en tu horario semanal.")
        else:
            for m_prog in materias_programadas_dia:
                m = m_prog.get("curso")
                if not m:
                    continue
                
                simbolo = "📖"  # El nuevo ícono unificado y elegante
                hd_m = float(m_prog.get("horas", 3))  # Obtenemos las horas programadas (por defecto 3 si no se guardó)
                
                st.markdown(f"### {simbolo} {m}")
                st.caption(f"⏱️ Horas programadas para este curso hoy: {int(hd_m)}h")
                c1, c2 = st.columns(2)
                with c1: 
                    h_in = st.number_input(f"Horas de estudio", min_value=0, max_value=24, value=0, step=1, key=f"h_{m}")
                with c2: 
                    e_in = st.number_input(f"Ejercicios resueltos", min_value=0, value=0, step=1, key=f"e_{m}")
                
                temas_in = st.text_input("Tema/s estudiado", placeholder="Ej: Vectores, Polinomios, Repaso", key=f"temas_{m}")
                
                disc = (h_in / hd_m) * 100 if hd_m > 0 else 0
                vel = e_in / h_in if h_in > 0 else 0
                
                reg_mat[m] = {
                    "horas_disponibles": hd_m, 
                    "horas_estudiadas": float(h_in), 
                    "Ejercicios_Resueltos": e_in, 
                    "Temas": temas_in, 
                    "Disciplina": round(disc, 2), 
                    "Velocidad": round(vel, 2)
                }
                tot_ej += e_in
                tot_hr += h_in
                st.divider()

            if materias_programadas_dia:
                if st.button("💾 Guardar Día", type="primary", use_container_width=True):
                    datos["diario"].append({
                        "fecha": fecha_hoy, 
                        "dia": nd, 
                        "hora_registro": hora_peru().strftime("%H:%M:%S"),                    
                        "horas_disponibles_total": hd, 
                        "materias": reg_mat,
                        "Total_Ejercicios_Resueltos_Dia": tot_ej, 
                        "Total_Horas_Estudiadas": tot_hr
                    })
                    guardar_datos(datos)
                    st.success(f"✅ ¡Día registrado! {tot_ej} ejercicios resueltos en {tot_hr}h.")
                    st.balloons()
                    st.rerun()

    st.divider()
    
    # ============================================
    # REGISTRO DE EXÁMENES (SOLO UNO POR DÍA)
    # ============================================
    st.subheader("📝 Registro de exámenes")
    
    # 1. Recuperamos de forma segura las preguntas totales desde config o usamos valores por defecto
    config_evals = config_actual.get("evaluaciones", {})
    preguntas_semanal_max = config_evals.get("preguntas_semanal", 60)
    # Aquí cambiamos el valor máximo predeterminado a 100 (formato estándar de simulacro)
    preguntas_simulacro_max = config_evals.get("preguntas_simulacro", 100)

    if ya_registro_examen_hoy:
        examen_registrado = examen_hoy[0]
        st.warning("⚠️ Ya registraste un examen hoy. Solo se permite un examen por día.")
        
        st.divider()
        st.subheader("📊 Examen registrado hoy:")
        
        # Adaptamos para mostrar la info del examen guardado de forma limpia
        tipo_reg = examen_registrado["tipo"]
        # Si es un simulacro guardado con el nuevo o viejo formato
        if tipo_reg in ["UNI", "Simulacro"]:
            nombre_mostrar = "Simulacro"
            # Soporte para el formato viejo (Promedio_Notas) y el nuevo (Puntaje_Simulacro)
            nota_reg = examen_registrado.get("Puntaje_Simulacro", examen_registrado.get("Promedio_Notas", "N/A"))
            prec_reg = examen_registrado.get("Precisión", examen_registrado.get("Promedio_Precision", "N/A"))
        else:
            nombre_mostrar = "Examen Semanal"
            nota_reg = examen_registrado["Puntaje_Simulacro"]
            prec_reg = examen_registrado.get("Precisión", "N/A")
            
        st.write(f"**Tipo:** 🥇 {nombre_mostrar}")
        st.write(f"**Puntaje / Nota:** {nota_reg}")
        st.write(f"**Precisión:** {prec_reg}%")

    else:
        # Selector de tipo de examen actualizado (Semanal vs Simulacro)
        tipo_examen = st.radio(
            "Tipo de examen:", 
            ["Semanal", "Simulacro"], 
            horizontal=True,
            format_func=lambda x: f"🥇 {x}" if x == "Semanal" else f"🏆 {x}"
        )
        
        if tipo_examen == "Semanal":
            c1, c2 = st.columns(2)
            with c1: 
                pj = st.number_input("Nota (0-20)", min_value=0.0, max_value=20.0, step=0.1)
            with c2: 
                co = st.number_input(f"Preguntas correctas (0-{preguntas_semanal_max})", min_value=0, max_value=preguntas_semanal_max, step=1)
            
            precision_calc = (co / preguntas_semanal_max) * 100 if preguntas_semanal_max > 0 else 0
            st.metric("🎯 Precisión", f"{precision_calc:.1f}%")
            
            if st.button("💾 Guardar Examen Semanal", type="primary"):
                datos["semanal"].append({
                    "fecha": fecha_hoy_peru(), 
                    "tipo": "Semanal", 
                    "Puntaje_Simulacro": pj, 
                    "Precisión": round(precision_calc, 2)
                })                    
                guardar_datos(datos)
                st.success("✅ Examen Semanal guardado.")
                st.balloons()
                
        else:  # Simulacro (Anteriormente UNI)
            st.subheader("🏆 Simulacro de Admisión")
            
            c1, c2 = st.columns(2)
            with c1: 
                pj = st.number_input("Nota (0-20)", min_value=0.0, max_value=20.0, step=0.1, key="nota_simulacro")
            with c2: 
                co = st.number_input(f"Preguntas correctas (0-{preguntas_simulacro_max})", min_value=0, max_value=preguntas_simulacro_max, step=1, key="corr_simulacro")
            
            precision_calc = (co / preguntas_simulacro_max) * 100 if preguntas_simulacro_max > 0 else 0
            st.metric("🎯 Precisión", f"{precision_calc:.1f}%")
            
            if st.button("💾 Guardar Simulacro", type="primary", use_container_width=True):
                # Mantener la consistencia con el contador de ejercicios resueltos
                ejercicios_semana = sum(d.get("Total_Ejercicios_Resueltos_Dia", 0) for d in datos.get("diario", [])[-7:])
                
                registro = {
                    "fecha": fecha_hoy_peru(), 
                    "tipo": "Simulacro", 
                    "Puntaje_Simulacro": pj, 
                    "Precisión": round(precision_calc, 2),
                    "Ejercicios_Resueltos_Semana": ejercicios_semana
                }
                datos["semanal"].append(registro)
                guardar_datos(datos)
                st.success(f"✅ ¡Simulacro registrado! Nota final: {pj:.2f}")
                st.balloons()

# ============================================
# VISTA: CONFIGURACIÓN DEL CICLO (REESTRUCTURADA Y CORREGIDA)
# ============================================
elif st.session_state.vista_actual == 'configuracion':
    st.header("⚙️ CONFIGURACIÓN DEL CICLO ACADÉMICO")

    if st.button("⬅️ Volver al inicio", key="back_config"):
        # 1. Guardamos en segundo plano automáticamente
        guardado_exitoso = guardar_datos_ciclo_automatico()
        
        # 2. Si guardó bien, redirigimos a la vista de inicio
        if guardado_exitoso:
            st.session_state.vista_actual = 'inicio'
            st.rerun()

    st.divider()
    
    datos = cargar_datos()
    config_actual = datos.get("config", {
        'universidad': 'UNI',
        'ciclo': 'Sin configurar',
        'materias': [],
        'horario': {}
    })

    # Creamos las tres pestañas solicitadas
    tab1, tab2, tab3 = st.tabs(["📅 Cronograma", "📚 Cursos", "📝 Exámenes"], key=f"tabs_configuracion_{st.session_state.get('user_id', 'anonimo')}")
    
    # Renderizamos los inputs asignándolos SIEMPRE a variables, controlando sus bloques con las pestañas correspondientes
    with tab1:
            st.subheader("📅 Cronograma del Ciclo")
            
            # 1. Selectores para construir el nombre del ciclo de forma dinámica
            col_tipo, col_meta = st.columns(2)
            with col_tipo:                  
                tipo_sel = st.text_input(
                    "Tipo de Preparación",
                    value=config_actual.get("tipo_preparacion", ""),
                    placeholder="Ej: Anual, Semestral, Repaso",
                    key="input_tipo_preparacion"
                )
                
            with col_meta:
                meta_guardada = config_actual.get("proceso_admision", "")
                meta_sel = st.text_input(
                    "Proceso de Admisión Objetivo",
                    value=meta_guardada,
                    placeholder="Ej: 2027-1, 2026-2",
                    key="input_proces_admision"
                )
                
            # Combinamos ambos para generar el nombre completo del ciclo
            nuevo_ciclo = f"{tipo_sel} {meta_sel}"
            nueva_uni = config_actual.get("universidad", "UNI") # Mantiene el destino actual
            
            st.divider()
            
            # 2. Configuración de Fechas Modificables
            st.markdown("#### ⏳ Duración del Ciclo")
            col_ini, col_fin = st.columns(2)
            
            # Convertir strings de Firebase a objetos date de Python de forma segura
            try:
                # 1. Intentamos leer con el formato de barras (el que usa el guardado automático)
                fecha_inicio_def = datetime.strptime(config_actual.get("fecha_inicio", "2026/07/17"), "%Y/%m/%d").date()
                fecha_fin_def = datetime.strptime(config_actual.get("fecha_fin", "2026/07/17"), "%Y/%m/%d").date()
            except Exception:
                try:
                    # 2. Respaldo por si hay registros antiguos con guiones
                    fecha_inicio_def = datetime.strptime(config_actual.get("fecha_inicio", "2026-07-17"), "%Y-%m-%d").date()
                    fecha_fin_def = datetime.strptime(config_actual.get("fecha_fin", "2026-07-17"), "%Y-%m-%d").date()
                except Exception:
                    # 3. Si no hay nada guardado, usa la fecha de hoy
                    fecha_inicio_def = hora_peru().date()
                    fecha_fin_def = hora_peru().date()
                
            with col_ini:
                f_inicio = st.date_input("Fecha de inicio del ciclo", value=fecha_inicio_def, key="input_fecha_inicio")
            with col_fin:
                f_fin = st.date_input("Fecha de finalización del ciclo", value=fecha_fin_def, key="input_fecha_fin")
                
            # 3. Validación de Ciclo Vencido (Aviso amistoso sin borrar datos)
            hoy_date = hora_peru().date()
            if hoy_date > f_fin:
                st.warning(
                    "⚠️ **Tu ciclo académico actual ha finalizado.**\n\n"
                    "Tus datos históricos y registros anteriores se mantendrán completamente intactos en tu panel. "
                    "Para iniciar una nueva etapa de estudio, actualiza los campos de arriba con los datos de tu siguiente ciclo "
                    "(por ejemplo, un ciclo Repaso o el nuevo Semestral) y guarda los cambios."
                )

    with tab2:
        # 1. DEFINICIÓN SEGURA DE VARIABLES Y PERSISTENCIA
        user_id = st.session_state.get('user_id', 'anonimo')
        key_lista_cursos = f"lista_cursos_config_{user_id}"
        
        # Intentamos obtener la configuración del usuario actual (config_actual)
        # Si no existe en el contexto, usamos 'datos' como respaldo
        if 'config_actual' in locals() or 'config_actual' in globals():
            catalogo_usuario_db = config_actual.get("catalogo_cursos", [])
        else:
            catalogo_usuario_db = datos.get("catalogo_cursos", [])   
        
        # Inicializamos la lista de la sesión si no existe
        if key_lista_cursos not in st.session_state:
            st.session_state[key_lista_cursos] = list(catalogo_usuario_db)
            
        # Sincronizamos la variable con el estado vivo de la sesión
        catalogo_usuario = st.session_state[key_lista_cursos]
                
        # 2. RENDERIZADO DE LA INTERFAZ DEL CATÁLOGO
        st.header("📚 Configuración del Catálogo de Cursos")
        
        # Inicializar el estado de edición en la sesión si no existe
        if "modo_edicion" not in st.session_state:
            st.session_state.modo_edicion = False

        # El botón de editar dinámico (Cambia de texto y color según el estado)
        texto_btn = "❌ Salir del modo edición" if st.session_state.modo_edicion else "✏️ Editar"
        tipo_btn = "secondary" if st.session_state.modo_edicion else "primary"
        
        if st.button(texto_btn, key="btn_modo_edicion", type=tipo_btn, use_container_width=False):
            st.session_state.modo_edicion = not st.session_state.modo_edicion
            st.rerun()

        # --- MODO LECTURA (Por defecto: Todo limpio) ---
        if not st.session_state.modo_edicion:
            
            # Vista simple de los cursos guardados en el catálogo
            if catalogo_usuario:
                st.write("### Tu Catálogo de Cursos Actual:")
                for curso in catalogo_usuario:
                    color = curso.get("color", "#FF4500")
                    nombre = curso.get("nombre", "Sin Nombre")
                    
                    # HTML limpio y unificado
                    html_curso = f'<div style="display: flex; align-items: center; margin-bottom: 8px;"><div style="width: 18px; height: 18px; background-color: {color}; border-radius: 4px; margin-right: 10px;"></div><span style="font-size: 16px; font-weight: 500;">📖 {nombre}</span></div>'
                    st.markdown(html_curso, unsafe_allow_html=True)
            else:
                st.warning("Aún no tienes cursos en tu catálogo. ¡Activa el modo edición para agregar uno!")

        # --- MODO EDICIÓN ACTIVO ---
        else:
            st.markdown("1. Registra aquí todas las materias que estudias en tu preparación y asígnales un color.")
            st.success("🛠️ **Modo Edición Activo**: Ahora puedes modificar tu catálogo.")
            
            # Formulario para agregar un nuevo curso
            st.write("### ➕ Añadir Nuevo Curso")
            c1, c2 = st.columns([4, 1])
            with c1:
                nuevo_curso_nombre = st.text_input("Nombre del Curso:", placeholder="Ej: Aritmética", key="nuevo_curso", label_visibility="collapsed")
            with c2:
                nuevo_curso_color = st.color_picker("Color:", "#2E8B57", key="nuevo_color", label_visibility="collapsed")
            
            col_add, col_spacer = st.columns([1, 2])
            with col_add:
                btn_añadir = st.button("＋ Añadir curso al catálogo", use_container_width=True)
                
            if btn_añadir:
                if nuevo_curso_nombre.strip():
                    existe = any(c["nombre"].lower() == nuevo_curso_nombre.strip().lower() for c in catalogo_usuario)
                    if not existe:
                        nuevo_elemento = {
                            "nombre": nuevo_curso_nombre.strip(),
                            "color": nuevo_curso_color
                        }
                        # 1. Guardar en memoria (RAM)
                        catalogo_usuario.append(nuevo_elemento)
                        st.session_state[key_lista_cursos] = catalogo_usuario
                        
                        # 2. Guardar físicamente tanto en 'config_actual' como en 'datos' para asegurar persistencia
                        if 'config_actual' in locals() or 'config_actual' in globals():
                            config_actual["catalogo_cursos"] = catalogo_usuario
                        datos["catalogo_cursos"] = catalogo_usuario
                        
                        guardar_datos(datos)
                        
                        st.session_state["mensaje_exito_adicion"] = f"¡{nuevo_curso_nombre} añadido al catálogo!"
                        st.rerun()
                    else:
                        st.error("Este curso ya está registrado en tu catálogo.")
                else:
                    st.warning("El nombre del curso no puede estar vacío.")

            if "mensaje_exito_adicion" in st.session_state:
                st.success(st.session_state["mensaje_exito_adicion"])
                del st.session_state["mensaje_exito_adicion"]

            st.divider()

            # Lista de cursos actuales con opción de eliminar
            st.write("### 📋 Administrar Cursos Existentes")
            if catalogo_usuario:
                for idx, curso in enumerate(catalogo_usuario):
                    nombre_curso = curso["nombre"]
                    color_curso = curso["color"]
                    
                    # Creamos un identificador único y limpio usando el nombre del curso
                    nombre_clean = nombre_curso.replace(" ", "_").lower()
                    key_btn_del = f"del_{nombre_clean}_{user_id}"
                    key_input_nom = f"nom_{nombre_clean}_{user_id}"
                    key_input_col = f"col_{nombre_clean}_{user_id}"
                    
                    col_nom, col_col, col_del = st.columns([4, 1, 1])
                    with col_nom:
                        st.text_input(f"Curso {idx+1}", value=nombre_curso, disabled=True, key=key_input_nom, label_visibility="collapsed")
                    with col_col:
                        st.color_picker(f"Color {idx+1}", value=color_curso, disabled=True, key=key_input_col, label_visibility="collapsed")
                    with col_del:
                        st.write("") 
                        # Usamos la clave única basada en el nombre del curso actual
                        btn_eliminar = st.button("❌", key=key_btn_del, help=f"Eliminar {nombre_curso}", use_container_width=True)
                        
                        if btn_eliminar:
                            # 1. Remover de memoria (RAM) usando la posición actual
                            catalogo_usuario.pop(idx)
                            st.session_state[key_lista_cursos] = catalogo_usuario
                            
                            # 2. Actualizar físicamente en base de datos
                            if 'config_actual' in locals() or 'config_actual' in globals():
                                config_actual["catalogo_cursos"] = catalogo_usuario
                            datos["catalogo_cursos"] = catalogo_usuario
                            
                            guardar_datos(datos)
                            st.rerun()
            else:
                st.info("No hay cursos para mostrar o eliminar.")

        # ============================================================
        # CRONOGRAMA SEMANAL (BLOQUES DESPLEGABLES POR DÍA)
        # ============================================================
        st.divider()
        st.subheader("🗓️ Distribución y Horas de Estudio Semanal")
        st.caption("2. Planifica qué cursos estudiarás cada día y cuántas horas les dedicarás a solas (sin contar clases).")

        # Filtramos los cursos de la sesión del usuario que tengan un nombre válido (no vacíos)
        cursos_validos = [c for c in st.session_state[key_lista_cursos] if c.get("nombre", "").strip()]
        lista_nombres_cursos = [c["nombre"] for c in cursos_validos]

        if not lista_nombres_cursos:
            st.info("💡 Registra al menos un curso en el catálogo de arriba para poder armar tu horario semanal.")
            horario_semanal_final = config_actual.get("horario", {})
        else:
            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            horario_semanal_final = {}
            horario_guardado = config_actual.get("horario", {})

            # Creamos una pestaña para cada día de la semana
            tabs = st.tabs(dias_semana)

            for idx_dia, dia in enumerate(dias_semana):
                # Renderizamos el contenido dentro de la pestaña correspondiente
                with tabs[idx_dia]:
                    st.write(f"#### 📅 Plan para el {dia}")
                    key_estado_dia = f"items_horario_{dia}_{user_id}"
                    
                    # Si no existe en session_state, lo inicializamos con lo que venga de la BD
                    if key_estado_dia not in st.session_state:
                        inicial_dia = horario_guardado.get(dia, [])
                        st.session_state[key_estado_dia] = [
                            item for item in inicial_dia if item.get("curso") in lista_nombres_cursos
                        ]

                    cursos_del_dia = []
                    
                    # Iteramos y renderizamos los cursos asignados a este día
                    if st.session_state[key_estado_dia]:
                        for h_idx, h_item in enumerate(st.session_state[key_estado_dia]):
                            col_del_h, col_cur_h, col_hrs_h = st.columns([0.5, 2, 1.5])
                            
                            with col_del_h:
                                if st.button("❌", key=f"del_h_{user_id}_{dia}_{h_idx}"):
                                    st.session_state[key_estado_dia].pop(h_idx)
                                    st.rerun()
                            
                            with col_cur_h:
                                curso_actual = h_item.get("curso")
                                idx_def = lista_nombres_cursos.index(curso_actual) if curso_actual in lista_nombres_cursos else 0
                                
                                # Cambiar de curso aquí es 100% seguro; no cerrará nada
                                curso_sel = st.selectbox(
                                    "Curso", 
                                    options=lista_nombres_cursos, 
                                    index=idx_def, 
                                    key=f"sel_h_{user_id}_{dia}_{h_idx}", 
                                    label_visibility="collapsed"
                                )
                                st.session_state[key_estado_dia][h_idx]["curso"] = curso_sel
                            
                            with col_hrs_h:
                                horas_sel = st.number_input(
                                    "Horas", 
                                    min_value=1, 
                                    max_value=16, 
                                    value=int(h_item.get("horas", 3)), 
                                    key=f"num_h_{user_id}_{dia}_{h_idx}", 
                                    label_visibility="collapsed"
                                )
                                st.session_state[key_estado_dia][h_idx]["horas"] = horas_sel
                            
                            cursos_del_dia.append({"curso": curso_sel, "horas": horas_sel})
                    else:
                        st.caption("No tienes cursos asignados para este día.")

                    st.write("") # Espaciador
                    if st.button(f"➕ Añadir curso a {dia}", key=f"btn_add_h_{user_id}_{dia}"):
                        st.session_state[key_estado_dia].append({"curso": lista_nombres_cursos[0], "horas": 3})
                        st.rerun()

                    horario_semanal_final[dia] = st.session_state[key_estado_dia]

        # Pasamos las variables limpias al ámbito general de la vista para el botón de guardado
        materias_seleccionadas = cursos_validos
        horario_configurado = horario_semanal_final

    with tab3:
        st.subheader("📝 Configuración de Exámenes")
        st.info("Configura la cantidad total de preguntas para tus evaluaciones semanales y simulacros generales.")
    
        # 1. Recuperamos de forma segura la configuración actual de evaluaciones
        config_evals = config_actual.get("evaluaciones", {})
        val_semanal = config_evals.get("preguntas_semanal", 60)
        val_simulacro = config_evals.get("preguntas_simulacro", 100)
    
        # 2. Creamos las dos sub-pestañas internas
        sub_tab1, sub_tab2 = st.tabs(["🥇 Examen Semanal", "🏆 Examen Simulacro"])
    
        with sub_tab1:
            st.write("### Ajustes del Examen Semanal")
            # Input numérico de enteros para las preguntas semanales
            preguntas_semanal = st.number_input(
                "Cantidad total de preguntas (Semanal):",
                min_value=1,
                max_value=200,
                value=int(val_semanal),
                step=1,
                key="input_preguntas_semanal"
            )
            st.caption("Esta cantidad definirá el límite superior al momento de registrar tus preguntas correctas en el examen semanal.")
    
        with sub_tab2:
            st.write("### Ajustes del Examen Simulacro")
            # Input numérico de enteros para las preguntas del simulacro
            preguntas_simulacro = st.number_input(
                "Cantidad total de preguntas (Simulacro):",
                min_value=1,
                max_value=200,
                value=int(val_simulacro),
                step=1,
                key="input_preguntas_simulacro"
            )
            st.caption("Esta cantidad definirá el límite superior al registrar tus preguntas correctas en los simulacros de admisión.")

    st.divider()

    # Botón de guardado unificado al final de las pestañas
    if st.button("💾 Guardar Cambios Generales", type="primary", key="btn_guardar_config"):
        # Llamamos a nuestra función unificada de guardado automático
        if guardar_datos_ciclo_automatico():
            # Activamos la bandera para pintar el cuadro verde y lanzar los globos
            st.session_state["mensaje_guardado"] = True
            st.rerun()

# ========================================================
# PUNTO #3: MOSTRAR EL MENSAJE SI LA BANDERA ES TRUE
# ========================================================
# Nota cómo este bloque está alineado al ras izquierdo (sin sangría del 'if st.button')
if st.session_state.get("mensaje_guardado", False):
    st.success("✅ Configuración actualizada con éxito.")
    st.balloons()
    # Apagamos la bandera para que desaparezca limpiamente en la próxima acción del usuario
    st.session_state["mensaje_guardado"] = False
