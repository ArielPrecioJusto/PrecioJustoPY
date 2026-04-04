import streamlit as st
import urllib.parse
import re

# =============================================
# CONFIGURACIÓN Y ESTILO (PARAGUAYO)
# =============================================
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
    
    .guia-box {
        background: #f0f7ff; padding: 20px; border-radius: 15px;
        border-left: 6px solid #2563eb; margin-bottom: 25px; color: #1e3a8a;
    }
    .guia-box h4 { margin-top: 0; color: #1e3a8a; font-size: 1.1rem; }
    .guia-box p { font-size: 0.9rem; margin-bottom: 8px; line-height: 1.4; }

    .stButton>button {
        border-radius: 12px; font-weight: 700; background: #1e3a8a; color: white;
        border: none; height: 55px; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background: #2563eb; transform: scale(1.01); }
    
    .alerta-manual {
        background: #fff7ed; color: #9a3412; padding: 12px; border-radius: 10px;
        font-size: 0.85rem; font-weight: 700; border: 1px solid #ffedd5; margin: 15px 0;
    }
    .detalle-box {
        background: #f8fafc; border-radius: 16px; padding: 15px; margin-top: 20px;
        border-left: 4px solid #2563eb; font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================
# FUNCIONES DE LIMPIEZA (FORMATO PARAGUAYO)
# =============================================
def limpiar_monto(texto):
    """Convierte texto con formato monetario paraguayo (ej: 1.500,50 o 1500,5) a float."""
    if not texto:
        return 0.0
    texto = texto.replace('$', '').replace('₲', '').replace('Gs', '').replace('USD', '').replace('BRL', '').replace('ARS', '').strip()
    
    if '.' in texto and ',' in texto:
        if texto.rfind(',') > texto.rfind('.'):
            texto = texto.replace('.', '').replace(',', '.')
        else:
            texto = texto.replace(',', '')
    elif ',' in texto:
        partes = texto.split(',')
        if len(partes[-1]) == 3:
            texto = texto.replace(',', '')
        else:
            texto = texto.replace(',', '.')
    elif '.' in texto:
        partes = texto.split('.')
        if len(partes[-1]) == 3:
            texto = texto.replace('.', '')
    try:
        return float(texto)
    except:
        return 0.0

def formatear_guaranies(valor):
    """Formatea un número con separador de miles (punto) y sin decimales, estilo Paraguay."""
    return "{:,.0f}".format(round(valor)).replace(",", ".")

# =============================================
# LÓGICA DE CÁLCULO (CON IVA CORREGIDO)
# =============================================
def calcular_precios(costo_ext, tasa, flete, ganancia_valor, ganancia_tipo,
                     proteccion_cambio, emitir_factura_con_iva, comision_porc, moneda):
    """
    Retorna (precio_efectivo_final, precio_lista_final, desglose_dict)
    
    IMPORTANTE:
    - Si emitir_factura_con_iva = True, el precio efectivo final incluye IVA (es el total que paga el cliente).
    - La base imponible (neto sin IVA) es lo que el revendedor realmente recibe después de pagar el IVA a DNIT.
    """
    # 1. Costo base en guaraníes
    costo_base_gs = costo_ext * tasa
    
    # 2. Protección cambiaria (+1.5% sobre costo base)
    if proteccion_cambio:
        costo_con_proteccion = costo_base_gs * 1.015
    else:
        costo_con_proteccion = costo_base_gs
    
    # 3. Subtotal (costo + flete)
    subtotal = costo_con_proteccion + flete
    
    # 4. Ganancia (sobre subtotal)
    if ganancia_tipo == "Porcentaje %":
        ganancia_gs = subtotal * (ganancia_valor / 100)
    else:
        ganancia_gs = ganancia_valor
    
    # Base imponible (neto sin IVA) = lo que el revendedor necesita recuperar
    base_imponible = subtotal + ganancia_gs
    
    # 5. Precio efectivo final (lo que paga el cliente)
    if emitir_factura_con_iva:
        # Se suma el 10% de IVA al neto
        iva_gs = base_imponible * 0.10
        precio_efectivo = base_imponible + iva_gs
    else:
        # Sin factura, no hay IVA
        iva_gs = 0
        precio_efectivo = base_imponible
    
    # 6. Precio lista (con comisión bancaria sobre el precio efectivo)
    if comision_porc > 0:
        precio_lista = precio_efectivo / (1 - comision_porc/100)
    else:
        precio_lista = precio_efectivo
    
    # Desglose detallado (en español paraguayo)
    desglose = {
        "Costo producto (moneda original)": f"{costo_ext:,.2f} {moneda}",
        "Cotización del cambista": f"{tasa:,.2f} ₲",
        "Costo base en guaraníes": formatear_guaranies(costo_base_gs),
        "Protección cambiaria (+1.5%)": "Sí" if proteccion_cambio else "No",
        "Costo con protección": formatear_guaranies(costo_con_proteccion),
        "Flete / Envío": formatear_guaranies(flete),
        "Subtotal (costo + flete)": formatear_guaranies(subtotal),
        f"Ganancia ({ganancia_tipo})": formatear_guaranies(ganancia_gs),
        "Base imponible (neto sin IVA)": formatear_guaranies(base_imponible),
    }
    
    if emitir_factura_con_iva:
        desglose["IVA 10% (sobre el neto)"] = formatear_guaranies(iva_gs)
        desglose["Total con IVA (factura legal)"] = formatear_guaranies(precio_efectivo)
        desglose["Nota"] = "El IVA se calcula como el 10% del neto. El precio final incluye el impuesto."
    else:
        desglose["IVA"] = "No incluido (sin factura legal)"
    
    desglose[f"Comisión bancaria ({comision_porc}%)"] = "Aplicada al precio con IVA" if emitir_factura_con_iva else "Aplicada al precio neto"
    desglose["💰 PRECIO EFECTIVO (SIPAP / Billetes)"] = formatear_guaranies(precio_efectivo)
    desglose["💳 PRECIO LISTA (Tarjeta / QR)"] = formatear_guaranies(precio_lista)
    
    return precio_efectivo, precio_lista, desglose

# =============================================
# INTERFAZ DE USUARIO (MERCADO PARAGUAYO)
# =============================================
st.title("🛡️ PrecioJusto PY")
st.markdown("<p style='color:#64748b; font-size:1.1rem; margin-top:-15px;'>La calculadora profesional para revendedores paraguayos</p>", unsafe_allow_html=True)

# Guía colapsable con explicación clara del IVA
with st.expander("📖 Guía para Paraguay (leer antes de usar)", expanded=False):
    st.markdown("""
    **🇵🇾 Reglas del mercado local:**
    - **Cotización manual:** Ingresá el precio real de tu **cambista** (ej: 8.050 ₲ por 1 USD).
    - **Protección cambiaria (+1.5%):** Seguro por si el dólar sube antes de reponer stock.
    - **Precio EFECTIVO:** Es el monto que **pagará el cliente** en SIPAP, transferencia o billetes.
    - **Precio LISTA:** Es el monto para pagar con **tarjeta o QR** (incluye la comisión bancaria).
    
    **🔍 Manejo del IVA (corregido):**
    - Si **NO activás** "Factura Legal", el precio efectivo **no incluye IVA**. (Venta informal)
    - Si **activás** "Factura Legal", el precio efectivo **ya incluye el 10% de IVA**. En el desglose verás:
        - *Base imponible*: lo que realmente recibís (neto).
        - *IVA*: el 10% de esa base.
        - *Total con IVA*: el precio final que paga el cliente.
    - **Ejemplo:** Si tu neto es 4.932.000 ₲, el IVA es 493.200 ₲ y el total con factura es 5.425.200 ₲.
    """)

# --- SECCIÓN 1: DATOS DEL PRODUCTO ---
st.subheader("📦 1. Datos del producto")
col1, col2 = st.columns(2)
producto = col1.text_input("Nombre del producto", placeholder="Ej: iPhone 15 Pro")
variante = col2.text_input("Variante / Modelo", value="Nuevo en caja")

# --- SECCIÓN 2: COSTO Y COTIZACIÓN (CAMBISTA) ---
st.subheader("💱 2. Costo y cotización del cambista")
col_a, col_b = st.columns(2)
moneda = col_a.selectbox("Moneda de compra", ["USD", "BRL", "ARS", "PYG"])
costo_raw = col_a.text_input(f"Costo en {moneda} (podés pegar el número)", value="0")

sugerencias = {"USD": "8050", "BRL": "1450", "ARS": "9.5", "PYG": "1"}
tasa_raw = col_b.text_input("Cotización del cambista (₲ por 1 unidad)", value=sugerencias[moneda])

st.markdown(f'<div class="alerta-manual">⚠️ Importante: La cotización del {moneda} debe ser la que usas con tu cambista. No es automática.</div>', unsafe_allow_html=True)

# --- SECCIÓN 3: GASTOS Y GANANCIA ---
st.subheader("📈 3. Logística y ganancia")
col_l1, col_l2 = st.columns(2)
flete_raw = col_l1.text_input("Flete / Envío (₲)", value="0")

ganancia_tipo = col_l2.radio("Método de ganancia", ["Porcentaje %", "Monto Fijo ₲"], horizontal=True)
ganancia_raw = col_l2.text_input("Ganancia (porcentaje o monto fijo)", value="15")

# --- SECCIÓN 4: AJUSTES FINALES (IVA, PROTECCIÓN, COMISIÓN) ---
st.subheader("🛡️ 4. Ajustes de seguridad y facturación")
col_p1, col_p2 = st.columns(2)
emitir_factura = col_p1.toggle("Incluir Factura Legal (IVA 10%)", 
                               help="Activá si le darás factura con IVA al cliente. El precio final incluirá el impuesto.")
proteccion_cambio = col_p1.toggle("Activar Protección Dólar (+1.5%)", value=True, 
                                  help="Cubre una posible subida del dólar antes de reponer")

tipo_pago = col_p2.selectbox("Medio de pago del cliente", 
                             ["Efectivo / SIPAP", "Tarjeta de Crédito (3.3%)", "Débito / QR (2.2%)"],
                             help="Según el medio, se aplica la comisión bancaria correspondiente")

comision_map = {
    "Efectivo / SIPAP": 0.0,
    "Tarjeta de Crédito (3.3%)": 3.3,
    "Débito / QR (2.2%)": 2.2
}
comision = comision_map[tipo_pago]

# --- BOTÓN PRINCIPAL ---
if st.button("🚀 GENERAR PRESUPUESTO", type="primary"):
    try:
        costo = limpiar_monto(costo_raw)
        tasa = limpiar_monto(tasa_raw)
        flete = limpiar_monto(flete_raw)
        ganancia_valor = limpiar_monto(ganancia_raw)
        
        if costo <= 0:
            st.error("❌ El costo del producto debe ser mayor a cero.")
            st.stop()
        if tasa <= 0 and moneda != "PYG":
            st.error("❌ La cotización del cambista debe ser mayor a cero.")
            st.stop()
        if ganancia_valor < 0:
            st.error("❌ La ganancia no puede ser negativa.")
            st.stop()
        
        precio_efectivo, precio_lista, desglose = calcular_precios(
            costo_ext=costo,
            tasa=tasa,
            flete=flete,
            ganancia_valor=ganancia_valor,
            ganancia_tipo=ganancia_tipo,
            proteccion_cambio=proteccion_cambio,
            emitir_factura_con_iva=emitir_factura,
            comision_porc=comision,
            moneda=moneda
        )
        
        st.markdown("---")
        col_r1, col_r2 = st.columns(2)
        col_r1.markdown(f"""
            <div class="result-card">
                <div class="res-label">💳 PRECIO LISTA (Tarjeta/QR)</div>
                <div class="res-price">{formatear_guaranies(precio_lista)} ₲</div>
                <small>Incluye comisión del {comision}%</small>
            </div>
        """, unsafe_allow_html=True)
        
        col_r2.markdown(f"""
            <div class="result-card" style="border-top:6px solid #10b981;">
                <div class="res-label">💰 PRECIO EFECTIVO</div>
                <div class="res-price" style="color:#10b981;">{formatear_guaranies(precio_efectivo)} ₲</div>
                <small>{"Incluye IVA 10%" if emitir_factura else "Sin IVA (sin factura)"}</small>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📊 Ver desglose completo de cálculos"):
            for clave, valor in desglose.items():
                st.markdown(f"**{clave}:** {valor}")
        
        # Mensaje para WhatsApp con información clara del IVA
        mensaje = f"""📝 *PRESUPUESTO PRECIOJUSTO PY*
🇵🇾 *Producto:* {producto} {variante}
💳 *Precio Lista (Tarjeta/QR):* {formatear_guaranies(precio_lista)} ₲
💰 *Precio Efectivo:* {formatear_guaranies(precio_efectivo)} ₲
{"✅ *Incluye IVA 10% (factura legal)*" if emitir_factura else "❌ *Sin IVA (sin factura)*"}

_Generado con PrecioJusto PY - cálculos adaptados a Paraguay_"""
        
        url_whatsapp = f"https://wa.me/?text={urllib.parse.quote(mensaje)}"
        st.markdown(f'<a href="{url_whatsapp}" target="_blank" style="text-decoration:none;">'
                    f'<div style="background-color:#25d366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">'
                    f'📲 ENVIAR POR WHATSAPP</div></a>', unsafe_allow_html=True)
        
        if st.button("🧹 NUEVA OPERACIÓN"):
            st.rerun()
            
    except Exception as e:
        st.error(f"⚠️ Error en los datos: {str(e)}. Revisá que los montos sean números válidos (ej:0000000000 1.500,50).")
st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:50px;'>PrecioJusto PY</p>", unsafe_allow_html=True)
