import streamlit as st
import urllib.parse

st.set_page_config(page_title="PrecioJusto PY", page_icon="💰")

# Títulos
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🇵🇾 PrecioJusto PY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Calculadora para el Revendedor Profesional (v1.0)</p>", unsafe_allow_html=True)

# Función de puntos para Paraguay
def formato_py(monto):
    entero = int(round(float(monto)))
    return "{:,}".format(entero).replace(",", ".")

st.subheader("📦 Datos de Compra")
moneda = st.selectbox("¿En qué moneda compraste?", ["USD (Dólar)", "BRL (Real)", "ARS (Peso)", "PYG (Guaraní)"], key="moneda_sel")

col1, col2 = st.columns(2)
with col1:
    # Agregamos KEY para que no se pierda el dato
    costo_base = st.number_input(f"Precio unitario en {moneda[:3]}", min_value=0.0, step=1.0, value=0.0, key="c_base")
with col2:
    if "USD" in moneda: val_sug = 7550.0
    elif "BRL" in moneda: val_sug = 1540.0
    elif "ARS" in moneda: val_sug = 8.5
    else: val_sug = 1.0
    cotizacion = st.number_input("Cotización hoy", value=val_sug, step=1.0, key="coti")

st.write("---")
# KEYS IMPORTANTES AQUÍ
cantidad = st.number_input("Cantidad de unidades", min_value=1, step=1, value=1, key="cant")
flete = st.number_input("Flete o Pasero por unidad (en ₲)", min_value=0.0, step=1.0, value=0.0, key="flete_in")
ganancia_deseada = st.number_input("¿Cuánto querés ganar limpios por unidad? (en ₲)", min_value=0.0, step=1.0, value=0.0, key="gana_in")

st.write("---")
comision_pos = st.checkbox("¿Cobrás con Tarjeta o QR? (Cubre el 3.3% de comisión)", key="pos_check")

# BOTÓN DE ACCIÓN
if st.button("🧮 Calcular Precio", use_container_width=True):
    # Convertimos todo a números reales para el cálculo
    costo_p_pyg = float(costo_base) * float(cotizacion)
    f_val = float(flete)
    g_val = float(ganancia_deseada)
    subtotal = costo_p_pyg + f_val + g_val

    if comision_pos and subtotal > 0:
        precio_final = subtotal / 0.967
    else:
        precio_final = subtotal

    precio_reposicion = (((float(costo_base) * 1.05) * float(cotizacion)) + f_val + g_val) / (0.967 if comision_pos else 1.0)
    total_lote = precio_final * int(cantidad)

    st.write("---")
    st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #1E88E5;">
            <p style="margin: 0; color: #555; font-weight: bold;">Precio de Venta por Unidad:</p>
            <h1 style="margin: 0; color: #4CAF50;">{formato_py(precio_final)} ₲</h1>
        </div>
    """, unsafe_allow_html=True)

    if int(cantidad) > 1:
        st.info(f"🧮 Total por {cantidad} unidades: **{formato_py(total_lote)} ₲**")

    # DETALLE SIN CEROS
    with st.expander("🔍 Ver detalle del costo", expanded=True):
        st.write(f"1. **Costo Producto:** {formato_py(costo_p_pyg)} ₲")
        st.write(f"2. **Flete/Pasero:** + {formato_py(f_val)} ₲")
        st.write(f"3. **Tu Ganancia Neta:** + {formato_py(g_val)} ₲")
        if comision_pos and precio_final > subtotal:
            st.write(f"4. **Comisión Bancaria:** + {formato_py(precio_final - subtotal)} ₲")

st.write("---")
mi_wa = "595995356287"
url_wa = f"https://wa.me/{mi_wa}?text=Hola%20Ariel,%20quiero%20activar%20la%20version%20PRO"
st.markdown(f'<a href="{url_wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">Solicitar Versión PRO (50.000 ₲)</div></a>', unsafe_allow_html=True)