import streamlit as st
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Configuración de la página
st.set_page_config(page_title="Dashboard de Anthuan", page_icon="📚", layout="wide")

# Configuración del horario
HORAS_DISPONIBLES = {0: 6, 1: 6, 2: 6, 3: 6, 4: 6, 5: 7, 6: 13}
HORARIO_MATERIAS = {
    0: ["Aritmética"],
    1: ["Álgebra"],
    2: ["Geometría"],
    3: ["Trigonometría"],
    4: ["Física"],
    5: ["Química"],
    6: ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]
}
HORAS_DOMINGO_POR_MATERIA = {
    "Aritmética": 2, "Álgebra": 2, "Geometría": 2, 
    "Trigonometría": 2, "Física": 3, "Química": 2
}
NOMBRES_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
COLORES_MATERIAS = ["#0BDCF4", "#E4EA38", "#5E664A", "#35C938", "#503EDA", "#E01C1C", "#C540A2"]
ARCHIVO_GUARDADO = "anthuan_stats.json"

# Funciones para cargar y guardar datos
def cargar_datos():
    if os.path.exists(ARCHIVO_GUARDADO):
        with open(ARCHIVO_GUARDADO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"diario": [], "semanal": []}

def guardar_datos(datos):
    with open(ARCHIVO_GUARDADO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# Título principal
st.title("📚 Tablero de Anthuan: Ciclo Semianual 2027-1")

# Menú lateral
st.sidebar.header("Menú Principal")
opcion = st.sidebar.radio("¿Qué quieres hacer?", ["📝 Registrar Día", "🏆 Registrar Simulacro", "📊 Ver Estadísticas", "📈 Ver Gráficos"])

st.divider()

# ============================================
# OPCIÓN 1: REGISTRAR DÍA
# ============================================
if opcion == "📝 Registrar Día":
    st.header("📝 Registro Diario")
    
    dia_semana = datetime.today().weekday()
    nombre_dia = NOMBRES_DIAS[dia_semana]
    horas_disponibles_total = HORAS_DISPONIBLES[dia_semana]
    materias = HORARIO_MATERIAS[dia_semana]
    
    st.info(f"📅 Hoy es **{nombre_dia}**. Tienes **{horas_disponibles_total} horas** disponibles.")
    
    datos = cargar_datos()
    
    registro_materias = {}
    total_ejercicios = 0
    total_horas = 0
    
    st.subheader("📚 Ingresa tus datos por materia:")
    
    for materia in materias:
        if dia_semana == 6:
            horas_disp = HORAS_DOMINGO_POR_MATERIA[materia]
        else:
            horas_disp = horas_disponibles_total
        
        with st.container():
            st.markdown(f"### 📖 {materia}")
            if dia_semana == 6:
                st.caption(f"Horas disponibles: {horas_disp}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                horas_input = st.number_input(
                    f"Horas estudiadas",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"horas_{materia}",
                    label_visibility="collapsed"
                )
                st.write(f"**⏰ Horas:** {int(horas_input)}")
            
            with col2:
                ejercicios_input = st.number_input(
                    f"Ejercicios",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"ejer_{materia}",
                    label_visibility="collapsed"
                )
                st.write(f"**📝 Ejercicios:** {ejercicios_input}")
            
            disciplina = (horas_input / horas_disp) * 100 if horas_disp > 0 else 0
            velocidad = ejercicios_input / horas_input if horas_input > 0 else 0
            
            registro_materias[materia] = {
                "horas_disponibles": horas_disp,
                "horas_estudiadas": float(horas_input),
                "Ejercicios_Resueltos": ejercicios_input,
                "Disciplina": round(disciplina, 2),
                "Velocidad": round(velocidad, 2)
            }
            
            total_ejercicios += ejercicios_input
            total_horas += horas_input
            
            col3, col4 = st.columns(2)
            with col3:
                st.metric("🔥 Disciplina", f"{disciplina:.1f}%")
            with col4:
                st.metric("⚡ Velocidad", f"{velocidad:.1f} ejercicios/h")
            
            st.divider()
    
    st.subheader("📊 Resumen del día")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Total ejercicios", total_ejercicios)
    with col2:
        st.metric("⏰ Total horas", f"{total_horas:.1f}h")
    
    if st.button("💾 Guardar registro del día", type="primary", use_container_width=True):
        registro_dia = {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "dia": nombre_dia,
            "horas_disponibles_total": horas_disponibles_total,
            "materias": registro_materias,
            "Total_Ejercicios_Resueltos_Dia": total_ejercicios,
            "Total_Horas_Estudiadas": total_horas
        }
        
        datos["diario"].append(registro_dia)
        guardar_datos(datos)
        
        st.success(f"✅ ¡Día registrado exitosamente! Total de ejercicios: {total_ejercicios}")
        st.balloons()

# ============================================
# OPCIÓN 2: REGISTRAR SIMULACRO
# ============================================
elif opcion == "🏆 Registrar Simulacro":
    st.header("🏆 Registro de Simulacro")
    
    datos = cargar_datos()
    
    tipo_simulacro = st.radio(
        "¿Qué tipo de simulacro vas a registrar?", 
        ["📝 Semanal (60 preguntas)", "🎓 Tipo UNI (3 días)"],
        index=0
    )
    
    st.divider()
    
    if tipo_simulacro == "📝 Semanal (60 preguntas)":
        st.subheader("📝 Simulacro Semanal")
        
        col1, col2 = st.columns(2)
        with col1:
            puntaje = st.number_input("Puntaje obtenido (0-20)", min_value=0.0, max_value=20.0, step=0.1)
        with col2:
            correctas = st.number_input("Preguntas correctas", min_value=0, max_value=60, step=1)
        
        precision = (correctas / 60) * 100 if correctas > 0 else 0
        
        st.metric("📊 Precisión", f"{precision:.1f}%")
        
        if st.button("💾 Guardar Simulacro Semanal", type="primary", use_container_width=True):
            ejercicios_semana = sum(d["Total_Ejercicios_Resueltos_Dia"] for d in datos["diario"][-7:])
            
            registro = {
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "tipo": "Semanal",
                "Puntaje_Simulacro": puntaje,
                "Precisión": round(precision, 2),
                "Ejercicios_Resueltos_Semana": ejercicios_semana
            }
            
            datos["semanal"].append(registro)
            guardar_datos(datos)
            
            st.success(f"✅ ¡Simulacro registrado! Puntaje: {puntaje}")
            st.balloons()
    
    else:
        st.subheader("🎓 Simulacro Tipo UNI (3 días)")
        
        totales = [100, 40, 40]
        dias_datos = []
        
        for i in range(3):
            with st.expander(f"📅 Día {i+1} ({totales[i]} preguntas)", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    puntaje_dia = st.number_input(f"Puntaje Día {i+1}", min_value=0.0, max_value=20.0, step=0.1, key=f"punti_dia_{i}")
                with col2:
                    correctas_dia = st.number_input(f"Correctas Día {i+1}", min_value=0, max_value=totales[i], step=1, key=f"corr_dia_{i}")
                
                precision_dia = (correctas_dia / totales[i]) * 100 if totales[i] > 0 else 0
                
                dias_datos.append({
                    "dia": i+1,
                    "puntaje": puntaje_dia,
                    "correctas": correctas_dia,
                    "precision": round(precision_dia, 2)
                })
                
                st.write(f"**Precisión Día {i+1}:** {precision_dia:.1f}%")
        
        prom_notas = sum(d["puntaje"] for d in dias_datos) / 3
        prom_precision = sum(d["precision"] for d in dias_datos) / 3
        
        st.divider()
        st.subheader("📊 Resumen del Simulacro UNI")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🎯 Promedio de Notas", f"{prom_notas:.2f}")
        with col2:
            st.metric("📊 Promedio de Precisión", f"{prom_precision:.1f}%")
        
        if st.button("💾 Guardar Simulacro UNI", type="primary", use_container_width=True):
            ejercicios_semana = sum(d["Total_Ejercicios_Resueltos_Dia"] for d in datos["diario"][-7:])
            
            registro = {
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "tipo": "UNI",
                "dias": dias_datos,
                "Promedio_Notas": round(prom_notas, 2),
                "Promedio_Precision": round(prom_precision, 2),
                "Ejercicios_Resueltos_Semana": ejercicios_semana
            }
            
            datos["semanal"].append(registro)
            guardar_datos(datos)
            
            st.success(f"✅ ¡Simulacro UNI registrado! Promedio: {prom_notas:.2f}")
            st.balloons()

# ============================================
# OPCIÓN 3: VER ESTADÍSTICAS
# ============================================
elif opcion == "📊 Ver Estadísticas":
    st.header("📊 Estadísticas")
    
    datos = cargar_datos()
    
    if not datos["diario"] and not datos["semanal"]:
        st.warning("⚠️ Aún no hay datos registrados. ¡A estudiar!")
    else:
        tipo_stats = st.radio(
            "¿Qué estadísticas quieres ver?", 
            ["📊 Generales del Ciclo", "📚 Por Materia"],
            horizontal=True,
            index=0
        )
        
        if tipo_stats == "📊 Generales del Ciclo":
            st.subheader("📊 Estadísticas Generales del Ciclo")
            
            if datos["diario"]:
                total_dias = len(datos["diario"])
                total_ejercicios = sum(d["Total_Ejercicios_Resueltos_Dia"] for d in datos["diario"])
                total_horas = sum(d["Total_Horas_Estudiadas"] for d in datos["diario"])
                
                todas_disciplinas = []
                todas_velocidades = []
                
                for dia in datos["diario"]:
                    for materia, stats in dia["materias"].items():
                        todas_disciplinas.append(stats["Disciplina"])
                        todas_velocidades.append(stats["Velocidad"])
                
                velocidad_promedio = sum(todas_velocidades) / len(todas_velocidades) if todas_velocidades else 0
                disciplina_promedio = sum(todas_disciplinas) / len(todas_disciplinas) if todas_disciplinas else 0
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📅 Total de días registrados", total_dias)
                    st.metric("📚 Total de ejercicios resueltos", total_ejercicios)
                with col2:
                    st.metric("⏰ Total de horas estudiadas", f"{total_horas:.1f}h")
                    st.metric("⚡ Velocidad", f"{velocidad_promedio:.1f} ejercicios/h")
                
                st.metric("🔥 Disciplina", f"{disciplina_promedio:.1f}%")
                
                if datos["semanal"]:
                    st.divider()
                    total_simulacros = len(datos["semanal"])
                    semanales = [s for s in datos["semanal"] if s["tipo"] == "Semanal"]
                    unis = [s for s in datos["semanal"] if s["tipo"] == "UNI"]
                    
                    st.subheader("🎯 Simulacros")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Simulacros", total_simulacros)
                    with col2:
                        st.metric("📝 Semanales", len(semanales))
                    with col3:
                        st.metric("🎓 Tipo UNI", len(unis))
        
        else:
            st.subheader("📚 Estadísticas Detalladas por Materia")
            
            if datos["diario"]:
                materias_stats = {}
                
                for dia in datos["diario"]:
                    for materia, stats in dia["materias"].items():
                        if materia not in materias_stats:
                            materias_stats[materia] = {
                                "dias": 0,
                                "ejercicios": 0,
                                "horas": 0,
                                "disciplinas": [],
                                "velocidades": []
                            }
                        
                        materias_stats[materia]["dias"] += 1
                        materias_stats[materia]["ejercicios"] += stats["Ejercicios_Resueltos"]
                        materias_stats[materia]["horas"] += stats["horas_estudiadas"]
                        materias_stats[materia]["disciplinas"].append(stats["Disciplina"])
                        materias_stats[materia]["velocidades"].append(stats["Velocidad"])
                
                for materia, stats in materias_stats.items():
                    with st.expander(f"📖 {materia}", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**📅 Días estudiados:** {stats['dias']}")
                            st.write(f"**📚 Ejercicios totales:** {stats['ejercicios']}")
                            st.write(f"**⏰ Horas totales:** {stats['horas']:.1f}h")
                        with col2:
                            st.write(f"**🔥 Disciplina:** {sum(stats['disciplinas'])/len(stats['disciplinas']):.1f}%")
                            st.write(f"**⚡ Velocidad:** {sum(stats['velocidades'])/len(stats['velocidades']):.1f} ejercicios/h")

# ============================================
# OPCIÓN 4: VER GRÁFICOS (MEJORADO)
# ============================================
elif opcion == "📈 Ver Gráficos":
    st.header("📈 Gráficos de rendimiento")
    
    datos = cargar_datos()
    
    # DEBUG: Mostrar información de depuración
    st.info(f"🔍 DEBUG: {len(datos['diario'])} días registrados, {len(datos.get('semanal', []))} simulacros")
    
    # Verificar si hay datos
    if not datos["diario"]:
        st.error("⚠️ No hay datos registrados aún.")
        st.info("💡 Ve a '📝 Registrar Día' y registra tu primer día de estudio.")
        st.stop()
    
    st.success(f"✅ {len(datos['diario'])} días registrados - {len(datos.get('semanal', []))} simulacros")
    
    # Preparar datos para gráficos
    try:
        materias_grafico = ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química", "Repaso"]
        disciplinas_por_materia = {m: [] for m in materias_grafico}
        velocidades_por_materia = {m: [] for m in materias_grafico}
        fechas = []
        
        for dia in datos["diario"][-30:]:
            fechas.append(datetime.strptime(dia["fecha"], "%Y-%m-%d"))
            
            if dia["dia"] == "Domingo":
                disc_repaso = [materia_data["Disciplina"] for materia_data in dia["materias"].values()]
                vel_repaso = [materia_data["Velocidad"] for materia_data in dia["materias"].values()]
                
                for materia in ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]:
                    disciplinas_por_materia[materia].append(None)
                    velocidades_por_materia[materia].append(None)
                
                disciplinas_por_materia["Repaso"].append(sum(disc_repaso) / len(disc_repaso) if disc_repaso else 0)
                velocidades_por_materia["Repaso"].append(sum(vel_repaso) / len(vel_repaso) if vel_repaso else 0)
            else:
                for materia in ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]:
                    if materia in dia["materias"]:
                        disciplinas_por_materia[materia].append(dia["materias"][materia]["Disciplina"])
                        velocidades_por_materia[materia].append(dia["materias"][materia]["Velocidad"])
                    else:
                        disciplinas_por_materia[materia].append(None)
                        velocidades_por_materia[materia].append(None)
                
                disciplinas_por_materia["Repaso"].append(None)
                velocidades_por_materia["Repaso"].append(None)
        
        # Selector de tipo de gráfico
        tipo_grafico = st.radio(
            "¿Qué gráficos quieres ver?", 
            ["📊 Estadísticas Generales", "📈 Estadísticas Detalladas"],
            horizontal=True
        )
        
        # ==========================================
        # GRÁFICO 1: ESTADÍSTICAS GENERALES
        # ==========================================
        if tipo_grafico == "📊 Estadísticas Generales":
            st.subheader("📊 Disciplina y Velocidad")
            
            # Calcular promedios
            disciplinas_promedio = []
            velocidades_promedio = []
            
            for dia in datos["diario"][-30:]:
                disc_vals = [materia_data["Disciplina"] for materia_data in dia["materias"].values()]
                vel_vals = [materia_data["Velocidad"] for materia_data in dia["materias"].values()]
                
                disciplinas_promedio.append(sum(disc_vals) / len(disc_vals) if disc_vals else 0)
                velocidades_promedio.append(sum(vel_vals) / len(vel_vals) if vel_vals else 0)
            
            # Crear gráfico
            fig, ax1 = plt.subplots(figsize=(14, 7))
            
            # Eje izquierdo - Disciplina (rojo)
            ax1.set_xlabel('Fecha', fontweight='bold', fontsize=12)
            ax1.set_ylabel('Disciplina (%)', color='red', fontweight='bold', fontsize=12)
            ax1.plot(fechas, disciplinas_promedio, color='red', linewidth=3, marker='o', markersize=8, label='Disciplina (%)')
            ax1.tick_params(axis='y', labelcolor='red')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3)
            
            # Eje derecho - Velocidad (dorado)
            ax2 = ax1.twinx()
            ax2.set_ylabel('Velocidad (ejercicios/h)', color='gold', fontweight='bold', fontsize=12)
            ax2.plot(fechas, velocidades_promedio, color='gold', linewidth=3, marker='s', markersize=8, label='Velocidad (ejercicios/h)')
            ax2.tick_params(axis='y', labelcolor='gold')
            
            # Título y leyenda
            ax1.set_title('📊 Disciplina y Velocidad', fontweight='bold', fontsize=14)
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=10)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        # ==========================================
        # GRÁFICO 2: ESTADÍSTICAS DETALLADAS (4 gráficos)
        # ==========================================
        else:
            st.subheader("📈 Gráficos Detallados")
            
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            
            # GRÁFICO 1: DISCIPLINA POR MATERIA
            for i, materia in enumerate(materias_grafico):
                disc_validos = [(f, d) for f, d in zip(fechas, disciplinas_por_materia[materia]) if d is not None]
                if disc_validos:
                    fechas_disc, disc_vals = zip(*disc_validos)
                    axes[0, 0].plot(fechas_disc, disc_vals, color=COLORES_MATERIAS[i], 
                                   linewidth=2.5, marker='o', markersize=6, label=f'{materia}')
            
            axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            axes[0, 0].xaxis.set_major_locator(mdates.AutoDateLocator())
            axes[0, 0].tick_params(axis='x', rotation=45)
            axes[0, 0].set_title('🔥 DISCIPLINA', fontweight='bold', fontsize=14)
            axes[0, 0].set_xlabel('Fecha')
            axes[0, 0].set_ylabel('Disciplina (%)')
            axes[0, 0].legend(loc='best', fontsize='small')
            axes[0, 0].grid(True, alpha=0.3)
            
            # GRÁFICO 2: VELOCIDAD POR MATERIA
            for i, materia in enumerate(materias_grafico):
                vel_validos = [(f, v) for f, v in zip(fechas, velocidades_por_materia[materia]) if v is not None]
                if vel_validos:
                    fechas_vel, vel_vals = zip(*vel_validos)
                    axes[0, 1].plot(fechas_vel, vel_vals, color=COLORES_MATERIAS[i], 
                                   linewidth=2.5, marker='s', markersize=6, label=f'{materia}')
            
            axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            axes[0, 1].xaxis.set_major_locator(mdates.AutoDateLocator())
            axes[0, 1].tick_params(axis='x', rotation=45)
            axes[0, 1].set_title('⚡ VELOCIDAD', fontweight='bold', fontsize=14)
            axes[0, 1].set_xlabel('Fecha')
            axes[0, 1].set_ylabel('Velocidad (ejercicios/h)')
            axes[0, 1].legend(loc='best', fontsize='small')
            axes[0, 1].grid(True, alpha=0.3)
            
            # GRÁFICO 3: BARRAS - EJERCICIOS VS HORAS
            materias_individuales = ["Aritmética", "Álgebra", "Geometría", "Trigonometría", "Física", "Química"]
            ejercicios_totales = {m: 0 for m in materias_individuales}
            tiempo_total = {m: 0 for m in materias_individuales}
            
            for dia in datos["diario"]:
                for materia, stats in dia["materias"].items():
                    if materia in ejercicios_totales:
                        ejercicios_totales[materia] += stats["Ejercicios_Resueltos"]
                        tiempo_total[materia] += stats["horas_estudiadas"]
            
            x = range(len(materias_individuales))
            width = 0.35
            
            barras_ejer = axes[1, 0].bar([i - width/2 for i in x], 
                                         [ejercicios_totales[m] for m in materias_individuales], 
                                         width, label='Ejercicios Resueltos', color='#3498DB', alpha=0.8)
            barras_horas = axes[1, 0].bar([i + width/2 for i in x], 
                                          [tiempo_total[m] for m in materias_individuales], 
                                          width, label='Horas Estudiadas', color='#E74C3C', alpha=0.8)
            
            axes[1, 0].set_title('📊 Total Histórico: Ejercicios vs Horas', fontweight='bold')
            axes[1, 0].set_xlabel('Materia')
            axes[1, 0].set_ylabel('Cantidad')
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels(materias_individuales, rotation=45)
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            
            for barra in barras_ejer:
                altura = barra.get_height()
                if altura > 0:
                    axes[1, 0].text(barra.get_x() + barra.get_width()/2., altura,
                                  f'{int(altura)}', ha='center', va='bottom', fontsize=8)
            
            for barra in barras_horas:
                altura = barra.get_height()
                if altura > 0:
                    axes[1, 0].text(barra.get_x() + barra.get_width()/2., altura,
                                  f'{altura:.1f}h', ha='center', va='bottom', fontsize=8)
            
            # GRÁFICO 4: SIMULACROS
            fechas_sim = []
            notas_sim = []
            tipos_sim = []
            
            simulacros_ordenados = sorted(datos["semanal"], key=lambda x: x["fecha"])
            
            for sim in simulacros_ordenados:
                fecha_sim = datetime.strptime(sim["fecha"], "%Y-%m-%d")
                fechas_sim.append(fecha_sim)
                
                if sim["tipo"] == "Semanal":
                    nota = sim["Puntaje_Simulacro"]
                else:
                    nota = sim["Promedio_Notas"]
                notas_sim.append(nota)
                tipos_sim.append(sim["tipo"])
            
            if fechas_sim:
                COLOR_SEMANAL = 'blue'
                COLOR_UNI = 'red'
                
                colores_sim = [COLOR_SEMANAL if t == "Semanal" else COLOR_UNI for t in tipos_sim]
                
                axes[1, 1].plot(fechas_sim, notas_sim, 'o-', linewidth=2, markersize=8, color='green', label='Nota')
                axes[1, 1].scatter(fechas_sim, notas_sim, c=colores_sim, s=80, zorder=5, edgecolors='black')
                
                axes[1, 1].set_ylim(0, 20)
                axes[1, 1].set_yticks(range(0, 21, 2))
                axes[1, 1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                axes[1, 1].xaxis.set_major_locator(mdates.AutoDateLocator())
                axes[1, 1].set_ylabel('Nota (0-20)', fontweight='bold')
                axes[1, 1].set_xlabel('Fecha')
                axes[1, 1].set_title('🎯 Notas en Simulacros', fontweight='bold')
                axes[1, 1].tick_params(axis='x', rotation=45)
                axes[1, 1].grid(True, alpha=0.3)
                
                for i, txt in enumerate(notas_sim):
                    axes[1, 1].annotate(f'{txt:.1f}', (fechas_sim[i], notas_sim[i]), 
                                        textcoords="offset points", xytext=(0,10), ha='center', fontweight='bold')
            else:
                axes[1, 1].text(0.5, 0.5, 'Sin datos de simulacros', ha='center', va='center', fontsize=12)
            
            plt.tight_layout()
            st.pyplot(fig)
    
    except Exception as e:
        st.error(f"❌ Error al generar gráficos: {str(e)}")
        st.info("💡 Esto puede significar que hay un problema con los datos. Intenta registrar más días.")