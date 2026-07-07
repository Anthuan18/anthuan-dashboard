import streamlit as st
import json
import os
from datetime import datetime
import plotly.graph_objects as go

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================
st.set_page_config(
    page_title="Dashboard de Anthuan", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Personalizado
st.markdown("""
<style>
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    .stButton > button {
        border-radius: 10px;
    }
    /* Hacer los gráficos responsivos */
    .js-plotly-plot .plotly {
        width: 100% !important;
    }
    
    /* RESALTAR BOTONES DE PLOTLY */
    /* Botón Home (Casa) - Color verde brillante */
    .modebar-btn[data-title="Reset axes"] {
        background-color: #00d4aa !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }
    .modebar-btn[data-title="Reset axes"] svg {
        fill: white !important;
    }
    .modebar-btn[data-title="Reset axes"]:hover {
        background-color: #00ff88 !important;
    }
    
    /* Botón Pan (Mover) - Color azul brillante */
    .modebar-btn[data-title="Pan"] {
        background-color: #0099ff !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }
    .modebar-btn[data-title="Pan"] svg {
        fill: white !important;
    }
    .modebar-btn[data-title="Pan"]:hover {
        background-color: #00bbff !important;
    }
    
    /* Botón Zoom Box - Color naranja brillante */
    .modebar-btn[data-title="Zoom"] {
        background-color: #ff6600 !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }
    .modebar-btn[data-title="Zoom"] svg {
        fill: white !important;
    }
    .modebar-btn[data-title="Zoom"]:hover {
        background-color: #ff8833 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURACIÓN Y DATOS
# ============================================
CONTRASEÑA_REGISTRO = "anthuan2027"

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
# ESTADO DE LA APLICACIÓN
# ============================================
if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = 'inicio'
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# ============================================
# ENCABEZADO (SIEMPRE VISIBLE)
# ============================================
st.title("📚 Estadísticas de Anthuan: Ciclo Semianual 2027-1")
st.markdown("### 👋 Hola, aquí verás mis estadísticas de rendimiento académico.")
st.divider()

# ============================================
# BOTONES DE NAVEGACIÓN (SOLO EN INICIO)
# ============================================
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
        if st.button("🔐 ACCEDER AL REGISTRO", use_container_width=True, key="btn_registro"):
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
        total_dias = len(datos["diario"])
        total_ejercicios = sum(d["Total_Ejercicios_Resueltos_Dia"] for d in datos["diario"])
        total_horas = sum(d["Total_Horas_Estudiadas"] for d in datos["diario"])
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("📅 Días registrados", total_dias)
        with col2: st.metric("📚 Ejercicios resueltos", total_ejercicios)
        with col3: st.metric("⏰ Horas de estudio", f"{total_horas:.1f}h")
        
        st.divider()

        # Preparar datos para gráficos
        fechas, disc_prom, vel_prom = [], [], []
        for dia in datos["diario"][-30:]:
            f = datetime.strptime(dia["fecha"], "%Y-%m-%d")
            fechas.append(f)
            disc_prom.append(sum(m["Disciplina"] for m in dia["materias"].values()) / len(dia["materias"]))
            vel_prom.append(sum(m["Velocidad"] for m in dia["materias"].values()) / len(dia["materias"]))

        # --- GRÁFICO DE DISCIPLINA (EJE Y DESDE 0) ---
        st.subheader(f"🔥 DISCIPLINA: {disc_prom[-1]:.1f}%")
        fig_disc = go.Figure()
        fig_disc.add_trace(go.Scatter(
            x=fechas, y=disc_prom,
            mode='lines+markers',
            name='Disciplina',
            line=dict(color='red', width=3),
            marker=dict(size=8, color='red'),
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Disciplina: %{y:.1f}%<extra></extra>'
        ))
        fig_disc.update_layout(
            yaxis_title='Disciplina (%)',
            yaxis=dict(range=[0, max(100, max(disc_prom)*1.2)]),  # EJE Y DESDE 0
            xaxis=dict(tickformat='%Y-%m-%d', tickangle=45),
            hovermode='x unified',
            height=400,
            margin=dict(l=50, r=20, t=20, b=50)
        )
        st.plotly_chart(fig_disc, use_container_width=True)
        st.divider()

        # --- GRÁFICO DE VELOCIDAD (EJE Y DESDE 0) ---
        st.subheader(f"⚡ VELOCIDAD: {vel_prom[-1]:.1f} ejercicios/hora")
        fig_vel = go.Figure()
        fig_vel.add_trace(go.Scatter(
            x=fechas, y=vel_prom,
            mode='lines+markers',
            name='Velocidad',
            line=dict(color='gold', width=3),
            marker=dict(size=8, color='gold'),
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Velocidad: %{y:.1f} ejercicios/h<extra></extra>'
        ))
        fig_vel.update_layout(
            yaxis_title='Velocidad (ejercicios/h)',
            yaxis=dict(range=[0, max(20, max(vel_prom)*1.2)]),  # EJE Y DESDE 0
            xaxis=dict(tickformat='%Y-%m-%d', tickangle=45),
            hovermode='x unified',
            height=400,
            margin=dict(l=50, r=20, t=20, b=50)
        )
        st.plotly_chart(fig_vel, use_container_width=True)
        st.divider()

        # --- GRÁFICO DE EXÁMENES (EJE Y DESDE 0) ---
        st.subheader("🎯 EXÁMENES")
        prom_sem, prom_uni, cnt_sem, cnt_uni = 0, 0, 0, 0
        fechas_sim, notas_sim, tipos_sim = [], [], []
        
        if datos["semanal"]:
            for sim in sorted(datos["semanal"], key=lambda x: x["fecha"]):
                f = datetime.strptime(sim["fecha"], "%Y-%m-%d")
                fechas_sim.append(f)
                if sim["tipo"] == "Semanal":
                    notas_sim.append(sim["Puntaje_Simulacro"])
                    prom_sem += sim["Puntaje_Simulacro"]; cnt_sem += 1
                    tipos_sim.append("Semanal")
                else:
                    notas_sim.append(sim["Promedio_Notas"])
                    prom_uni += sim["Promedio_Notas"]; cnt_uni += 1
                    tipos_sim.append("UNI")
        if cnt_sem: prom_sem /= cnt_sem
        if cnt_uni: prom_uni /= cnt_uni

        col1, col2 = st.columns(2)
        with col1: st.metric("📝 Promedio Semanales", f"{prom_sem:.1f}")
        with col2: st.metric("🎓 Promedio Tipo UNI", f"{prom_uni:.1f}")
            
        if fechas_sim:
            fechas_sem = [f for f, t in zip(fechas_sim, tipos_sim) if t == "Semanal"]
            notas_sem = [n for n, t in zip(notas_sim, tipos_sim) if t == "Semanal"]
            fechas_uni = [f for f, t in zip(fechas_sim, tipos_sim) if t == "UNI"]
            notas_uni = [n for n, t in zip(notas_sim, tipos_sim) if t == "UNI"]
            
            fig_exam = go.Figure()
            
            fig_exam.add_trace(go.Scatter(
                x=fechas_sim, y=notas_sim,
                mode='lines',
                name='Tendencia',
                line=dict(color='green', width=2),
                showlegend=False
            ))
            
            if fechas_sem:
                fig_exam.add_trace(go.Scatter(
                    x=fechas_sem, y=notas_sem,
                    mode='markers',
                    name='Semanal',
                    marker=dict(size=10, color='blue', symbol='circle'),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Semanal: %{y:.1f}<extra></extra>'
                ))
            
            if fechas_uni:
                fig_exam.add_trace(go.Scatter(
                    x=fechas_uni, y=notas_uni,
                    mode='markers',
                    name='Tipo UNI',
                    marker=dict(size=10, color='red', symbol='square'),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>UNI: %{y:.1f}<extra></extra>'
                ))
            
            fig_exam.update_layout(
                yaxis_title='Nota (0-20)',
                yaxis=dict(range=[0, 20]),  # EJE Y DESDE 0
                xaxis=dict(tickformat='%Y-%m-%d', tickangle=45),
                hovermode='x unified',
                height=400,
                margin=dict(l=50, r=20, t=20, b=50)
            )
            st.plotly_chart(fig_exam, use_container_width=True)
        else:
            st.info("⚠️ Aún no hay datos de exámenes registrados.")
    else:
        st.warning("⚠️ Aún no hay datos registrados.")

# ============================================
# VISTA: RENDIMIENTO POR CURSO
# ============================================
elif st.session_state.vista_actual == 'curso':
    st.header("📚 SECCIÓN: RENDIMIENTO POR CURSO")
    if st.button("⬅️ Volver al inicio", key="back_curso"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
    st.divider()
    
    datos = cargar_datos()
    
    if datos["diario"]:
        st.subheader("📖 ESTADÍSTICAS")
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

        for mat, s in materias_stats.items():
            with st.expander(f"▼ {mat}", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"📅 Días estudiados: {s['dias']}")
                    st.write(f"📚 Ejercicios totales: {s['ejercicios']}")
                    st.write(f"⏰ Horas totales: {s['horas']:.1f}h")
                with c2:
                    st.write(f"🔥 Disciplina: {sum(s['disc'])/len(s['disc']):.1f}%")
                    st.write(f"⚡ Velocidad: {sum(s['vel'])/len(s['vel']):.1f} ejercicios/h")
        st.divider()

        # Preparar datos para gráficos por materia
        mats = ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]
        f_det, d_mat, v_mat = [], {m:[] for m in mats}, {m:[] for m in mats}
        for dia in datos["diario"][-30:]:
            if dia["dia"] != "Domingo":
                f_det.append(datetime.strptime(dia["fecha"], "%Y-%m-%d"))
                for m in mats:
                    if m in dia["materias"]:
                        d_mat[m].append(dia["materias"][m]["Disciplina"])
                        v_mat[m].append(dia["materias"][m]["Velocidad"])
                    else:
                        d_mat[m].append(None)
                        v_mat[m].append(None)

        # --- GRÁFICO DE DISCIPLINA POR MATERIA (EJE Y DESDE 0) ---
        st.subheader("🔥 DISCIPLINA")
        fig_disc_mat = go.Figure()
        for i, m in enumerate(mats):
            val = [(f, d) for f, d in zip(f_det, d_mat[m]) if d is not None]
            if val:
                ff, dd = zip(*val)
                fig_disc_mat.add_trace(go.Scatter(
                    x=ff, y=dd,
                    mode='lines+markers',
                    name=m,
                    line=dict(color=COLORES_MATERIAS[i], width=2),
                    marker=dict(size=6),
                    hovertemplate=f'<b>%{{x|%Y-%m-%d}}</b><br>{m}: %{{y:.1f}}%<extra></extra>'
                ))
        fig_disc_mat.update_layout(
            yaxis_title='Disciplina (%)',
            yaxis=dict(range=[0, 100]),  # EJE Y DESDE 0
            xaxis=dict(tickformat='%Y-%m-%d', tickangle=45),
            hovermode='x unified',
            height=500,
           
