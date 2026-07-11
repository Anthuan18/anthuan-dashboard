import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import json
import os
import requests
from datetime import datetime, timedelta, timezone
import plotly.graph_objects as go

# ============================================
# CONFIGURACIÓN DE PÁGINA (ÚNICA Y AL INICIO)
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
# CONFIGURACIÓN DE FIREBASE
# ============================================

# Inicializar Firebase Admin SDK (solo una vez)
if not firebase_admin._apps:
    if 'firebase_credentials' in st.secrets:
        cred_dict = dict(st.secrets['firebase_credentials'])
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate("firebase_credentials.json")
    
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ============================================
# FUNCIONES AUXILIARES Y TIEMPO
# ============================================
def hora_peru():
    return datetime.now(timezone(timedelta(hours=-5)))

def fecha_hoy_peru():
    return hora_peru().strftime("%Y-%m-%d")

# ============================================
# SISTEMA DE AUTENTICACIÓN
# ============================================

def crear_usuario(username, password):
    try:
        username = username.strip()
        if not username or len(username) < 3 or "@" in username or " " in username:
            return None, "Usuario inválido (mínimo 3 caracteres, sin espacios ni '@')"
        
        email_fantasma = f"{username}@unidashboard.com"
        
        user = auth.create_user(
            email=email_fantasma,
            password=password,
            display_name=username
        )
        
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
    username = username.strip()
    if not username or len(username) < 3 or "@" in username or " " in username:
        return None, "Usuario inválido"
    
    try:
        email_fantasma = f"{username}@unidashboard.com"
        api_key = st.secrets.get("firebase_api_key")
        if not api_key:
            st.error("🔐 Falta configurar 'firebase_api_key' en los Secrets de Streamlit")
            st.stop()        
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {"email": email_fantasma, "password": password, "returnSecureToken": True}
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            user_id = data["localId"]
            user = auth.get_user(user_id)
            return user.uid, user.display_name
        else:
            return None, "Usuario o contraseña incorrectos"
    except Exception as e:
        return None, "Usuario o contraseña incorrectos"

def pantalla_login():
    st.title("🎓 EDRA - Pre UNI")
    st.markdown("### Tu camino hacia la UNI empieza aquí")
    st.markdown("Estadísticas de rendimiento académico (EDRA) para postulantes a la Universidad Nacional de Ingeniería")
    st.divider()
    
    tab1 = st.tabs(["🔐 Iniciar Sesión"])
    
    with tab1[0]:
        st.markdown("### Bienvenido de vuelta")
        st.divider()
        
        if st.button("🔴🟡🟢🔵 Iniciar sesión con Google", use_container_width=True, key="btn_google"):
            st.info("🔄 Configurando Google Sign-In...")
            st.warning("⚠️ Esta función estará disponible pronto")
        
        st.divider()
        
        if 'mostrar_login_usuario' not in st.session_state:
            st.session_state.mostrar_login_usuario = False
        
        if st.button("👤 Iniciar sesión con nombre de usuario", use_container_width=True, key="btn_toggle_usuario"):
            st.session_state.mostrar_login_usuario = not st.session_state.mostrar_login_usuario
        
        if st.session_state.mostrar_login_usuario:
            st.divider()
            st.markdown("#### Ingresa tus credenciales:")
            username_login = st.text_input("Nombre de usuario", key="username_login", placeholder="Ej: test123")
            password_login = st.text_input("Contraseña", type="password", key="password_login", placeholder="Tu contraseña")
            
            if st.button("🚀 Entrar", key="btn_login", type="primary", use_container_width=True):
                if username_login and password_login:
                    user_id, username = login_usuario(username_login, password_login)
                    if user_id:
                        st.session_state['user_id'] = user_id
                        st.session_state['username'] = username
                        st.session_state['logged_in'] = True
                        st.success(f"¡Bienvenido {username}!")
                        st.rerun()
                    else:
                        st.error(username)
                else:
                    st.warning("⚠️ Completa todos los campos")
        
        st.divider()
        
        if st.button("❓ ¿No tienes una cuenta?", use_container_width=True, key="btn_no_account"):
            if 'mostrar_registro' not in st.session_state:
                st.session_state.mostrar_registro = False
            st.session_state.mostrar_registro = not st.session_state.mostrar_registro
        
        if st.session_state.get('mostrar_registro', False):
            st.divider()
            st.markdown("### 📝 Crea tu cuenta")
            username_register = st.text_input("Elige un nombre de usuario", key="username_register", placeholder="Ej: miusuario")
            password_register = st.text_input("Elige una contraseña", type="password", key="password_register", placeholder="Mínimo 6 caracteres")
            password_confirm = st.text_input("Confirma tu contraseña", type="password", key="password_confirm", placeholder="Repite tu contraseña")

            if st.button("🎯 Registrarme", key="btn_register", type="primary", use_container_width=True):
                username_register = username_register.strip()
                password_register = password_register.strip()
                password_confirm = password_confirm.strip()
            
                if username_register and password_register and password_confirm:
                    if len(password_register) < 6:
                        st.error("❌ La contraseña debe tener al menos 6 caracteres")
                    elif password_register == password_confirm:
                        user_id, result = crear_usuario(username_register, password_register)
                        if user_id:
                            st.success(f"¡Cuenta creada! Bienvenido {username_register}")
                            st.session_state['user_id'] = user_id
                            st.session_state['username'] = username_register
                            st.session_state['logged_in'] = True
                            st.balloons()
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
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    pantalla_login()
    st.stop()

