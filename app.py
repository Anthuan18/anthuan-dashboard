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
    initial_sidebar_state="collapsed"
)

# CSS Personalizado para ocultar la flecha (>>)
st.markdown("""
<style>
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    .stButton > button {
        border-radius: 10px;
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

        fechas, disc_prom, vel_prom = [], [], []
        for dia in datos["diario"][-30:]:
            fechas.append(datetime.strptime(dia["fecha"], "%Y-%m-%d"))
            disc_prom.append(sum(m["Disciplina"] for m in dia["materias"].values()) / len(dia["materias"]))
            vel_prom.append(sum(m["Velocidad"] for m in dia["materias"].values()) / len(dia["materias"]))

        st.subheader(f"🔥 DISCIPLINA: {disc_prom[-1]:.1f}%")
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(fechas, disc_prom, color='red', linewidth=3, marker='o', markersize=6)
        ax.set_ylabel('Disciplina (%)', color='red', fontweight='bold')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        st.divider()

        st.subheader(f"⚡ VELOCIDAD: {vel_prom[-1]:.1f} ejercicios/hora")
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(fechas, vel_prom, color='gold', linewidth=3, marker='s', markersize=6)
        ax.set_ylabel('Velocidad (ejercicios/h)', color='gold', fontweight='bold')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        st.divider()

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
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(fechas_sim, notas_sim, color='green', linewidth=2, linestyle='-')
            for i, (f, n, t) in enumerate(zip(fechas_sim, notas_sim, tipos_sim)):
                ax.scatter(f, n, color='blue' if t=='Semanal' else 'red', marker='o' if t=='Semanal' else 's', s=80, zorder=5, label=t if i==0 else "")
            ax.set_ylabel('Nota (0-20)', fontweight='bold')
            ax.set_ylim(0, 20)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
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
        fig, ax = plt.subplots(figsize=(12, 5))
        for i, m in enumerate(mats):
            val = [(f, d) for f, d in zip(f_det, d_mat[m]) if d is not None]
            if val:
                ff, dd = zip(*val)
                ax.plot(ff, dd, color=COLORES_MATERIAS[i], linewidth=2, marker='o', label=m)
        ax.set_ylabel('Disciplina (%)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.tick_params(axis='x', rotation=45)
        ax.legend(loc='best', fontsize='small')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        st.divider()

        st.subheader("⚡ VELOCIDAD")
        fig, ax = plt.subplots(figsize=(12, 5))
        for i, m in enumerate(mats):
            val = [(f, v) for f, v in zip(f_det, v_mat[m]) if v is not None]
            if val:
                ff, vv = zip(*val)
                ax.plot(ff, vv, color=COLORES_MATERIAS[i], linewidth=2, marker='s', label=m)
        ax.set_ylabel('Velocidad (ejercicios/h)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.tick_params(axis='x', rotation=45)
        ax.legend(loc='best', fontsize='small')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        st.divider()

        st.subheader("📊 EJERCICIOS VS HORAS")
        ej_tot = {m:0 for m in mats}
        hr_tot = {m:0 for m in mats}
        for dia in datos["diario"]:
            for m, s in dia["materias"].items():
                if m in ej_tot:
                    ej_tot[m] += s["Ejercicios_Resueltos"]
                    hr_tot[m] += s["horas_estudiadas"]
        x = range(len(mats))
        w = 0.35
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar([i-w/2 for i in x], [ej_tot[m] for m in mats], w, label='Ejercicios', color='#3498DB')
        ax.bar([i+w/2 for i in x], [hr_tot[m] for m in mats], w, label='Horas', color='#E74C3C')
        ax.set_xticks(x)
        ax.set_xticklabels(mats)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.warning("⚠️ No hay datos de materias registrados.")

# ============================================
# VISTA: REGISTRO
# ============================================
elif st.session_state.vista_actual == 'registro':
    st.header("🔐 ACCEDER AL REGISTRO")
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
        
        st.subheader("📝 Registro Diario")
        ds = datetime.today().weekday()
        nd = NOMBRES_DIAS[ds]
        hd = HORAS_DISPONIBLES[ds]
        mats = HORARIO_MATERIAS[ds]
        st.info(f"📅 Hoy es **{nd}**. Tienes **{hd} horas** disponibles.")
        
        datos = cargar_datos()
        reg_mat = {}
        tot_ej, tot_hr = 0, 0
        
        for m in mats:
            hd_m = HORAS_DOMINGO_POR_MATERIA[m] if ds == 6 else hd
            st.markdown(f"### 📖 {m}")
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
                "fecha": datetime.now().strftime("%Y-%m-%d"), "dia": nd,
                "horas_disponibles_total": hd, "materias": reg_mat,
                "Total_Ejercicios_Resueltos_Dia": tot_ej, "Total_Horas_Estudiadas": tot_hr
            })
            guardar_datos(datos)
            st.success(f"✅ ¡Día registrado! {tot_ej} ejercicios.")
            st.balloons()
            st.rerun()

        st.divider()
        st.subheader("🏆 Registro de Simulacro")
        tipo = st.radio("Tipo de simulacro:", ["📝 Semanal", "🎓 Tipo UNI"], horizontal=True)
        if tipo == "📝 Semanal":
            c1, c2 = st.columns(2)
            with c1: pj = st.number_input("Puntaje (0-20)", min_value=0.0, max_value=20.0, step=0.1)
            with c2: co = st.number_input("Correctas (0-60)", min_value=0, max_value=60, step=1)
            if st.button("💾 Guardar Semanal", type="primary"):
                datos["semanal"].append({"fecha": datetime.now().strftime("%Y-%m-%d"), "tipo": "Semanal", "Puntaje_Simulacro": pj, "Precisión": round((co/60)*100, 2)})
                guardar_datos(datos)
                st.success("✅ Simulacro Semanal guardado.")
                st.rerun()
        else:
            st.write("🎓 Registro Tipo UNI (3 días) - *Funcionalidad disponible próximamente*")
