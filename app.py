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
    
    st.title("🎓 EDRA - Pre UNI")
    st.markdown("### Tu camino hacia la UNI empieza aquí")
    st.markdown("Estadísticas de rendimiento académico (EDRA) para postulantes a la Universidad Nacional de Ingeniería")
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
        st.session_state[cache_key] = {
            'diario': datos_a_guardar['diario'],
            'semanal': datos_a_guardar['semanal'],
            'materias': datos_a_guardar.get('materias', {})
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

st.title(f"🎓 EDRA de {usuario_actual} - {nombre_cycle_display}")

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
            
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📥 REGISTRAR DATOS", use_container_width=True, key="btn_registro"):
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
        
        # Generar lista completa de días desde el primer registro hasta hoy
        dias_completos = []
        dia_actual = fecha_inicio
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
                # Día NO registrado, crear registro ficticio con 0%
                dia_semana = dia_actual.weekday()
                nombre_dia = NOMBRES_DIAS[dia_semana]
                
                # OBTENER HORAS PROGRAMADAS DINÁMICAMENTE
                # Primero buscamos en su horario personalizado
                materias_dia = horario_usuario.get(nombre_dia, [])
                
                # Si no tiene nada asignado en su horario personalizado, usamos el respaldo temporal
                if not materias_dia:
                    materias_dia = HORARIO_PREDETERMINADO.get(nombre_dia, [])
                
                # Sumamos las horas de todos los cursos programados para ese día
                horas_disponibles = sum(int(m.get("horas", 0)) for m in materias_dia)
                
                # Si por alguna razón la suma da 0, le damos un mínimo de 1 para evitar divisiones por cero en tus métricas
                if horas_disponibles <= 0:
                    horas_disponibles = 4
                
                # Crear registro ficticio con 0 horas y 0 ejercicios
                registro_ficticio = {
                    "fecha": fecha_str,
                    "dia": nombre_dia,
                    "horas_disponibles_total": horas_disponibles,
                    "materias": {},
                    "Total_Ejercicios_Resueltos_Dia": 0,
                    "Total_Horas_Estudiadas": 0,
                    "es_ficticio": True  # Marcador para saber que es un día no registrado
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
            for sim in sorted(datos["semanal"], key=lambda x: x["fecha"]):
                f = datetime.strptime(sim["fecha"], "%Y-%m-%d")
                fechas_sim.append(f)
                if sim["tipo"] == "Semanal":
                    notas_sim.append(sim["Puntaje_Simulacro"])
                    prom_sem += sim["Puntaje_Simulacro"]
                    cnt_sem += 1
                    tipos_sim.append("Semanal")
                    if "Precisión" in sim: prec_sem_total += sim["Precisión"]
                else:
                    notas_sim.append(sim["Promedio_Notas"])
                    prom_uni += sim["Promedio_Notas"]
                    cnt_uni += 1
                    tipos_sim.append("UNI")
                    if "Promedio_Precision" in sim: prec_uni_total += sim["Promedio_Precision"]
        
        if cnt_sem: prom_sem /= cnt_sem
        if cnt_uni: prom_uni /= cnt_uni
        prec_sem_prom = prec_sem_total / cnt_sem if cnt_sem > 0 else 0
        prec_uni_prom = prec_uni_total / cnt_uni if cnt_uni > 0 else 0

        col1, col2 = st.columns(2)
        with col1: 
            st.metric("🥇 Promedio Semanales", f"{prom_sem:.1f}")
            st.metric("🎯 Precisión", f"{prec_sem_prom:.1f}%")
        with col2: 
            st.metric("🏆 Promedio Tipo UNI", f"{prom_uni:.1f}")
            st.metric("🎯 Precisión", f"{prec_uni_prom:.1f}%")
            
        if fechas_sim:
            fechas_sem = [f for f, t in zip(fechas_sim, tipos_sim) if t == "Semanal"]
            notas_sem = [n for n, t in zip(notas_sim, tipos_sim) if t == "Semanal"]
            fechas_uni = [f for f, t in zip(fechas_sim, tipos_sim) if t == "UNI"]
            notas_uni = [n for n, t in zip(notas_sim, tipos_sim) if t == "UNI"]
            
            fig_exam = go.Figure()
            fig_exam.add_trace(go.Scatter(x=fechas_sim, y=notas_sim, mode='lines', line=dict(color='green', width=2), showlegend=False))
            if fechas_sem:
                fig_exam.add_trace(go.Scatter(x=fechas_sem, y=notas_sem, mode='markers', name='Semanal', marker=dict(size=10, color='blue', symbol='circle'), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Semanal: %{y:.1f}<extra></extra>'))
            if fechas_uni:
                fig_exam.add_trace(go.Scatter(x=fechas_uni, y=notas_uni, mode='markers', name='Tipo UNI', marker=dict(size=10, color='red', symbol='square'), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>UNI: %{y:.1f}<extra></extra>'))
            
            fig_exam.update_layout(yaxis_title='Nota (0-20)', yaxis=dict(range=[0, 20]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='closest', height=400, margin=dict(l=50, r=20, t=20, b=50))
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
                
                # OPTIMIZACIÓN: Si el curso estaba programado O si de verdad se registraron datos reales (Ej: Biología recién creado)
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
                st.caption(f"⏱️ Horas programadas para este curso hoy: {hd_m}h")
                c1, c2 = st.columns(2)
                with c1: 
                    h_in = st.number_input(f"Horas reales dedicadas", min_value=0.0, max_value=24.0, value=0.0, step=0.5, key=f"h_{m}")
                with c2: 
                    e_in = st.number_input(f"Ejercicios resueltos", min_value=0, value=0, step=1, key=f"e_{m}")
                
                temas_in = st.text_input("Tema/s estudiado", placeholder="Ej: Vectores, Polinomios", key=f"temas_{m}")
                
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
    st.subheader("\U0001F4C4 Registro de exámenes")
    
    if ya_registro_examen_hoy:
        examen_registrado = examen_hoy[0]
        st.warning("\u26A0\uFE0F Ya registraste un examen hoy. Solo se permite un examen por día.")
        
        st.divider()
        st.subheader("\U0001F4CA Examen registrado hoy:")
        
        if examen_registrado["tipo"] == "Semanal":
            st.write(f"**Tipo:** \U0001F947 Examen Semanal")
            st.write(f"**Puntaje:** {examen_registrado['Puntaje_Simulacro']}")
            st.write(f"**Precisión:** {examen_registrado.get('Precisión', 'N/A')}%")
        else:
            st.write(f"**Tipo:** \U0001F3C6 Examen Tipo UNI")
            st.write(f"**Nota final:** {examen_registrado['Promedio_Notas']}")
            st.write(f"**Precisión:** {examen_registrado.get('Promedio_Precision', 'N/A')}%")
    else:
        # Selector con format_func para evitar problemas con emojis
        tipo_examen = st.radio(
            "Tipo de examen:", 
            ["Semanal", "UNI"], 
            horizontal=True,
            format_func=lambda x: f"\U0001F947 {x}" if x == "Semanal" else f"\U0001F3C6 {x}"
        )
        
        if tipo_examen == "Semanal":
            c1, c2 = st.columns(2)
            with c1: pj = st.number_input("Nota (0-20)", min_value=0.0, max_value=20.0, step=0.1)
            with c2: co = st.number_input("Preguntas correctas (0-60)", min_value=0, max_value=60, step=1)
            
            precision_calc = (co / 60) * 100
            st.metric("\U0001F3AF Precisión", f"{precision_calc:.1f}%")
            
            if st.button("\U0001F4BE Guardar Examen Semanal", type="primary"):
                datos["semanal"].append({"fecha": fecha_hoy_peru(), "tipo": "Semanal", "Puntaje_Simulacro": pj, "Precisión": round(precision_calc, 2)})                    
                guardar_datos(datos)
                st.success("\u2705 Examen Semanal guardado.")
                st.balloons()
        else:  # UNI
            st.subheader("\U0001F3C6 Examen Tipo UNI (3 días)")
            
            dias_uni = [
                {"nombre": "\U0001F310 Aptitud Académica y Humanidades", "preguntas": 100},
                {"nombre": "\U0001F522 Matemáticas", "preguntas": 40},
                {"nombre": "\U0001F9EA Ciencias", "preguntas": 40}
            ]
            
            dias_datos = []
            for i, dia_info in enumerate(dias_uni):
                with st.expander(f"\U0001F4C5 Día {i+1} - {dia_info['nombre']} ({dia_info['preguntas']} preguntas)", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        puntaje_dia = st.number_input("Nota", min_value=0.0, max_value=20.0, step=0.1, key=f"punti_dia_{i}")
                    with col2:
                        correctas_dia = st.number_input("Preguntas correctas", min_value=0, max_value=dia_info['preguntas'], step=1, key=f"corr_dia_{i}")
                    
                    precision_dia = (correctas_dia / dia_info['preguntas']) * 100 if dia_info['preguntas'] > 0 else 0
                    dias_datos.append({"dia": i+1, "nombre": dia_info['nombre'], "puntaje": puntaje_dia, "correctas": correctas_dia, "precision": round(precision_dia, 2)})
                    st.write(f"**\U0001F3AF Precisión:** {precision_dia:.1f}%")
            
            if dias_datos:
                prom_notas = sum(d["puntaje"] for d in dias_datos) / 3
                prom_precision = sum(d["precision"] for d in dias_datos) / 3
                
                st.divider()
                st.subheader("\U0001F4CA Resumen del Examen UNI")
                col1, col2 = st.columns(2)
                with col1: st.metric("\U0001F3C6 Nota final", f"{prom_notas:.2f}")
                with col2: st.metric("\U0001F3AF Precisión", f"{prom_precision:.1f}%")
                
                if st.button("\U0001F4BE Guardar Examen UNI", type="primary", use_container_width=True):
                    ejercicios_semana = sum(d["Total_Ejercicios_Resueltos_Dia"] for d in datos["diario"][-7:])
                    registro = {
                        "fecha": fecha_hoy, "tipo": "UNI", "dias": dias_datos,
                        "Promedio_Notas": round(prom_notas, 2), "Promedio_Precision": round(prom_precision, 2),
                        "Ejercicios_Resueltos_Semana": ejercicios_semana
                    }
                    datos["semanal"].append(registro)
                    guardar_datos(datos)
                    st.success(f"\u2705 ¡Examen UNI registrado! Nota final: {prom_notas:.2f}")
                    st.balloons()

# ============================================
# VISTA: CONFIGURACIÓN DEL CICLO (REESTRUCTURADA Y CORREGIDA)
# ============================================
elif st.session_state.vista_actual == 'configuracion':
    st.header("⚙️ CONFIGURACIÓN DEL CICLO ACADÉMICO")
    
    if st.button("⬅️ Volver al inicio", key="back_config"):
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
                tipos_ciclo = [
                    "Semestral básico (Semianual)",
                    "Semestral",
                    "Anual",
                    "Intensivo / Repaso"
                ]
                # Intentamos recuperar qué tipo estaba guardado antes
                tipo_guardado = config_actual.get("tipo_preparacion", "Semestral básico (Semianual)")
                if tipo_guardado not in tipos_ciclo:
                    tipo_guardado = tipos_ciclo[0]
                    
                tipo_sel = st.selectbox(
                    "Tipo de Preparación",
                    tipos_ciclo,
                    index=tipos_ciclo.index(tipo_guardado),
                    key="input_tipo_preparacion"
                )
                
            with col_meta:
                meta_guardada = config_actual.get("proceso_admision", "2027-1")
                meta_sel = st.text_input(
                    "Proceso de Admisión Objetivo",
                    value=meta_guardada,
                    placeholder="Ej: 2027-1, 2026-2",
                    key="input_proceso_admision"
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
                fecha_inicio_def = datetime.strptime(config_actual.get("fecha_inicio", fecha_hoy_peru()), "%Y-%m-%d").date()
                fecha_fin_def = datetime.strptime(config_actual.get("fecha_fin", fecha_hoy_peru()), "%Y-%m-%d").date()
            except Exception:
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
            st.subheader("📚 Configuración del Catálogo de Cursos")
            st.caption("1. Registra aquí todas las materias que estudias en tu preparación y asígnales un color.")
            
            # Recuperamos el ID del usuario actual para aislar la sesión
            user_id = st.session_state.get('user_id', 'anonimo')
            key_lista_cursos = f"lista_cursos_config_{user_id}"
            
            # Inicializamos la lista de cursos en la sesión del usuario si no existe
            if key_lista_cursos not in st.session_state:
                st.session_state[key_lista_cursos] = config_actual.get("catalogo_cursos", [])
    
            # Contenedor para mostrar la tabla dinámica de cursos y colores
            container_cursos = st.container()
            
            with container_cursos:
                col_eliminar, col_nombre_c, col_color_c = st.columns([0.5, 2, 1.5])
                with col_nombre_c:
                    st.markdown("**Curso:**")
                with col_color_c:
                    st.markdown("**Color asignado:**")
    
                # Iteramos usando la clave aislada por usuario
                for idx, item in enumerate(st.session_state[key_lista_cursos]):
                    c_eliminar, c_nombre, c_color = st.columns([0.5, 2, 1.5])
                    with c_eliminar:
                        if st.button("❌", key=f"del_curso_{user_id}_{idx}"):
                            st.session_state[key_lista_cursos].pop(idx)
                            st.rerun()
                    with c_nombre:
                        nombre_val = st.text_input(
                            "Nombre del curso", 
                            value=item.get("nombre", ""), 
                            key=f"nom_curso_{user_id}_{idx}", 
                            label_visibility="collapsed"
                        )
                        st.session_state[key_lista_cursos][idx]["nombre"] = nombre_val.strip()
                    with c_color:
                        color_val = st.color_picker(
                            "Elige un color", 
                            value=item.get("color", "#1F77B4"), 
                            key=f"col_curso_{user_id}_{idx}", 
                            label_visibility="collapsed"
                        )
                        st.session_state[key_lista_cursos][idx]["color"] = color_val
    
            if st.button("➕ Añadir curso al catálogo", key=f"btn_add_curso_row_{user_id}"):
                st.session_state[key_lista_cursos].append({"nombre": "", "color": "#2E7D32"})
                st.rerun()
    
            st.divider()
    
            # ============================================================
            # CRONOGRAMA SEMANAL (BLOQUES DESPLEGABLES POR DÍA)
            # ============================================================
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
    
                for dia in dias_semana:
                    with st.expander(f"🔽 {dia}", expanded=False):
                        # Clave del horario diaria también aislada por usuario
                        key_estado_dia = f"items_horario_{dia}_{user_id}"
                        if key_estado_dia not in st.session_state:
                            inicial_dia = horario_guardado.get(dia, [])
                            st.session_state[key_estado_dia] = [
                                item for item in inicial_dia if item.get("curso") in lista_nombres_cursos
                            ]
    
                        cursos_del_dia = []
                        for h_idx, h_item in enumerate(st.session_state[key_estado_dia]):
                            col_del_h, col_cur_h, col_hrs_h = st.columns([0.5, 2, 1.5])
                            
                            with col_del_h:
                                if st.button("❌", key=f"del_h_{user_id}_{dia}_{h_idx}"):
                                    st.session_state[key_estado_dia].pop(h_idx)
                                    st.rerun()
                            
                            with col_cur_h:
                                curso_actual = h_item.get("curso")
                                idx_def = lista_nombres_cursos.index(curso_actual) if curso_actual in lista_nombres_cursos else 0
                                
                                curso_sel = st.selectbox(
                                    "Curso", 
                                    options=lista_nombres_cursos, 
                                    index=idx_def, 
                                    key=f"sel_h_{user_id}_{dia}_{h_idx}", 
                                    label_visibility="collapsed"
                                )
                            
                            with col_hrs_h:
                                horas_sel = st.number_input(
                                    "Horas", 
                                    min_value=1, 
                                    max_value=16, 
                                    value=int(h_item.get("horas", 3)), 
                                    key=f"num_h_{user_id}_{dia}_{h_idx}", 
                                    label_visibility="collapsed"
                                )
                            
                            cursos_del_dia.append({"curso": curso_sel, "horas": horas_sel})
    
                        if st.button(f"➕ Añadir curso a {dia}", key=f"btn_add_h_{user_id}_{dia}"):
                            st.session_state[key_estado_dia].append({"curso": lista_nombres_cursos[0], "horas": 3})
                            st.rerun()
    
                        horario_semanal_final[dia] = cursos_del_dia
    
            # Pasamos las variables limpias al ámbito general de la vista para el botón de guardado
            materias_seleccionadas = cursos_validos
            horario_configurado = horario_semanal_final

    with tab3:
        st.subheader("📝 Configuración de Exámenes")
        st.info("Configuraciones específicas para tus simulacros (próximamente)")

    st.divider()

    # Botón de guardado unificado al final de las pestañas
    if st.button("💾 Guardar Cambios Generales", type="primary", key="btn_guardar_config"):
        user_id = st.session_state['user_id']
        
        # Reconstruimos el nombre del ciclo usando las selecciones de la pestaña 1
        nombre_ciclo_completo = f"{st.session_state.input_tipo_preparacion} {st.session_state.input_proceso_admision}"
        
        nueva_config = {
            'ciclo': nombre_ciclo_completo,
            'universidad': config_actual.get("universidad", "UNI"),
            'tipo_preparacion': st.session_state.input_tipo_preparacion,
            'proceso_admision': st.session_state.input_proceso_admision,
            'fecha_inicio': st.session_state.input_fecha_inicio.strftime("%Y-%m-%d"),
            'fecha_fin': st.session_state.input_fecha_fin.strftime("%Y-%m-%d"),
            'catalogo_cursos': materias_seleccionadas,
            'horario': horario_configurado
        }
        
        try:
            db.collection('usuarios').document(user_id).set({'config': nueva_config}, merge=True)
            datos["config"] = nueva_config
            st.session_state[f"cached_datos_{user_id}"] = datos
            st.success("✅ Configuración actualizada con éxito.")
            st.balloons()
        except Exception as e:
            st.error(f"Error al guardar: {e}")