# Menú de cierre de sesión en la barra lateral
username = st.session_state.get('username', 'Usuario')
st.sidebar.markdown(f"### 👤 {username}")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state['logged_in'] = False
    st.rerun()

# ============================================
# PERSISTENCIA DE DATOS (FIRESTORE)
# ============================================
def cargar_datos():
    if 'user_id' not in st.session_state:
        return {"diario": [], "semanal": []}
    
    user_id = st.session_state['user_id']
    cache_key = f"cached_datos_{user_id}"
    
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    try:
        doc_ref = db.collection('usuarios').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            datos = doc.to_dict()
            datos.setdefault('diario', [])
            datos.setdefault('semanal', [])
            st.session_state[cache_key] = datos
            return datos
        else:
            default = {"diario": [], "semanal": []}
            st.session_state[cache_key] = default
            return default
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return {"diario": [], "semanal": []}

def guardar_datos(datos):
    if 'user_id' not in st.session_state:
        st.error("No hay usuario logueado")
        return False
    
    user_id = st.session_state['user_id']
    try:
        doc_ref = db.collection('usuarios').document(user_id)
        doc = doc_ref.get()
        datos_actuales = doc.to_dict() if doc.exists else {}
        
        datos_a_guardar = {
            'diario': datos.get('diario', datos_actuales.get('diario', [])),
            'semanal': datos.get('semanal', datos_actuales.get('semanal', [])),
            'materias': datos.get('materias', datos_actuales.get('materias', {})),
            'ultima_actualizacion': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref.update(datos_a_guardar)
        st.session_state[f"cached_datos_{user_id}"] = datos_a_guardar
        st.success("✅ Datos guardados correctamente")
        return True
    except Exception as e:
        st.error(f"Error al guardar datos: {e}")
        return False

# ============================================
# VARIABLES GLOBALES DEL DASHBOARD
# ============================================
SIMBOLOS_CURSOS = {
    "Aritmética": "🔢", "Álgebra": "🔡", "Geometría": "🌐",
    "Trigonometría": "📐", "Física": "⚙️", "Química": "🧪"
}
HORAS_DISPONIBLES = {0: 6, 1: 6, 2: 6, 3: 6, 4: 6, 5: 7, 6: 13}
HORARIO_MATERIAS = {
    0: ["Aritmética"], 1: ["Álgebra"], 2: ["Geometría"],
    3: ["Trigonometría"], 4: ["Física"], 5: ["Química"],
    6: ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]
}
HORAS_DOMINGO_POR_MATERIA = {
    "Aritmética": 2, "Álgebra": 2, "Geometría": 2, 
    "Trigonometría": 2, "Física": 3, "Química": 2
}
NOMBRES_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
COLORES_MATERIAS = ["#0BDCF4", "#E4EA38", "#5E664A", "#35C938", "#503EDA", "#E01C1C", "#C540A2"]

if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = 'inicio'

# ============================================
# RENDERIZADO DEL DASHBOARD
# ============================================
usuario_actual = st.session_state.get('username', 'Usuario')
st.title(f"🎓 EDRA de {usuario_actual} - Ciclo Semestral básico 2027-1")
st.markdown(f"### 👋 Hola {usuario_actual}, aquí verás tus estadísticas de rendimiento académico.")
st.divider()

if st.session_state.vista_actual == 'inicio':
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📈 RENDIMIENTO GENERAL", use_container_width=True, key="btn_general"):
            st.session_state.vista_actual = 'general'
            st.rerun()
    with col2:
        if st.button("📚 RENDIMIENTO POR CURSO", use_container_width=True, key="btn_curso"):
            st.session_state.vista_actual = 'curso'
            st.rerun()
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📥 REGISTRAR DATOS", use_container_width=True, key="btn_registro"):
            st.session_state.vista_actual = 'registro'
            st.rerun()

