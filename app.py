import streamlit as st
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================
st.set_page_config(
    page_title="Dashboard de Anthuan", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="collapsed" # Oculta el menú lateral por defecto
)

# CSS Personalizado para ocultar la flecha (>>) y estilizar botones
st.markdown("""
<style>
    /* Ocultar botón de colapsar sidebar (>>) */
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    
    /* Ocultar el sidebar completamente si está vacío */
    .css-1d391kg, .css-1lcbmhc {
        display: none;
    }

    /* Estilos para los botones grandes de navegación */
    .nav-button {
        display: block;
        width: 100%;
        padding: 25px;
        font-size: 22px;
        font-weight: bold;
        text-align: center;
        text-decoration: none;
        color: white !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    .nav-button:hover {
        transform: scale(1.02);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    .nav-button-general {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .nav-button-curso {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    /* Ocultar el menú de Streamlit (hamburguesa) si se desea */
    /* button[kind="header"] { display: none; } */
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURACIÓN DEL HORARIO Y DATOS
# ============================================
CONTRASEÑA_REGISTRO = "anthuan2027" # ¡Cámbiala por la que quieras!

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
    if os.path.exists(ARCHIVO_GUARDADO):
        with open(ARCHIVO_GUARDADO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"diario": [], "semanal": []}

def guardar_datos(datos):
    with open(ARCHIVO_GUARDADO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# ============================================
# ENCABEZADO Y BIENVENIDA
# ============================================
st.title("📚 Estadísticas de Anthuan: Ciclo Semianual 2027-1")
st.markdown("### 👋 Hola, aquí verás mis estadísticas de rendimiento académico.")
st.divider()

# ============================================
# BOTONES DE NAVEGACIÓN
# ============================================
col1, col2 = st.columns(2)
with col1:
    st.markdown('<a href="#rendimiento-general" target="_self" class="nav-button nav-button-general">📈 RENDIMIENTO GENERAL</a>', unsafe_allow_html=True)
with col2:
    st.markdown('<a href="#rendimiento-curso" target="_self" class="nav-button nav-button-curso">📚 RENDIMIENTO POR CURSO</a>', unsafe_allow_html=True)

st.divider()

# Cargar datos una sola vez
datos = cargar_datos()

# ============================================
# SECCIÓN 1: RENDIMIENTO GENERAL
# ============================================
st.markdown('<div id="rendimiento-general"></div>', unsafe_allow_html=True)
st.header("📈 SECCIÓN: RENDIMIENTO GENERAL")
st.divider()

if datos["diario"]:
    # --- MÉTRICAS BÁSICAS ---
    total_dias = len(datos["diario"])
    total_ejercicios = sum(d["Total_Ejercicios_Resueltos_Dia"] for d in datos["diario"])
    total_horas = sum(d["Total_Horas_Estudiadas"] for d in datos["diario"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Días registrados", total_dias)
    with col2:
        st.metric("📚 Ejercicios resueltos", total_ejercicios)
    with col3:
        st.metric("⏰ Horas de estudio", f"{total_horas:.1f}h")
    
    st.divider()

    # Preparar datos para gráficos generales
    fechas = []
    disciplinas_promedio = []
    velocidades_promedio = []
    
    for dia in datos["diario"][-30:]:
        fechas.append(datetime.strptime(dia["fecha"], "%Y-%m-%d"))
        disc_vals = [m["Disciplina"] for m in dia["materias"].values()]
        vel_vals = [m["Velocidad"] for m in dia["materias"].values()]
        disciplinas_promedio.append(sum(disc_vals) / len(disc_vals) if disc_vals else 0)
        velocidades_promedio.append(sum(vel_vals) / len(vel_vals) if vel_vals else 0)

    # --- DISCIPLINA ---
    disc_final = disciplinas_promedio[-1] if disciplinas_promedio else 0
    st.subheader(f"🔥 DISCIPLINA: {disc_final:.1f}%")
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(fechas, disciplinas_promedio, color='red', linewidth=3, marker='o', markersize=8)
    ax.set_ylabel('Disciplina (%)', color='red', fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    st.divider()

    # --- VELOCIDAD ---
    vel_final = velocidades_promedio[-1] if velocidades_promedio else 0
    st.subheader(f"⚡ VELOCIDAD: {vel_final:.1f} ejercicios/hora")
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(fechas, velocidades_promedio, color='gold', linewidth=3, marker='s', markersize=8)
    ax.set_ylabel('Velocidad (ejercicios/h)', color='gold', fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    st.divider()

    # --- EXÁMENES ---
    st.subheader("🎯 EXÁMENES")
    
    # Calcular promedios de exámenes
    prom_semanal = 0
    prom_uni = 0
    count_sem = 0
    count_uni = 0
    
    fechas_sim = []
    notas_sim = []
    tipos_sim = []
    
    if datos["semanal"]:
        simulacros_ordenados = sorted(datos["semanal"], key=lambda x: x["fecha"])
        for sim in simulacros_ordenados:
            fecha_sim = datetime.strptime(sim["fecha"], "%Y-%m-%d")
            fechas_sim.append(fecha_sim)
            
            if sim["tipo"] == "Semanal":
                nota = sim["Puntaje_Simulacro"]
                prom_semanal += nota
                count_sem += 1
            else:
                nota = sim["Promedio_Notas"]
                prom_uni += nota
                count_uni += 1
            notas_sim.append(nota)
            tipos_sim.append(sim["tipo"])
            
    if count_sem > 0: prom_semanal /= count_sem
    if count_uni > 0: prom_uni /= count_uni

    col1, col2 = st.columns(2)
    with col1:
        st.metric(" Promedio Semanales", f"{prom_semanal:.1f}")
    with col2:
        st.metric("🎓 Promedio Tipo UNI", f"{prom_uni:.1f}")
        
    if fechas_sim:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(fechas_sim, notas_sim, color='green', linewidth=2, linestyle='-')
        
        # Puntos diferenciados
        for i, (fecha, nota, tipo) in enumerate(zip(fechas_sim, notas_sim, tipos_sim)):
            if tipo == "Semanal":
                ax.scatter(fecha, nota, color='blue', marker='o', s=100, zorder=5, label='Semanal' if i==0 else "")
            else:
                ax.scatter(fecha, nota, color='red', marker='s', s=100, zorder=5, label='Tipo UNI' if i==0 else "")
                
        ax.set_ylabel('Nota (0-20)', fontweight='bold')
        ax.set_ylim(0, 20)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("Aún no hay datos de exámenes registrados.")
        
else:
    st.warning("️ Aún no hay datos registrados. Ve a la sección de Registro al final de la página.")

st.divider()

# ============================================
# SECCIÓN 2: RENDIMIENTO POR CURSO
# ============================================
st.markdown('<div id="rendimiento-curso"></div>', unsafe_allow_html=True)
st.header("📚 SECCIÓN: RENDIMIENTO POR CURSO")
st.divider()

if datos["diario"]:
    # --- ESTADÍSTICAS POR MATERIA ---
    st.subheader("📖 ESTADÍSTICAS")
    
    materias_stats = {}
    for dia in datos["diario"]:
        for materia, stats in dia["materias"].items():
            if materia not in materias_stats:
                materias_stats[materia] = {"dias": 0, "ejercicios": 0, "horas": 0, "disciplinas": [], "velocidades": []}
            materias_stats[materia]["dias"] += 1
            materias_stats[materia]["ejercicios"] += stats["Ejercicios_Resueltos"]
            materias_stats[materia]["horas"] += stats["horas_estudiadas"]
            materias_stats[materia]["disciplinas"].append(stats["Disciplina"])
            materias_stats[materia]["velocidades"].append(stats["Velocidad"])

    for materia, stats in materias_stats.items():
        with st.expander(f"▼ {materia}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📅 Días estudiados: {stats['dias']}")
                st.write(f"📚 Ejercicios totales: {stats['ejercicios']}")
                st.write(f"⏰ Horas totales: {stats['horas']:.1f}h")
            with col2:
                st.write(f"🔥 Disciplina: {sum(stats['disciplinas'])/len(stats['disciplinas']):.1f}%")
                st.write(f"⚡ Velocidad: {sum(stats['velocidades'])/len(stats['velocidades']):.1f} ejercicios/h")
    
    st.divider()

    # Preparar datos para gráficos por materia
    materias_grafico = ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]
    disciplinas_por_materia = {m: [] for m in materias_grafico}
    velocidades_por_materia = {m: [] for m in materias_grafico}
    fechas_det = []
    
    for dia in datos["diario"][-30:]:
        if dia["dia"] != "Domingo": # Solo días de semana para materias individuales
            fechas_det.append(datetime.strptime(dia["fecha"], "%Y-%m-%d"))
            for materia in materias_grafico:
                if materia in dia["materias"]:
                    disciplinas_por_materia[materia].append(dia["materias"][materia]["Disciplina"])
                    velocidades_por_materia[materia].append(dia["materias"][materia]["Velocidad"])
                else:
                    disciplinas_por_materia[materia].append(None)
                    velocidades_por_materia[materia].append(None)

    # --- DISCIPLINA POR MATERIA ---
    st.subheader(" DISCIPLINA")
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, materia in enumerate(materias_grafico):
        validos = [(f, d) for f, d in zip(fechas_det, disciplinas_por_materia[materia]) if d is not None]
        if validos:
            f_vals, d_vals = zip(*validos)
            ax.plot(f_vals, d_vals, color=COLORES_MATERIAS[i], linewidth=2, marker='o', label=materia)
    ax.set_ylabel('Disciplina (%)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.tick_params(axis='x', rotation=45)
    ax.legend(loc='best', fontsize='small')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    st.divider()

    # --- VELOCIDAD POR MATERIA ---
    st.subheader("⚡ VELOCIDAD")
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, materia in enumerate(materias_grafico):
        validos = [(f, v) for f, v in zip(fechas_det, velocidades_por_materia[materia]) if v is not None]
        if validos:
            f_vals, v_vals = zip(*validos)
            ax.plot(f_vals, v_vals, color=COLORES_MATERIAS[i], linewidth=2, marker='s', label=materia)
    ax.set_ylabel('Velocidad (ejercicios/h)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.tick_params(axis='x', rotation=45)
    ax.legend(loc='best', fontsize='small')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    st.divider()

    # --- EJERCICIOS VS HORAS ---
    st.subheader("📊 EJERCICIOS VS HORAS")
    ejercicios_totales = {m: 0 for m in materias_grafico}
    tiempo_total = {m: 0 for m in materias_grafico}
    
    for dia in datos["diario"]:
        for materia, stats in dia["materias"].items():
            if materia in ejercicios_totales:
                ejercicios_totales[materia] += stats["Ejercicios_Resueltos"]
                tiempo_total[materia] += stats["horas_estudiadas"]
                
    x = range(len(materias_grafico))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar([i - width/2 for i in x], [ejercicios_totales[m] for m in materias_grafico], width, label='Ejercicios', color='#3498DB')
    ax.bar([i + width/2 for i in x], [tiempo_total[m] for m in materias_grafico], width, label='Horas', color='#E74C3C')
    ax.set_xticks(x)
    ax.set_xticklabels(materias_grafico)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

else:
    st.warning("⚠️ No hay datos de materias registrados.")

st.divider()

# ============================================
# SECCIÓN 3: REGISTRO (PROTEGIDO)
# ============================================
st.header("🔐 ACCEDER AL REGISTRO")

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    password_input = st.text_input("Ingresa la contraseña para registrar datos:", type="password")
    if st.button("🔓 Desbloquear Registro", type="primary"):
        if password_input == CONTRASEÑA_REGISTRO:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")
else:
    st.success("🔓 Sesión iniciada. Puedes registrar tus datos.")
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
    
    st.divider()
    
    # --- FORMULARIO DIARIO ---
    st.subheader("📝 Registro Diario")
    dia_semana = datetime.today().weekday()
    nombre_dia = NOMBRES_DIAS[dia_semana]
    horas_disponibles_total = HORAS_DISPONIBLES[dia_semana]
    materias = HORARIO_MATERIAS[dia_semana]
    
    st.info(f"📅 Hoy es **{nombre_dia}**. Tienes **{horas_disponibles_total} horas** disponibles.")
    
    registro_materias = {}
    total_ejercicios = 0
    total_horas = 0
    
    for materia in materias:
        horas_disp = HORAS_DOMINGO_POR_MATERIA[materia] if dia_semana == 6 else horas_disponibles_total
        
        st.markdown(f"### 📖 {materia}")
        col1, col2 = st.columns(2)
        with col1:
            horas_input = st.number_input(f"Horas ({materia})", min_value=0, value=0, step=1, key=f"horas_{materia}")
        with col2:
            ejercicios_input = st.number_input(f"Ejercicios ({materia})", min_value=0, value=0, step=1, key=f"ejer_{materia}")
            
        disciplina = (horas_input / horas_disp) * 100 if horas_disp > 0 else 0
        velocidad = ejercicios_input / horas_input if horas_input > 0 else 0
        
        registro_materias[materia] = {
            "horas_disponibles": horas_disp, "horas_estudiadas": float(horas_input),
            "Ejercicios_Resueltos": ejercicios_input, "Disciplina": round(disciplina, 2), "Velocidad": round(velocidad, 2)
        }
        total_ejercicios += ejercicios_input
        total_horas += horas_input
        st.divider()

    if st.button("💾 Guardar Día", type="primary", use_container_width=True):
        registro_dia = {
            "fecha": datetime.now().strftime("%Y-%m-%d"), "dia": nombre_dia,
            "horas_disponibles_total": horas_disponibles_total, "materias": registro_materias,
            "Total_Ejercicios_Resueltos_Dia": total_ejercicios, "Total_Horas_Estudiadas": total_horas
        }
        datos["diario"].append(registro_dia)
        guardar_datos(datos)
        st.success(f"✅ ¡Día registrado! {total_ejercicios} ejercicios.")
        st.balloons()

    st.divider()

    # --- FORMULARIO SIMULACROS ---
    st.subheader("🏆 Registro de Simulacro")
    tipo_simulacro = st.radio("Tipo de simulacro:", ["📝 Semanal", "🎓 Tipo UNI"], horizontal=True)
    
    if tipo_simulacro == "📝 Semanal":
        col1, col2 = st.columns(2)
        with col1: puntaje = st.number_input("Puntaje (0-20)", min_value=0.0, max_value=20.0, step=0.1)
        with col2: correctas = st.number_input("Correctas (0-60)", min_value=0, max_value=60, step=1)
        
        if st.button("💾 Guardar Semanal", type="primary"):
            datos["semanal"].append({
                "fecha": datetime.now().strftime("%Y-%m-%d"), "tipo": "Semanal",
                "Puntaje_Simulacro": puntaje, "Precisión": round((correctas/60)*100, 2)
            })
            guardar_datos(datos)
            st.success("✅ Simulacro Semanal guardado.")
    else:
        st.write("Registro Tipo UNI (3 días) - *Funcionalidad disponible próximamente*")
