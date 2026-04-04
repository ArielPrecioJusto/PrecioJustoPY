import streamlit as st
import urllib.parse
import math

# 1. CONFIGURACIÓN Y CAPA DE PRIVACIDAD TOTAL
st.set_page_config(page_title="PrecioJusto PY", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
    /* ELIMINAR TODA LA BARRA SUPERIOR, MENÚS Y LOGOS DE GITHUB */
    header, footer, .stAppDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    
    /* OCULTAR BOTONES DE + Y - EN LOS NUMBER INPUTS PARA QUE NO MOLESTEN EN EL CELU */
    div[data-baseweb="input"] > div[data-testid="stNumberInputStepUp"] {display: none !important;}
    div[data-baseweb="input"] > div[data-testid="stNumberInputStepDown"] {display: none !important;}
    input[type="number"] { -moz-appearance: textfield; }
    
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #fcfdfe; }
    
    .result-card {
        background: #ffffff; padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        border: 1px solid #f1f5f9; text-align: center; margin-bottom: 20px;
    }
    .res-label { font-size: 0.85rem; color: #64748b; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
    .res-price { font-size: 2.1rem; color: #1e293b; font-weight: 800; margin: 10px 0; }
    
    .alerta-manual {
        background: #fff7ed; color: #9a3412; padding: 12px; border-radius: 10px;
        font-size: 0.85rem; font-weight: 700; border: 1px solid #ffedd5; margin: 15px 0; text-align: center;
    }
    
    .stButton>button {
        border-radius: 12px; font-weight: 700; background: #1e3a8a; color: white;
        border: none; height: 55px; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background: #2563eb; transform: scale(1.01); }
    </style>
""", unsafe_allow_html=True)

# 2. FUNCIONES MATEMÁTICAS (REDONDEO 500 Gs)
def redondear_500(monto):
    """Redondea hacia arriba al 500 o 000 más cercano para no dar vueltos chicos."""
    return math.ceil(monto / 500) * 500

def formatear(valor):
    return "{:,.0f}".format(valor).replace(",", ".")

# 3. INTERFAZ Y GUÍA
st.title("🛡️ PrecioJusto PY")
st.markdown("<p style='color:#64748b; font-size:1.1rem; margin-top:-15px;'>Herramienta Privada de Cotización</p>", unsafe_allow_html=True)

# Recuperamos la guía que pediste
with st.expander("📖 Guía de Funciones (Leer antes de usar)", expanded=False):
    st.markdown("""
    - **Protección (+1.5%):** Seguro por si el dólar sube antes de reponer stock.
    - **Precio LISTA:** Monto para Tarjeta o QR (Ya incluye comisión bancaria).
    - **Precio EFECTIVO:** Monto neto para SIPAP o Billetes.
    - *Todos los precios finales se redondean al 500 más cercano.*
    """)

st.subheader("📦 1. Datos del producto")
c1, c2 = st.columns(2)
prod = c1.text_input("Nombre del producto", placeholder="Ej: Pantalla iPhone 13")
var = c2.text_input("Variante / Detalles", value="Original")

st.subheader("💱 2. Costo y Cotización")
ca, cb = st.columns(2)
moneda = ca.selectbox("Moneda de compra", ["USD", "BRL", "ARS", "PYG"])

# Número directo: En el celular te abre el teclado numérico.
costo = ca.number_input(f"Costo en {moneda}", min_value=0.0, format="%.2f")

sug_tasas = {"USD": 8050.0, "BRL": 1450.0, "ARS": 9.5, "PYG": 1.0}
tasa = cb.number_input("Cotización (₲)", min_value=0.0, value=sug_tasas[moneda], format="%.0f")

# Recuperamos la alerta naranja
st.markdown(f'<div class="alerta-manual">⚠️ AVISO: Cotización de {moneda} es MANUAL. Revisá antes de seguir.</div>', unsafe_allow_html=True)

st.subheader("📈 3. Logística y Ganancia")
l1, l2 = st.columns(2)
flete = l1.number_input("Flete / Envío (₲)", min_value=0.0, format="%.0f")
gan_tipo = l2.radio("Método de ganancia", ["Porcentaje %", "Monto Fijo ₲"], horizontal=True)
gan_val = l2.number_input("Tu Ganancia", min_value=0.0, value=15.0 if gan_tipo=="Porcentaje %" else 150000.0)

st.subheader("🛡️ 4. Ajustes Finales")
p1, p2 = st.columns(2)
is_iva = p1.toggle("Incluir Factura Legal (IVA 10%)")
p_cambio = p1.toggle("Protección Dólar (+1.5%)", value=True)
pago = p2.selectbox("Medio de Pago del Cliente", ["Efectivo / SIPAP", "Tarjeta de Crédito (3.3%)", "Débito / QR (2.2%)"])

# 4. LÓGICA DE CÁLCULO
if st.button("🚀 GENERAR PRESUPUESTO", type="primary"):
    if costo > 0 and tasa > 0:
        # Cálculos de costo real
        costo_base_gs = costo * tasa
        costo_prot_gs = costo_base_gs * 1.015 if p_cambio else costo_base_gs
        
        # Utilidad (Ahora sí, calculada sobre el costo protegido)
        utilidad = (costo_prot_gs * (gan_val / 100)) if gan_tipo == "Porcentaje %" else gan_val
        
        # Base y Efectivo (Con IVA sumado 10%)
        base_neta = costo_prot_gs + flete + utilidad
        iva_monto = base_neta * 0.10 if is_iva else 0
        precio_efectivo = redondear_500(base_neta + iva_monto)
        
        # Lista (Tarjeta/QR)
        com_map = {"Efectivo / SIPAP": 0.0, "Tarjeta de Crédito (3.3%)": 3.3, "Débito / QR (2.2%)": 2.2}
        comision_pct = com_map[pago]
        precio_lista = redondear_500(precio_efectivo / (1 - comision_pct / 100)) if comision_pct > 0 else precio_efectivo

        # DESPLIEGUE VISUAL
        st.markdown("---")
        r1, r2 = st.columns(2)
        r1.markdown(f'<div class="result-card"><div class="res-label">💳 PRECIO LISTA</div><div class="res-price">{formatear(precio_lista)} ₲</div><small>Tarjeta / QR ({comision_pct}%)</small></div>', unsafe_allow_html=True)
        r2.markdown(f'<div class="result-card" style="border-top:6px solid #10b981;"><div class="res-label">💰 EFECTIVO / SIPAP</div><div class="res-price" style="color:#10b981;">{formatear(precio_efectivo)} ₲</div><small>{"IVA 10% Incluido" if is_iva else "Sin Factura / Neto"}</small></div>', unsafe_allow_html=True)

        # RECUPERAMOS EL DESGLOSE DETALLADO
        with st.expander("📊 Ver desglose detallado de costos"):
            st.write(f"**Costo Producto:** {formatear(costo_base_gs)} ₲")
            if p_cambio: st.write(f"**Protección (1.5%):** {formatear(costo_prot_gs - costo_base_gs)} ₲")
            st.write(f"**Flete:** {formatear(flete)} ₲")
            st.write(f"**Ganancia Neta:** {formatear(utilidad)} ₲")
            if is_iva: st.write(f"**IVA (10%):** {formatear(iva_monto)} ₲")

        # WHATSAPP CORTO Y CON FORMATO
        var_text = f" ({var})" if var else ""
        msg = f"📝 *PRESUPUESTO*\n📦 *{prod}{var_text}*\n\n💰 *Efectivo / SIPAP:* {formatear(precio_efectivo)} ₲\n💳 *Tarjeta / QR:* {formatear(precio_lista)} ₲\n\n_Generado por PrecioJusto PY_"
        st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📲 ENVIAR POR WHATSAPP</div></a>', unsafe_allow_html=True)

        st.markdown("""<script>window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });</script>""", unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:50px;'>Versión Final Pro | Uso Exclusivo</p>", unsafe_allow_html=True)