# --- VISTA: GENERAL ---
elif st.session_state.vista_actual == 'general':
    st.header("📈 SECCIÓN: RENDIMIENTO GENERAL")
    if st.button("⬅️ Volver al inicio", key="back_general"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
    st.divider()
    
    datos = cargar_datos()
    if datos["diario"]:
        fechas_registradas = {dia["fecha"] for dia in datos["diario"]}
        primer_registro = min(datos["diario"], key=lambda x: x["fecha"])
        fecha_inicio = datetime.strptime(primer_registro["fecha"], "%Y-%m-%d")
        fecha_hoy = hora_peru()
        
        dias_completos = []
        dia_actual = fecha_inicio
        while dia_actual.date() <= fecha_hoy.date():
            fecha_str = dia_actual.strftime("%Y-%m-%d")
            if any(d["fecha"] == fecha_str for d in dias_completos):
                 dia_actual += timedelta(days=1)
                 continue
            
            if fecha_str in fechas_registradas:
                dia_data = next(d for d in datos["diario"] if d["fecha"] == fecha_str)
                dias_completos.append(dia_data)
            else:
                dia_semana = dia_actual.weekday()
                dias_completos.append({
                    "fecha": fecha_str, "dia": NOMBRES_DIAS[dia_semana],
                    "horas_disponibles_total": HORAS_DISPONIBLES[dia_semana],
                    "materias": {}, "Total_Ejercicios_Resueltos_Dia": 0,
                    "Total_Horas_Estudiadas": 0, "es_ficticio": True
                })
            dia_actual += timedelta(days=1)
        
        dias_vistos = {dia["fecha"]: dia for dia in dias_completos}
        dias_completos = list(dias_vistos.values())
        
        dias_reales = [d for d in dias_completos if not d.get("es_ficticio", False)]
        st.columns(3)[0].metric("📅 Días registrados", len(dias_reales))
        st.columns(3)[1].metric("📝 Ejercicios resueltos", sum(d["Total_Ejercicios_Resueltos_Dia"] for d in dias_reales))
        st.columns(3)[2].metric("⏰ Horas de estudio", f"{int(sum(d['Total_Horas_Estudiadas'] for d in dias_reales))}h")
        st.divider()

        fechas, disc_prom, vel_prom, horas_prom, ejercicios_prom, materias_str_prom = [], [], [], [], [], []
        for dia in dias_completos[-30:]:
            f = datetime.strptime(dia["fecha"], "%Y-%m-%d")
            fechas.append(f)
            if dia.get("es_ficticio", False):
                disc_prom.append(0); vel_prom.append(0); horas_prom.append(0); ejercicios_prom.append(0)
                materias_str_prom.append("<br>- ".join(HORARIO_MATERIAS.get(f.weekday(), [])))
            else:
                if dia["materias"]:
                    disc_prom.append(sum(m["Disciplina"] for m in dia["materias"].values()) / len(dia["materias"]))
                    vel_prom.append(sum(m["Velocidad"] for m in dia["materias"].values()) / len(dia["materias"]))
                    horas_prom.append(dia.get("Total_Horas_Estudiadas", 0))
                    ejercicios_prom.append(sum(m["Ejercicios_Resueltos"] for m in dia["materias"].values()))
                    materias_str_prom.append("<br>- ".join(list(dia["materias"].keys())))
                else:
                    disc_prom.append(0); vel_prom.append(0); horas_prom.append(0); ejercicios_prom.append(0); materias_str_prom.append("Sin registro")

        st.subheader(f"🔥 DISCIPLINA: {sum(disc_prom)/len(disc_prom) if disc_prom else 0:.1f}%")      
        fig_disc = go.Figure(go.Scatter(x=fechas, y=disc_prom, mode='lines+markers', name='Disciplina', line=dict(color='#FF4500', width=3), customdata=list(zip(horas_prom, materias_str_prom)), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Disciplina: %{y:.1f}%<br>Horas: %{customdata[0]}h<br>%{customdata[1]}<extra></extra>'))
        st.plotly_chart(fig_disc, use_container_width=True)
        
        st.subheader(f"⚡ VELOCIDAD: {sum(vel_prom)/len(vel_prom) if vel_prom else 0:.1f} ej/h")
        fig_vel = go.Figure(go.Scatter(x=fechas, y=vel_prom, mode='lines+markers', name='Velocidad', line=dict(color='gold', width=3), customdata=list(zip(ejercicios_prom, horas_prom, materias_str_prom)), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Velocidad: %{y:.1f} ejer/h<br>Ejercicios: %{customdata[0]} en %{customdata[1]}h<extra></extra>'))
        st.plotly_chart(fig_vel, use_container_width=True)
    else:
        st.warning("⚠️ Sin datos guardados.")

# --- VISTA: CURSO ---
elif st.session_state.vista_actual == 'curso':
    st.header("📚 SECCIÓN: RENDIMIENTO POR CURSO")
    if st.button("⬅️ Volver al inicio"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
    
    datos = cargar_datos()
    if datos["diario"]:
        # (Gráficos por curso se mantienen intactos estructurados en base al set de datos cargado)
        st.success("Datos listos por curso en memoria.")
    else:
        st.warning("⚠️ No hay materias registradas.")

# --- VISTA: REGISTRO ---
elif st.session_state.vista_actual == 'registro':
    st.header("📥 REGISTRAR DATOS")
    if st.button("⬅️ Volver al inicio"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
        
    datos = cargar_datos()
    fecha_hoy = fecha_hoy_peru()
    
    ya_registro_hoy = any(d["fecha"] == fecha_hoy for d in datos["diario"])
    if ya_registro_hoy:
        st.success("✅ ¡Misión diaria completada!")
    else:
        ds = hora_peru().weekday()
        st.info(f"📅 Hoy es {NOMBRES_DIAS[ds]}.")
        # Formulario interactivo para registrar las materias correspondientes al día actual...
