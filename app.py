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
    """Muestra la pantalla de login con Google, usuario y registro integrado"""
    st.set_page_config(page_title="EDRA - Pre UNI", layout="wide")
    
    st.title("🎓 EDRA - Pre UNI")
    st.markdown("### Tu camino hacia la UNI empieza aquí")
    st.markdown("Estadísticas de rendimiento académico (EDRA) para postulantes a la Universidad Nacional de Ingeniería")
    st.divider()
    
    # Solo 1 tab: Iniciar Sesión
    tab1 = st.tabs(["🔐 Iniciar Sesión"])
    
    with tab1[0]:
        st.markdown("### Bienvenido de vuelta")
        st.divider()
        
        # ============================================
        # BOTÓN 1: Google Sign-In
        # ============================================
        if st.button("🔴🟡🟢🔵 Iniciar sesión con Google", 
                     use_container_width=True, 
                     key="btn_google",
                     type="secondary"):
            try:
                st.info("🔄 Configurando Google Sign-In...")
                st.warning("⚠️ Esta función estará disponible pronto")
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.divider()
        
        # ============================================
        # BOTÓN 2: Toggle para login con usuario
        # ============================================
        if 'mostrar_login_usuario' not in st.session_state:
            st.session_state.mostrar_login_usuario = False
        
        if st.button("👤 Iniciar sesión con nombre de usuario",
                     use_container_width=True,
                     key="btn_toggle_usuario",
                     type="secondary"):
            st.session_state.mostrar_login_usuario = not st.session_state.mostrar_login_usuario
        
        # ============================================
        # Formulario de login (aparece/desaparece)
        # ============================================
        if st.session_state.mostrar_login_usuario:
            st.divider()
            st.markdown("#### Ingresa tus credenciales:")
            
            username_login = st.text_input(
                "Nombre de usuario", 
                key="username_login",
                placeholder="Ej: test123"
            )
            password_login = st.text_input(
                "Contraseña", 
                type="password", 
                key="password_login",
                placeholder="Tu contraseña"
            )
            
            if st.button("🚀 Entrar", 
                         key="btn_login",
                         type="primary",
                         use_container_width=True):
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
        
        # ============================================
        # PREGUNTA: ¿No tienes una cuenta? (ROJO NEÓN)
        # ============================================
        st.markdown("""
            <style>
            .no-account-text {
                text-align: center;
                color: #FF3131 !important;
                font-weight: bold !important;
                font-size: 16px !important;
                cursor: pointer !important;
                text-decoration: underline !important;
                margin-top: 20px !important;
                margin-bottom: 10px !important;
            }
            .no-account-text:hover {
                color: #FF6666 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Botón/Link que muestra el formulario de registro
        if st.button("❓ ¿No tienes una cuenta?",
                     use_container_width=True,
                     key="btn_no_account",
                     type="secondary"):
            if 'mostrar_registro' not in st.session_state:
                st.session_state.mostrar_registro = False
            st.session_state.mostrar_registro = not st.session_state.mostrar_registro
        
        # ============================================
        # Formulario de registro (aparece/desaparece)
        # ============================================
        if 'mostrar_registro' not in st.session_state:
            st.session_state.mostrar_registro = False
        
        if st.session_state.mostrar_registro:
            st.divider()
            st.markdown("### 📝 Crea tu cuenta")
            
            username_register = st.text_input(
                "Elige un nombre de usuario", 
                key="username_register",
                placeholder="Ej: miusuario"
            )
            password_register = st.text_input(
                "Elige una contraseña", 
                type="password", 
                key="password_register",
                placeholder="Mínimo 6 caracteres"
            )
            password_confirm = st.text_input(
                "Confirma tu contraseña", 
                type="password", 
                key="password_confirm",
                placeholder="Repite tu contraseña"
            )

            if st.button("🎯 Registrarme", 
                         key="btn_register",
                         type="primary",
                         use_container_width=True):
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

# DICCIONARIO DE SÍMBOLOS - VERIFICAR QUE ESTÉN TODOS
SIMBOLOS_CURSOS = {
    "Aritmética": "\U0001F522",  # 🔢
    "Álgebra": "\U0001F521",     # 🔡
    "Geometría": "\U0001F310",   # 🌐
    "Trigonometría": "\U0001F4D0", # 📐
    "Física": "\u2699\uFE0F",    # ⚙️
    "Química": "\U0001F9EA"      # 🧪
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
ARCHIVO_GUARDADO = "anthuan_stats.json"

def cargar_datos():
    """Carga los datos del usuario actual desde Firestore (con cache en session_state)"""
    if 'user_id' not in st.session_state:
        return {"diario": [], "semanal": []}
    
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
            
            # Guardar en cache para próximas lecturas
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

# ============================================
# ENCABEZADO Y NAVEGACIÓN
# ============================================
# Obtener el nombre del usuario logueado
usuario_actual = st.session_state.get('username', 'Usuario')

st.title(f"🎓 EDRA de {usuario_actual} - Ciclo Semestral básico 2027-1")
st.markdown(f"### 👋 Hola {usuario_actual}, aquí verás tus estadísticas de rendimiento académico.")
st.divider()

if st.session_state.vista_actual == 'inicio':
    col1, col2 = st.columns(2)
    with col1:
        if st.button("\U0001F4C8 RENDIMIENTO GENERAL", use_container_width=True, key="btn_general"):
            st.session_state.vista_actual = 'general'
            st.rerun()
    with col2:
        if st.button("\U0001F4DA RENDIMIENTO POR CURSO", use_container_width=True, key="btn_curso"):
            st.session_state.vista_actual = 'curso'
            st.rerun()
    
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("\U0001F4E5 REGISTRAR DATOS", use_container_width=True, key="btn_registro"):
            st.session_state.vista_actual = 'registro'
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
                horas_disponibles = HORAS_DISPONIBLES[dia_semana]
                
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

        for dia in dias_unicos[-30:]:
        
            f = datetime.strptime(dia["fecha"], "%Y-%m-%d")
            fechas.append(f)
                        
            if dia.get("es_ficticio", False):
                # Día no registrado = 0% disciplina, 0 velocidad, 0 horas
                disc_prom.append(0)
                vel_prom.append(0)
                horas_prom.append(0)
                ejercicios_prom.append(0)
                
                # NUEVO: Obtener materias programadas para ese día
                dia_semana = f.weekday()  # 0=Lunes, 1=Martes... 6=Domingo
                materias_programadas = HORARIO_MATERIAS.get(dia_semana, [])
                
                if materias_programadas:
                    materias_str = "<br>- ".join(materias_programadas)
                    materias_str_prom.append(f"️ Día no registrado<br>Materias programadas:<br>- {materias_str}")
                else:
                    materias_str_prom.append("ℹ️ Día no registrado")
            else:
                # Día registrado, calcular valores reales
                if dia["materias"]:
                    disc_prom.append(sum(m["Disciplina"] for m in dia["materias"].values()) / len(dia["materias"]))
                    vel_prom.append(sum(m["Velocidad"] for m in dia["materias"].values()) / len(dia["materias"]))
                    horas_prom.append(dia.get("Total_Horas_Estudiadas", 0))
                    ejercicios_prom.append(sum(m["Ejercicios_Resueltos"] for m in dia["materias"].values()))

                    # NUEVO: Guardar nombres de las materias estudiadas
                    materias_list = list(dia["materias"].keys())
                    materias_str = "<br>- ".join(materias_list)
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
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Disciplina: %{y:.1f}%<br>Horas: %{customdata[0]}h<br>%{customdata[1]}<extra></extra>',
            customdata=list(zip(horas_prom, materias_str_prom))))        
        fig_disc.update_layout(yaxis_title='Disciplina (%)', yaxis=dict(range=[0, 150]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=400, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_disc, use_container_width=True)
        st.divider()

        promedio_vel = sum(vel_prom) / len(vel_prom) if vel_prom else 0
        st.subheader(f"⚡ VELOCIDAD: {promedio_vel:.1f} ejercicios/hora")
        fig_vel = go.Figure()
        if vel_prom:
            fig_vel.add_trace(go.Scatter(x=fechas, y=vel_prom, mode='lines+markers', name='Velocidad', 
                line=dict(color='gold', width=3), 
                marker=dict(size=8, color='gold'), 
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Velocidad: %{y:.1f} ejer/h<br>-Resolviste %{customdata[0]} ejer en %{customdata[1]}h<br>%{customdata[2]}<extra></extra>',
                customdata=list(zip(ejercicios_prom, horas_prom, materias_str_prom))))
            fig_vel.update_layout(yaxis_title='Velocidad (ejercicios/h)', yaxis=dict(range=[0, max(30, max(vel_prom)*1.2)]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=400, margin=dict(l=50, r=20, t=20, b=50))
            st.plotly_chart(fig_vel, use_container_width=True)
        else:
            st.warning("️ No hay datos de velocidad disponibles")

        # --- EXÁMENES ---
        st.subheader("\U0001F4C4 EXÁMENES")
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
            st.metric("\U0001F947 Promedio Semanales", f"{prom_sem:.1f}")
            st.metric("\U0001F3AF Precisión", f"{prec_sem_prom:.1f}%")
        with col2: 
            st.metric("\U0001F3C6 Promedio Tipo UNI", f"{prom_uni:.1f}")
            st.metric("\U0001F3AF Precisión", f"{prec_uni_prom:.1f}%")
            
        if fechas_sim:
            fechas_sem = [f for f, t in zip(fechas_sim, tipos_sim) if t == "Semanal"]
            notas_sem = [n for n, t in zip(notas_sim, tipos_sim) if t == "Semanal"]
            fechas_uni = [f for f, t in zip(fechas_sim, tipos_sim) if t == "UNI"]
            notas_uni = [n for n, t in zip(notas_sim, tipos_sim) if t == "UNI"]
            
            fig_exam = go.Figure()
            fig_exam.add_trace(go.Scatter(x=fechas_sim, y=notas_sim, mode='lines', name='Tendencia', line=dict(color='green', width=2), showlegend=False))
            if fechas_sem:
                fig_exam.add_trace(go.Scatter(x=fechas_sem, y=notas_sem, mode='markers', name='Semanal', marker=dict(size=10, color='blue', symbol='circle'), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Semanal: %{y:.1f}<extra></extra>'))
            if fechas_uni:
                fig_exam.add_trace(go.Scatter(x=fechas_uni, y=notas_uni, mode='markers', name='Tipo UNI', marker=dict(size=10, color='red', symbol='square'), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>UNI: %{y:.1f}<extra></extra>'))
            
            fig_exam.update_layout(yaxis_title='Nota (0-20)', yaxis=dict(range=[0, 20]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=400, margin=dict(l=50, r=20, t=20, b=50))
            st.plotly_chart(fig_exam, use_container_width=True)
        else:
            st.info("\u26A0\uFE0F Aún no hay datos de exámenes registrados.")
    else:
        st.warning("\u26A0\uFE0F Aún no hay datos registrados.")

# ============================================
# VISTA: RENDIMIENTO POR CURSO
# ============================================
elif st.session_state.vista_actual == 'curso':
    st.header("\U0001F4DA SECCIÓN: RENDIMIENTO POR CURSO")
    if st.button("\u2B05\uFE0F Volver al inicio", key="back_curso"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
    st.divider()
    
    datos = cargar_datos()
    
    if datos["diario"]:
        st.subheader("\U0001F4D6 ESTADÍSTICAS")
        materias_stats = {}
        for dia in datos["diario"]:
            for mat, stats in dia["materias"].items():
                if mat not in materias_stats:
                    materias_stats[mat] = {"dias": 0, "ejercicios": 0, "horas": 0, "disc": [], "vel": []}
                materias_stats[mat]["dias"] += 1
                materias_stats[mat]["ejercicios"] += stats["Ejercicios_Resueltos"]
                materias_stats[mat]["horas"] += stats["horas_estudiadas"]
                materias_stats[mat]["disc"].append(stats["Disciplina"])
                materias_stats[mat]["vel"].append(stats["Velocidad"])

        # DEFINIR mats ANTES del loop
        mats = ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]
        
        for mat, s in materias_stats.items():
            simbolo = SIMBOLOS_CURSOS.get(mat, "\U0001F4DA")
            with st.expander(f"\u25BC {simbolo} {mat}", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"\U0001F4C5 Días estudiados: {s['dias']}")
                    st.write(f"\U0001F4DD Ejercicios totales: {s['ejercicios']}")
                    st.write(f"\u23F0 Horas totales: {int(s['horas'])}h")
                with c2:
                    st.write(f"\U0001F525 Disciplina: {sum(s['disc'])/len(s['disc']):.1f}%")
                    st.write(f"\u26A1 VELOCIDAD: {sum(s['vel'])/len(s['vel']):.1f} ejercicios/h")
                
                # BOTÓN PARA VER GRÁFICOS
                if st.button(f" Ver gráficos de {mat}", key=f"btn_graf_{mat}", use_container_width=True):
                    st.divider()
                    st.markdown(f"###  Evolución de {simbolo} {mat}")
                    
                    datos_mat = []
                    for dia in sorted(datos["diario"], key=lambda x: x["fecha"]):
                        if mat in dia["materias"]:
                            datos_mat.append({
                                "fecha": datetime.strptime(dia["fecha"], "%Y-%m-%d"),
                                "disciplina": dia["materias"][mat]["Disciplina"],
                                "velocidad": dia["materias"][mat]["Velocidad"],
                                "horas": dia["materias"][mat].get("horas_estudiadas", 0),
                                "ejercicios": dia["materias"][mat].get("Ejercicios_Resueltos", 0)
                            })
                    
                    if datos_mat:
                        fechas = [d["fecha"] for d in datos_mat]
                        disciplinas = [d["disciplina"] for d in datos_mat]
                        velocidades = [d["velocidad"] for d in datos_mat]
                        horas = [d["horas"] for d in datos_mat]
                        ejercicios = [d["ejercicios"] for d in datos_mat]
                        
                        color_idx = mats.index(mat) if mat in mats else 0
                        color_mat = COLORES_MATERIAS[color_idx]
                        
                        # GRÁFICO 1: DISCIPLINA
                        fig_disc = go.Figure()
                        fig_disc.add_trace(go.Scatter(
                            x=fechas, y=disciplinas, mode='lines+markers',
                            name='Disciplina',
                            line=dict(color=color_mat, width=3),
                            marker=dict(size=8),
                            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Disciplina: %{y:.1f}%<br>Horas: %{customdata}h<extra></extra>',
                            customdata=horas
                        ))
                        fig_disc.update_layout(
                            yaxis_title='Disciplina (%)', 
                            yaxis=dict(range=[0, 150]), 
                            xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), 
                            hovermode='x unified', 
                            height=350, margin=dict(l=50, r=20, t=20, b=50)
                        )
                        st.plotly_chart(fig_disc, use_container_width=True)
                        
                        # GRÁFICO 2: VELOCIDAD
                        max_vel = max(velocidades) if velocidades else 30
                        fig_vel = go.Figure()
                        fig_vel.add_trace(go.Scatter(
                            x=fechas, y=velocidades, mode='lines+markers',
                            name='Velocidad',
                            line=dict(color='gold', width=3),
                            marker=dict(size=8),
                            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Velocidad: %{y:.1f} ejer/h<br>Ejercicios: %{customdata[0]}<br>Horas: %{customdata[1]}h<extra></extra>',
                            customdata=list(zip(ejercicios, horas))
                        ))
                        fig_vel.update_layout(
                            yaxis_title='Velocidad (ejercicios/h)', 
                            yaxis=dict(range=[0, max(30, max_vel*1.2)]), 
                            xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), 
                            hovermode='x unified', 
                            height=350, margin=dict(l=50, r=20, t=20, b=50)
                        )
                        st.plotly_chart(fig_vel, use_container_width=True)
                    else:
                        st.warning("⚠️ No hay datos para mostrar gráficos.")
        st.divider()

        mats = ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]
        f_det, d_mat, v_mat, h_mat, e_mat = [], {m:[] for m in mats}, {m:[] for m in mats}, {m:[] for m in mats}, {m:[] for m in mats}
        for dia in datos["diario"][-30:]:
            if dia["dia"] != "Domingo":
                f_det.append(datetime.strptime(dia["fecha"], "%Y-%m-%d"))
                for m in mats:
                    if m in dia["materias"]:
                        d_mat[m].append(dia["materias"][m]["Disciplina"])
                        v_mat[m].append(dia["materias"][m]["Velocidad"])
                        h_mat[m].append(dia["materias"][m].get("horas_estudiadas", 0))
                        e_mat[m].append(dia["materias"][m].get("Ejercicios_Resueltos", 0))
                    else:
                        d_mat[m].append(None)
                        v_mat[m].append(None)
                        h_mat[m].append(None)
                        e_mat[m].append(None)

        st.subheader("\U0001F525 DISCIPLINA")
        fig_disc_mat = go.Figure()
        for i, m in enumerate(mats):
            val = [(f, d) for f, d in zip(f_det, d_mat[m]) if d is not None]
            if val:
                ff, dd = zip(*val)
                # Filtrar horas para que coincidan con ff y dd
                hh = [h for f, h in zip(f_det, h_mat[m]) if h is not None]
        
                fig_disc_mat.add_trace(go.Scatter(x=ff, y=dd, mode='lines+markers', name=f'{SIMBOLOS_CURSOS[m]} {m}',
                    line=dict(color=COLORES_MATERIAS[i], width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Disciplina: %{y:.1f}%<br>Horas: %{customdata}h<extra></extra>',
                    customdata=hh))                          
         
        fig_disc_mat.update_layout(yaxis_title='Disciplina (%)', yaxis=dict(range=[0, 150]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=500, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_disc_mat, use_container_width=True)
        st.divider()

        st.subheader("\u26A1 VELOCIDAD")
        fig_vel_mat = go.Figure()
        for i, m in enumerate(mats):
            val = [(f, v) for f, v in zip(f_det, v_mat[m]) if v is not None]
            if val:
                ff, vv = zip(*val)
                # Filtrar horas y ejercicios para que coincidan
                hh = [h for f, h in zip(f_det, h_mat[m]) if h is not None]
                ee = [e for f, e in zip(f_det, e_mat[m]) if e is not None]
                
                fig_vel_mat.add_trace(go.Scatter(x=ff, y=vv, mode='lines+markers', name=f'{SIMBOLOS_CURSOS[m]} {m}', 
                    line=dict(color=COLORES_MATERIAS[i], width=2), 
                    marker=dict(size=6), 
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' + m + ': %{y:.1f} ejer/h<br>-Resolviste %{customdata[0]} ejer en %{customdata[1]}h<extra></extra>',
                    customdata=list(zip(ee, hh))))
        fig_vel_mat.update_layout(yaxis_title='Velocidad (ejercicios/h)', yaxis=dict(range=[0, max(30, max([v for v in sum(v_mat.values(), []) if v is not None])*1.2)]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=500, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_vel_mat, use_container_width=True)
        st.divider()

        st.subheader("\U0001F4CA EJERCICIOS VS HORAS")
        ej_tot = {m:0 for m in mats}
        hr_tot = {m:0 for m in mats}
        for dia in datos["diario"]:
            for m, s in dia["materias"].items():
                if m in ej_tot:
                    ej_tot[m] += s["Ejercicios_Resueltos"]
                    hr_tot[m] += s["horas_estudiadas"]
        
        etiquetas = [f"{SIMBOLOS_CURSOS[m]} {m}" for m in mats]
        fig_barras = go.Figure()
        fig_barras.add_trace(go.Bar(name='Ejercicios', x=etiquetas, y=[ej_tot[m] for m in mats], marker_color='#3498DB', hovertemplate='<b>%{x}</b><br>Ejercicios: %{y}<extra></extra>'))
        fig_barras.add_trace(go.Bar(name='Horas', x=etiquetas, y=[hr_tot[m] for m in mats], marker_color='#E74C3C', hovertemplate='<b>%{x}</b><br>Horas: %{y:.1f}h<extra></extra>'))
        fig_barras.update_layout(barmode='group', yaxis_title='Cantidad', yaxis=dict(range=[0, max(max(ej_tot.values()), max(hr_tot.values()))*1.2]), xaxis_title='Materia', height=500, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_barras, use_container_width=True)
    else:
        st.warning("\u26A0\uFE0F No hay datos de materias registrados.")

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
    fecha_hoy = fecha_hoy_peru()

    ya_registro_hoy = any(d["fecha"] == fecha_hoy for d in datos["diario"])
    examen_hoy = [e for e in datos["semanal"] if e["fecha"] == fecha_hoy]
    ya_registro_examen_hoy = len(examen_hoy) > 0
    
    # ============================================
    # REGISTRO DIARIO
    # ============================================
    st.subheader("\U0001F4DD Registro Diario")
    
    if ya_registro_hoy:
        registro_hoy = next(d for d in datos["diario"] if d["fecha"] == fecha_hoy)
        st.success("\u2705 ¡Misión Diaria Completada!")
        st.info(f"Ya registraste tus datos de hoy. ¡Descansa y vuelve mañana! \U0001F319")
        st.divider()
        st.write(f"**\U0001F4DD Ejercicios:** {registro_hoy['Total_Ejercicios_Resueltos_Dia']}")
        st.write(f"**\u23F0 Horas:** {int(registro_hoy['Total_Horas_Estudiadas'])}h")
    else:
        ds = hora_peru().weekday()
        nd = NOMBRES_DIAS[ds]
        hd = HORAS_DISPONIBLES[ds]
        mats = HORARIO_MATERIAS[ds]
        st.info(f"\U0001F4C5 Hoy es **{nd}**. Tienes **{hd} horas** disponibles.")
        
        reg_mat = {}
        tot_ej, tot_hr = 0, 0
        
        for m in mats:
            simbolo = SIMBOLOS_CURSOS.get(m, "\U0001F4DA")
            hd_m = HORAS_DOMINGO_POR_MATERIA[m] if ds == 6 else hd
            st.markdown(f"### {simbolo} {m}")
            c1, c2 = st.columns(2)
            with c1: h_in = st.number_input(f"Horas", min_value=0, value=0, step=1, key=f"h_{m}")
            with c2: e_in = st.number_input(f"Ejercicios", min_value=0, value=0, step=1, key=f"e_{m}")
            
            disc = (h_in / hd_m) * 100 if hd_m > 0 else 0
            vel = e_in / h_in if h_in > 0 else 0
            reg_mat[m] = {"horas_disponibles": hd_m, "horas_estudiadas": float(h_in), "Ejercicios_Resueltos": e_in, "Disciplina": round(disc, 2), "Velocidad": round(vel, 2)}
            tot_ej += e_in; tot_hr += h_in
            st.divider()

        if st.button("\U0001F4BE Guardar Día", type="primary", use_container_width=True):
            datos["diario"].append({
                "fecha": fecha_hoy, "dia": nd, "hora_registro": hora_peru().strftime("%H:%M:%S"),                    
                "horas_disponibles_total": hd, "materias": reg_mat,
                "Total_Ejercicios_Resueltos_Dia": tot_ej, "Total_Horas_Estudiadas": tot_hr
            })
            guardar_datos(datos)
            st.success(f"\u2705 ¡Día registrado! {tot_ej} ejercicios.")
            st.balloons()

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
