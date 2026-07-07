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
    
    .modebar-btn[data-title="Reset axes"] { background-color: #00d4aa !important; border-radius: 5px !important; padding: 5px !important; }
    .modebar-btn[data-title="Reset axes"] svg { fill: white !important; }
    .modebar-btn[data-title="Pan"] { background-color: #0099ff !important; border-radius: 5px !important; padding: 5px !important; }
    .modebar-btn[data-title="Pan"] svg { fill: white !important; }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURACIÓN Y DATOS
# ============================================
CONTRASEÑA_REGISTRO = "anthuan2027"

SIMBOLOS_CURSOS = {
    "Aritmética": "", "Álgebra": "", "Geometría": "", 
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
# ENCABEZADO Y NAVEGACIÓN
# ============================================
st.title("🎓 Estadísticas de Anthuan: Ciclo Semestral básico 2027-1")
st.markdown("### 👋 Hola, aquí verás mis estadísticas de rendimiento académico.")
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
        with col2: st.metric("📝 Ejercicios resueltos", total_ejercicios)
        with col3: st.metric("⏰ Horas de estudio", f"{int(total_horas)}h")
        st.divider()

        fechas, disc_prom, vel_prom = [], [], []
        for dia in datos["diario"][-30:]:
            f = datetime.strptime(dia["fecha"], "%Y-%m-%d")
            fechas.append(f)
            disc_prom.append(sum(m["Disciplina"] for m in dia["materias"].values()) / len(dia["materias"]))
            vel_prom.append(sum(m["Velocidad"] for m in dia["materias"].values()) / len(dia["materias"]))

        st.subheader(f"🔥 DISCIPLINA: {disc_prom[-1]:.1f}%")
        fig_disc = go.Figure()
        fig_disc.add_trace(go.Scatter(x=fechas, y=disc_prom, mode='lines+markers', name='Disciplina', line=dict(color='red', width=3), marker=dict(size=8, color='red'), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Disciplina: %{y:.1f}%<extra></extra>'))
        fig_disc.update_layout(yaxis_title='Disciplina (%)', yaxis=dict(range=[0, max(100, max(disc_prom)*1.2)]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=400, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_disc, use_container_width=True)
        st.divider()

        st.subheader(f"⚡ VELOCIDAD: {int(vel_prom[-1])} ejercicios/hora")
        fig_vel = go.Figure()
        fig_vel.add_trace(go.Scatter(x=fechas, y=vel_prom, mode='lines+markers', name='Velocidad', line=dict(color='gold', width=3), marker=dict(size=8, color='gold'), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Velocidad: %{y:.1f} ejercicios/h<extra></extra>'))
        fig_vel.update_layout(yaxis_title='Velocidad (ejercicios/h)', yaxis=dict(range=[0, max(20, max(vel_prom)*1.2)]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=400, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_vel, use_container_width=True)
        st.divider()

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
            st.metric("🎯Precisión", f"{prec_sem_prom:.1f}%")
        with col2: 
            st.metric("🏆 Promedio Tipo UNI", f"{prom_uni:.1f}")
            st.metric("🎯Precisión", f"{prec_uni_prom:.1f}%")
            
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
            simbolo = SIMBOLOS_CURSOS.get(mat, "")
            with st.expander(f"▼ {simbolo} {mat}", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"📅 Días estudiados: {s['dias']}")
                    st.write(f"📝 Ejercicios totales: {s['ejercicios']}")
                    st.write(f"⏰ Horas totales: {int(s['horas'])}h")
                with c2:
                    st.write(f"🔥 Disciplina: {sum(s['disc'])/len(s['disc']):.1f}%")
                    st.write(f"⚡ Velocidad: {int(sum(s['vel'])/len(s['vel']))} ejercicios/h")
        st.divider()

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

        st.subheader("🔥 DISCIPLINA")
        fig_disc_mat = go.Figure()
        for i, m in enumerate(mats):
            val = [(f, d) for f, d in zip(f_det, d_mat[m]) if d is not None]
            if val:
                ff, dd = zip(*val)
                fig_disc_mat.add_trace(go.Scatter(x=ff, y=dd, mode='lines+markers', name=f"{SIMBOLOS_CURSOS[m]} {m}", line=dict(color=COLORES_MATERIAS[i], width=2), marker=dict(size=6), hovertemplate=f'<b>%{{x|%Y-%m-%d}}</b><br>{m}: %{{y:.1f}}%<extra></extra>'))
        fig_disc_mat.update_layout(yaxis_title='Disciplina (%)', yaxis=dict(range=[0, 100]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=500, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_disc_mat, use_container_width=True)
        st.divider()

        st.subheader("⚡ VELOCIDAD")
        fig_vel_mat = go.Figure()
        for i, m in enumerate(mats):
            val = [(f, v) for f, v in zip(f_det, v_mat[m]) if v is not None]
            if val:
                ff, vv = zip(*val)
                fig_vel_mat.add_trace(go.Scatter(x=ff, y=vv, mode='lines+markers', name=f"{SIMBOLOS_CURSOS[m]} {m}", line=dict(color=COLORES_MATERIAS[i], width=2), marker=dict(size=6), hovertemplate=f'<b>%{{x|%Y-%m-%d}}</b><br>{m}: %{{y:.1f}} ejer/h<extra></extra>'))
        fig_vel_mat.update_layout(yaxis_title='Velocidad (ejercicios/h)', yaxis=dict(range=[0, max(20, max([v for v in sum(v_mat.values(), []) if v is not None])*1.2)]), xaxis=dict(tickformat='%Y-%m-%d', tickangle=45), hovermode='x unified', height=500, margin=dict(l=50, r=20, t=20, b=50))
        st.plotly_chart(fig_vel_mat, use_container_width=True)
        st.divider()

        st.subheader("📊 EJERCICIOS VS HORAS")
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
        st.warning("⚠️ No hay datos de materias registrados.")

# ============================================
# VISTA: REGISTRO
# ============================================
elif st.session_state.vista_actual == 'registro':
    st.header("📥 REGISTRAR DATOS")
    if st.button("⬅️ Volver al inicio", key="back_registro"):
        st.session_state.vista_actual = 'inicio'
        st.rerun()
    st.divider()
    
    if not st.session_state.autenticado:
        pwd = st.text_input("Ingresa la contraseña para registrar datos:", type="password")
        if st.button("🔓 Desbloquear Registro", type="primary"):
            if pwd == CONTRASEÑA_REGISTRO:
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
        
        # ============================================
        # VERIFICAR REGISTROS DE HOY
        # ============================================
        datos = cargar_datos()
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Verificar registro diario
        ya_registro_hoy = any(d["fecha"] == fecha_hoy for d in datos["diario"])
        
        # Verificar si YA registró CUALQUIER examen hoy (semanal O UNI)
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
            ds = datetime.today().weekday()
            nd = NOMBRES_DIAS[ds]
            hd = HORAS_DISPONIBLES[ds]
            mats = HORARIO_MATERIAS[ds]
            st.info(f"📅 Hoy es **{nd}**. Tienes **{hd} horas** disponibles.")
            
            reg_mat = {}
            tot_ej, tot_hr = 0, 0
            
            for m in mats:
                simbolo = SIMBOLOS_CURSOS.get(m, "")
                hd_m = HORAS_DOMINGO_POR_MATERIA[m] if ds == 6 else hd
                st.markdown(f"### {simbolo} {m}")
                c1, c2 = st.columns(2)
                with c1: h_in = st.number_input(f"Horas ({m})", min_value=0, value=0, step=1, key=f"h_{m}")
                with c2: e_in = st.number_input(f"Ejercicios ({m})", min_value=0, value=0, step=1, key=f"e_{m}")
                
                disc = (h_in / hd_m) * 100 if hd_m > 0 else 0
                vel = e_in / h_in if h_in > 0 else 0
                reg_mat[m] = {"horas_disponibles": hd_m, "horas_estudiadas": float(h_in), "Ejercicios_Resueltos": e_in, "Disciplina": round(disc, 2), "Velocidad": round(vel, 2)}
                tot_ej += e_in; tot_hr += h_in
                st.divider()

            if st.button("💾 Guardar Día", type="primary", use_container_width=True):
                datos["diario"].append({
                    "fecha": fecha_hoy, "dia": nd,
                    "horas_disponibles_total": hd, "materias": reg_mat,
                    "Total_Ejercicios_Resueltos_Dia": tot_ej, "Total_Horas_Estudiadas": tot_hr
                })
                guardar_datos(datos)
                st.success(f"✅ ¡Día registrado! {tot_ej} ejercicios.")
                st.balloons()

        st.divider()
        
        # ============================================
        # REGISTRO DE EXÁMENES (SOLO UNO POR DÍA)
        # ============================================
        st.subheader("📄 Registro de exámenes")
        
        if ya_registro_examen_hoy:
            # Mostrar el examen que ya registró hoy
            examen_registrado = examen_hoy[0]
            st.warning("⚠️ Ya registraste un examen hoy. Solo se permite un examen por día.")
            
            st.divider()
            st.subheader("📊 Examen registrado hoy:")
            
            if examen_registrado["tipo"] == "Semanal":
                st.write(f"**Tipo:** 🥇 Examen Semanal")
                st.write(f"**Puntaje:** {examen_registrado['Puntaje_Simulacro']}")
                st.write(f"**Precisión:** {examen_registrado.get('Precisión', 'N/A')}%")
            else:
                st.write(f"**Tipo:** 🏆 Examen Tipo UNI")
                st.write(f"**Nota final:** {examen_registrado['Promedio_Notas']}")
                st.write(f"**Precisión:** {examen_registrado.get('Promedio_Precision', 'N/A')}%")
        else:
            # Permitir registrar un examen
            tipo = st.radio("Tipo de examen:", ["🥇 Semanal", "🏆 Tipo UNI"], horizontal=True)
            
            if tipo == "🥇 Semanal":
                c1, c2 = st.columns(2)
                with c1: pj = st.number_input("Puntaje (0-20)", min_value=0.0, max_value=20.0, step=0.1)
                with c2: co = st.number_input("Correctas (0-60)", min_value=0, max_value=60, step=1)
                
                precision_calc = (co / 60) * 100
                st.metric("🎯Precisión", f"{precision_calc:.1f}%")
                
                if st.button("💾 Guardar Examen Semanal", type="primary"):
                    datos["semanal"].append({"fecha": fecha_hoy, "tipo": "Semanal", "Puntaje_Simulacro": pj, "Precisión": round(precision_calc, 2)})
                    guardar_datos(datos)
                    st.success("✅ Examen Semanal guardado.")
                    st.balloons()
                    st.rerun()
            else:
                st.subheader("🏆 Examen Tipo UNI (3 días)")
                
                dias_uni = [
                    {"nombre": "🌐 Aptitud Académica y Humanidades", "preguntas": 100},
                    {"nombre": "🔢 Matemáticas", "preguntas": 40},
                    {"nombre": "🧪 Ciencias", "preguntas": 40}
                ]
                
                dias_datos = []
                for i, dia_info in enumerate(dias_uni):
                    with st.expander(f"📅 Día {i+1} - {dia_info['nombre']} ({dia_info['preguntas']} preguntas)", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            puntaje_dia = st.number_input("Puntaje", min_value=0.0, max_value=20.0, step=0.1, key=f"punti_dia_{i}")
                        with col2:
                            correctas_dia = st.number_input("Preguntas acertadas", min_value=0, max_value=dia_info['preguntas'], step=1, key=f"corr_dia_{i}")
                        
                        precision_dia = (correctas_dia / dia_info['preguntas']) * 100 if dia_info['preguntas'] > 0 else 0
                        dias_datos.append({"dia": i+1, "nombre": dia_info['nombre'], "puntaje": puntaje_dia, "correctas": correctas_dia, "precision": round(precision_dia, 2)})
                        st.write(f"**🎯Precisión:** {precision_dia:.1f}%")
                
                if dias_datos:
                    prom_notas = sum(d["puntaje"] for d in dias_datos) / 3
                    prom_precision = sum(d["precision"] for d in dias_datos) / 3
                    
                    st.divider()
                    st.subheader("📊 Resumen del Examen UNI")
                    col1, col2 = st.columns(2)
                    with col1: st.metric("🏆 Nota final", f"{prom_notas:.2f}")
                    with col2: st.metric("🎯 Precisión", f"{prom_precision:.1f}%")
                    
                    if st.button("💾 Guardar Examen UNI", type="primary", use_container_width=True):
                        ejercicios_semana = sum(d["Total_Ejercicios_Resueltos_Dia"] for d in datos["diario"][-7:])
                        registro = {
                            "fecha": fecha_hoy, "tipo": "UNI", "dias": dias_datos,
                            "Promedio_Notas": round(prom_notas, 2), "Promedio_Precision": round(prom_precision, 2),
                            "Ejercicios_Resueltos_Semana": ejercicios_semana
                        }
                        datos["semanal"].append(registro)
                        guardar_datos(datos)
                        st.success(f"✅ ¡Examen UNI registrado! Nota final: {prom_notas:.2f}")
                        st.balloons()
                        st.rerun()
