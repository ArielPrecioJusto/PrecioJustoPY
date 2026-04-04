import streamlit as st
import urllib.parse
import re

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(page_title="PrecioJusto PY", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #fcfdfe; }
    
    .result-card {
        background: #ffffff; padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        border: 1px solid #f1f5f9; text-align: center; margin-bottom: 20px;
    }
    .res-label { font-size: 0.85rem; color: #64748b; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
    .res-price { font-size: 2.2rem; color: #1e293b; font-weight: 800; margin: 10px 0; }
    
    .alerta-manual {
        background: #fff7ed; color: #9a3412; padding: 12px; border-radius: 10px;
        font-size: 0.85rem; font-weight: 700; border: 1px solid #ffedd5; margin: 15px 0;
    }

    .stButton>button {
        border-radius: 12px; font-weight: 700; background: #1e3a8a; color: white;
        border: none; height: 55px; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background: #2563eb; transform: scale(1.01); }
    </style>
""", unsafe_allow_html=True)

# 2. MOTOR DE LIMPIEZA MEJORADO
def limpiar_monto(texto, nombre_campo="campo"):
    if not texto:
        return 0.0
    texto = str(texto).replace('$', '').replace('₲', '').replace('Gs', '').replace('USD', '').strip()
    if '.' in texto and ',' in texto:
        if texto.rfind(',') > texto.rfind('.'):
            texto = texto.replace('.', '').replace(',', '.')
        else:
            texto = texto.replace(',', '')
    elif ',' in texto:
        if len(texto.split(',')[-1]) == 3:
            texto = texto.replace(',', '')
        else:
            texto = texto.replace(',', '.')
    elif '.' in texto:
        if len(texto.split('.')[-1]) == 3:
            texto = texto.replace('.', '')
    try:
        return float(texto)
    except:
        st.error(f"❌ Error en {nombre_campo}: solo se permiten números, puntos y comas.")
        return None

def formatear_guaranies(valor):
    return "{:,.0f}".format(round(valor)).replace(",", ".")

# 3. INTERFAZ DE USUARIO
st.title("🛡️ PrecioJusto PY")
st.markdown("<p style='color:#64748b; font-size:1.1rem; margin-top:-15px;'>Gestión de Reventa v3.6 Pro</p>", unsafe_allow_html=True)

with st.expander("📖 Guía de Funciones (Leer antes de usar)", expanded=False):
    st.markdown("""
    - **Cotización:** Ingresá el precio de tu cambista. El sistema NO es automático para evitar errores de costo.
    - **Protección (+1.5%):** Seguro por si la moneda sube antes de reponer stock.
    - **Precio LISTA:** Monto para Tarjeta o QR (Ya incluye comisión bancaria).
    - **Precio EFECTIVO:** Monto neto para SIPAP o Billetes.
    - **IVA 10%:** Si activás factura legal, se suma el 10% sobre la base imponible.
    """)

st.subheader("📦 1. Datos del producto")
c1, c2 = st.columns(2)
producto = c1.text_input("Nombre del producto", placeholder="Ej: iPhone 15 Pro Max")
variante = c2.text_input("Variante / Modelo", value="Nuevo en caja")

st.subheader("💱 2. Costo y Cotización")
ca, cb = st.columns(2)
moneda = ca.selectbox("Moneda de compra", ["USD", "BRL", "ARS", "PYG"])
costo_raw = ca.text_input(f"Costo en {moneda} (Podés pegar montos)", value="0")

sug = {"USD": "8050", "BRL": "1450", "ARS": "9.5", "PYG": "1"}
tasa_raw = cb.text_input("Cotización del cambista (₲)", value=sug[moneda])
st.markdown(f'<div class="alerta-manual">⚠️ AVISO: El valor de {moneda} es MANUAL. Verifique con su proveedor.</div>', unsafe_allow_html=True)

st.subheader("📈 3. Logística y Ganancia")
l1, l2 = st.columns(2)
flete_raw = l1.text_input("Flete / Envío en Guaraníes", value="0")
gan_tipo = l2.radio("Método de ganancia", ["Porcentaje %", "Monto Fijo ₲"], horizontal=True)
gan_raw = l2.text_input("Tu Ganancia (Número o %)", value="15")

st.subheader("🛡️ 4. Ajustes de Seguridad")
p1, p2 = st.columns(2)
is_iva = p1.toggle("Incluir Factura Legal (IVA 10%)")
p_cambio = p1.toggle("Activar Protección Dólar (+1.5%)", value=True)
tipo_pago = p2.selectbox("Medio de pago del cliente", ["Efectivo / SIPAP", "Tarjeta de Crédito (3.3%)", "Débito / QR (2.2%)"])

# 4. CÁLCULOS Y RESULTADOS (CORREGIDO)
if st.button("🚀 GENERAR PRESUPUESTO", type="primary"):
    c = limpiar_monto(costo_raw, "el costo")
    t = limpiar_monto(tasa_raw, "la cotización")
    f = limpiar_monto(flete_raw, "el flete")
    g = limpiar_monto(gan_raw, "la ganancia")
    
    if None in (c, t, f, g):
        st.stop()
    
    # Validaciones adicionales
    if c <= 0:
        st.error("❌ El costo debe ser mayor a cero.")
        st.stop()
    if moneda != "PYG" and t <= 0:
        st.error("❌ La cotización debe ser mayor a cero.")
        st.stop()
    
    # Cálculos según práctica comercial paraguaya
    costo_base = c * t
    costo_con_proteccion = costo_base * 1.015 if p_cambio else costo_base
    subtotal_con_flete = costo_con_proteccion + f
    
    if gan_tipo == "Porcentaje %":
        utilidad = subtotal_con_flete * (g / 100)
    else:
        utilidad = g
    
    base_imponible = subtotal_con_flete + utilidad
    precio_efectivo = base_imponible * 1.10 if is_iva else base_imponible
    
    com_map = {"Efectivo / SIPAP": 0.0, "Tarjeta de Crédito (3.3%)": 3.3, "Débito / QR (2.2%)": 2.2}
    comision = com_map[tipo_pago]
    precio_lista = precio_efectivo / (1 - comision/100) if comision > 0 else precio_efectivo

    # Mostrar resultados
    st.markdown("---")
    r1, r2 = st.columns(2)
    r1.markdown(f"""
        <div class="result-card">
            <div class="res-label">💳 PRECIO LISTA (Tarjeta/QR)</div>
            <div class="res-price">{formatear_guaranies(precio_lista)} ₲</div>
            <small>Incluye comisión del {comision}%</small>
        </div>
    """, unsafe_allow_html=True)
    r2.markdown(f"""
        <div class="result-card" style="border-top:6px solid #10b981;">
            <div class="res-label">💰 PRECIO EFECTIVO</div>
            <div class="res-price" style="color:#10b981;">{formatear_guaranies(precio_efectivo)} ₲</div>
            <small>{"Incluye IVA 10%" if is_iva else "Sin Factura / Sin IVA"}</small>
        </div>
    """, unsafe_allow_html=True)

    # Desglose detallado
    with st.expander("📊 Ver desglose detallado de costos"):
        st.write(f"**Costo Producto:** {formatear_guaranies(costo_base)} ₲")
        if p_cambio:
            proteccion = costo_con_proteccion - costo_base
            st.write(f"**Protección (1.5%):** {formatear_guaranies(proteccion)} ₲")
        st.write(f"**Flete:** {formatear_guaranies(f)} ₲")
        st.write(f"**Subtotal (costo+protección+flete):** {formatear_guaranies(subtotal_con_flete)} ₲")
        st.write(f"**Ganancia neta:** {formatear_guaranies(utilidad)} ₲")
        st.write(f"**Base imponible (sin IVA):** {formatear_guaranies(base_imponible)} ₲")
        if is_iva:
            iva_calculado = precio_efectivo - base_imponible
            st.write(f"**IVA 10% (sobre la base):** {formatear_guaranies(iva_calculado)} ₲")

    # Botón WhatsApp
    msg = f"📝 *PRESUPUESTO*\n📦 *Item:* {producto} {variante}\n💳 *Lista:* {formatear_guaranies(precio_lista)} Gs.\n💵 *Efectivo:* {formatear_guaranies(precio_efectivo)} Gs.\n_PrecioJusto PY_"
    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📲 ENVIAR POR WHATSAPP</div></a>', unsafe_allow_html=True)

    # Botón para nueva operación
    if st.button("🧹 NUEVA OPERACIÓN"):
        st.rerun()

    # Scroll automático
    st.markdown("""<script>window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });</script>""", unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:50px;'>PRECIOJUSTO PY v3.6 | Optimizado para Celulares | IVA correcto | Ganancia sobre subtotal</p>", unsafe_allow_html=True)
