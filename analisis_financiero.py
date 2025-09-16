import pandas as pd
import streamlit as st
import plotly.express as px
import io

st.set_page_config(page_title="Dashboard Financiero Proyecto Eólico", layout="wide")
st.title("📊 Dashboard Financiero Proyecto Eólico")

archivo = "detallefinanciero.xlsx"
df = pd.read_excel(archivo, sheet_name="Base")

# Limpieza básica y nuevas columnas útiles
df = df.dropna(subset=["Fecha de documento", "Val/Mon.so.CO", "Proveedor"])
df["Fecha de documento"] = pd.to_datetime(df["Fecha de documento"])
df["Año-Mes"] = df["Fecha de documento"].dt.to_period("M").astype(str)

# --- KPIs superiores ---
presupuesto_total = 126_000_000
ejecutado = df["Val/Mon.so.CO"].sum()
saldo = presupuesto_total - ejecutado
porcentaje_ejecutado = ejecutado / presupuesto_total if presupuesto_total > 0 else 0

col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 1])  # Más ancho para números grandes

col1.metric("💰 Presupuesto Inyectado", f"${presupuesto_total:,.0f} CLP")
col2.metric("💸 Monto Ejecutado", f"${ejecutado:,.0f} CLP")
col3.metric("🟢 Saldo Disponible", f"${saldo:,.0f} CLP")
col4.metric("📊 % Ejecutado", f"{porcentaje_ejecutado*100:,.1f} %")

# === FILTROS PRINCIPALES ===
st.sidebar.header("🔎 Filtros principales")

# Denominaciones de Objeto
todos_objetos = sorted(df["Denominación del objeto"].dropna().unique())
opciones_objeto = ["[Seleccionar todo]"] + todos_objetos

objeto_sel = st.sidebar.multiselect(
    "Denominaciones de Objeto",
    options=opciones_objeto,
    default=["[Seleccionar todo]"],
    help="Selecciona uno o varios objetos, o elige '[Seleccionar todo]' para mostrar todos."
)
if "[Seleccionar todo]" in objeto_sel or not objeto_sel:
    objeto_sel = todos_objetos

# Proveedores filtrados SOLO por los objetos seleccionados
proveedores_filtrados = sorted(df[df["Denominación del objeto"].isin(objeto_sel)]["Proveedor"].unique())
opciones_proveedor = ["[Seleccionar todo]"] + proveedores_filtrados

proveedor_sel = st.sidebar.multiselect(
    "Proveedores",
    options=opciones_proveedor,
    default=["[Seleccionar todo]"],
    help="Selecciona uno o varios proveedores, o elige '[Seleccionar todo]' para mostrar todos los proveedores del objeto filtrado."
)
if "[Seleccionar todo]" in proveedor_sel or not proveedor_sel:
    proveedor_sel = proveedores_filtrados

# Filtrado final
df_filtrado = df[
    (df["Denominación del objeto"].isin(objeto_sel)) &
    (df["Proveedor"].isin(proveedor_sel))
]

with st.sidebar.expander("Filtros avanzados (ejemplo)", expanded=False):
    st.caption("Aquí puedes agregar más filtros en el futuro (por fecha, monto, etc.)")

# --- GRAFICO 1: Evolución temporal (barras) ---
st.subheader("Evolución mensual de inversión")
evolucion = df_filtrado.groupby("Año-Mes")["Val/Mon.so.CO"].sum().reset_index()
fig1 = px.bar(
    evolucion, x="Año-Mes", y="Val/Mon.so.CO",
    labels={"Año-Mes": "Mes", "Val/Mon.so.CO": "Monto CLP"},
    title="Inversión Mensual", text_auto=True
)
st.plotly_chart(fig1, use_container_width=True)

# --- GRAFICO 2: Ejecución acumulada (línea) ---
evolucion["Ejecución Acumulada"] = evolucion["Val/Mon.so.CO"].cumsum()
fig_acum = px.line(
    evolucion, x="Año-Mes", y="Ejecución Acumulada",
    labels={"Año-Mes": "Mes", "Ejecución Acumulada": "Ejecución Acumulada CLP"},
    title="Ejecución Acumulada del Proyecto"
)
st.plotly_chart(fig_acum, use_container_width=True)

# --- GRAFICO 3: Pie chart distribución por objeto ---
st.subheader("Distribución del Gasto por Centro de Costo (%)")
dist_objeto = (
    df_filtrado.groupby("Denominación del objeto")["Val/Mon.so.CO"]
    .sum()
    .reset_index()
    .sort_values(by="Val/Mon.so.CO", ascending=False)
)
fig_pie = px.pie(
    dist_objeto, values="Val/Mon.so.CO", names="Denominación del objeto",
    title="Participación de Cada Centro de Costo en el Gasto"
)
st.plotly_chart(fig_pie, use_container_width=True)

# --- GRAFICO 4: Barra horizontal de Top 10 Proveedores ---
st.subheader("Ranking de Proveedores")
ranking_prov = (
    df_filtrado.groupby("Proveedor")["Val/Mon.so.CO"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
fig2 = px.bar(
    ranking_prov, y="Proveedor", x="Val/Mon.so.CO", orientation="h",
    labels={"Proveedor": "Proveedor", "Val/Mon.so.CO": "Monto CLP"},
    title="Top 10 Proveedores"
)
st.plotly_chart(fig2, use_container_width=True)

# --- GRAFICO 5: Barra de Top 10 Objetos ---
st.subheader("Top 10 Denominaciones de Objeto por Monto Ejecutado")
top_objetos = (
    dist_objeto.head(10)
)
fig3 = px.bar(
    top_objetos, x="Denominación del objeto", y="Val/Mon.so.CO",
    labels={"Denominación del objeto": "Objeto", "Val/Mon.so.CO": "Monto CLP"},
    title="Top 10 Objetos", text_auto=True
)
st.plotly_chart(fig3, use_container_width=True)

# --- Top 5 mayores gastos individuales ---
st.subheader("🚨 Top 5 Movimientos de Mayor Monto")
top_movimientos = (
    df_filtrado[["Fecha de documento", "Proveedor", "Denominación del objeto", "Val/Mon.so.CO"]]
    .sort_values(by="Val/Mon.so.CO", ascending=False)
    .head(5)
)
st.dataframe(top_movimientos)

# --- Tabla interactiva de todos los movimientos filtrados ---
st.subheader("Detalle de los movimientos filtrados")
st.dataframe(df_filtrado[["Fecha de documento", "Denominación del objeto", "Val/Mon.so.CO", "Proveedor"]])

# --- Exportar datos filtrados a Excel ---
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df_filtrado.to_excel(writer, index=False)
output.seek(0)

st.download_button(
    label="Descargar datos filtrados en Excel",
    data=output,
    file_name="detalle_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)



