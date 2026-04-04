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
    </style>
    <script>
    // Auto-scroll al resultado después de generar presupuesto
    function scrollToResults() {
        const results = document.querySelector('.result-card');
        if(results) results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    </script>
""", unsafe_allow_html=True)

# =============================================
# FUNCIONES DE LIMPIEZA Y VALIDACIÓN
# =============================================
def es_numero_valido(texto):
    """Verifica si el texto contiene solo caracteres numéricos, puntos, comas y signos de moneda."""
    if not texto:
        return False
    # Permite dígitos, punto, coma, espacio, símbolos de moneda, signo menos
    patron = re.compile(r'^[\d\.,\s\-\$₲Gs%]+$')
    return bool(patron.match(texto))

def limpiar_monto(texto):
    """Convierte texto con formato monetario paraguayo (ej: 1.500,50 o 1500,5) a float."""
    if not texto:
        return 0.0
    # Si contiene letras no permitidas, retorna None para indicar error
    if not es_numero_valido(texto):
        return None
    
    # Eliminar símbolos de moneda y espacios
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
        return None

def formatear_guaranies(valor):
    return "{:,.0f}".format(round(valor)).replace(",", ".")

# =============================================
# LÓGICA DE CÁLCULO
# =============================================
def calcular_precios(costo_ext, tasa, flete, ganancia_valor, ganancia_tipo,
                     proteccion_cambio, emitir_factura_con_iva, comision_porc, moneda):
    costo_base_gs = costo_ext * tasa
    if proteccion_cambio:
        costo_con_proteccion = costo_base_gs * 1.015
    else:
        costo_con_proteccion = costo_base_gs
    
    subtotal = costo_con_proteccion + flete
    
    if ganancia_tipo == "Porcentaje %":
        ganancia_gs = subtotal * (ganancia_valor / 100)
    else:
        ganancia_gs = ganancia_valor
    
    base_imponible = subtotal + ganancia_gs
    
    if emitir_factura_con_iva:
        iva_gs = base_imponible * 0.10
        precio_efectivo = base_imponible + iva_gs
    else:
        iva_gs = 0
        precio_efectivo = base_imponible
    
    if comision_porc > 0:
        precio_lista = precio_efectivo / (1 - comision_porc/100)
    else:
        precio_lista = precio_efectivo
    
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
    else:
        desglose["IVA"] = "No incluido (sin factura legal)"
    
    desglose[f"Comisión bancaria ({comision_porc}%)"] = "Aplicada al precio con IVA" if emitir_factura_con_iva else "Aplicada al precio neto"
    desglose["💰 PRECIO EFECTIVO (SIPAP / Billetes)"] = formatear_guaranies(precio_efectivo)
    desglose["💳 PRECIO LISTA (Tarjeta / QR)"] = formatear_guaranies(precio_lista)
    
    return precio_efectivo, precio_lista, desglose

# =============================================
# INTERFAZ DE USUARIO
# =============================================
st.title("🛡️ PrecioJusto PY")
st.markdown("<p style='color:#64748b; font-size:1.1rem; margin-top:-15px;'>La calculadora profesional para revendedores paraguayos</p>", unsafe_allow_html=True)

with st.expander("📖 Guía para Paraguay (leer antes de usar)", expanded=False):
    st.markdown("""
    **🇵🇾 Reglas del mercado local:**
    - **Cotización manual:** Ingresá el precio real de tu **cambista** (ej: 8.050 ₲ por 1 USD).
    - **Protección cambiaria (+1.5%):** Seguro por si el dólar sube antes de reponer stock.
    - **Precio EFECTIVO:** Es el monto que **pagará el cliente** en SIPAP, transferencia o billetes.
    - **Precio LISTA:** Es el monto para pagar con **tarjeta o QR** (incluye la comisión bancaria).
    
    **🔍 Manejo del IVA (corregido):**
    - Si **NO activás** "Factura Legal", el precio efectivo **no incluye IVA**. (Venta informal)
    - Si **activás** "Factura Legal", el precio efectivo **ya incluye el 10% de IVA**.
    - **Ejemplo:** Neto 4.932.000 ₲ → IVA 493.200 ₲ → Total con factura 5.425.200 ₲.
    
    **📝 Solo números:** En los campos de dinero usá solo números, puntos y comas (ej: 1.500,50 o 1500.50). No pongas letras.
    """)

# Formulario para evitar el "Enter" que recarga la página
with st.form(key="calculadora_form"):
    st.subheader("📦 1. Datos del producto")
    col1, col2 = st.columns(2)
    producto = col1.text_input("Nombre del producto", placeholder="Ej: iPhone 15 Pro")
    variante = col2.text_input("Variante / Modelo", value="Nuevo en caja")
    
    st.subheader("💱 2. Costo y cotización del cambista")
    col_a, col_b = st.columns(2)
    moneda = col_a.selectbox("Moneda de compra", ["USD", "BRL", "ARS", "PYG"])
    costo_raw = col_a.text_input(f"Costo en {moneda} (solo números)", value="0")
    
    sugerencias = {"USD": "8050", "BRL": "1450", "ARS": "9.5", "PYG": "1"}
    tasa_raw = col_b.text_input("Cotización del cambista (₲ por 1 unidad) - solo números", value=sugerencias[moneda])
    
    st.subheader("📈 3. Logística y ganancia")
    col_l1, col_l2 = st.columns(2)
    flete_raw = col_l1.text_input("Flete / Envío (₲) - solo números", value="0")
    
    ganancia_tipo = col_l2.radio("Método de ganancia", ["Porcentaje %", "Monto Fijo ₲"], horizontal=True)
    ganancia_raw = col_l2.text_input("Ganancia (solo números)", value="15")
    
    st.subheader("🛡️ 4. Ajustes de seguridad y facturación")
    col_p1, col_p2 = st.columns(2)
    emitir_factura = col_p1.toggle("Incluir Factura Legal (IVA 10%)")
    proteccion_cambio = col_p1.toggle("Activar Protección Dólar (+1.5%)", value=True)
    
    tipo_pago = col_p2.selectbox("Medio de pago del cliente", 
                                 ["Efectivo / SIPAP", "Tarjeta de Crédito (3.3%)", "Débito / QR (2.2%)"])
    
    # Botón dentro del formulario
    submitted = st.form_submit_button("🚀 GENERAR PRESUPUESTO", type="primary")

# Procesamiento fuera del formulario
if submitted:
    error = False
    # Validar que los campos no tengan letras
    costo = limpiar_monto(costo_raw)
    if costo is None:
        st.error("❌ El costo contiene letras o símbolos no válidos. Usá solo números, puntos y comas.")
        error = True
    
    tasa = limpiar_monto(tasa_raw)
    if tasa is None and moneda != "PYG":
        st.error("❌ La cotización contiene letras o símbolos no válidos. Usá solo números, puntos y comas.")
        error = True
    
    flete = limpiar_monto(flete_raw)
    if flete is None:
        st.error("❌ El flete contiene letras o símbolos no válidos. Usá solo números, puntos y comas.")
        error = True
    
    ganancia_valor = limpiar_monto(ganancia_raw)
    if ganancia_valor is None:
        st.error("❌ La ganancia contiene letras o símbolos no válidos. Usá solo números, puntos y comas.")
        error = True
    
    if not error:
        try:
            if costo <= 0:
                st.error("❌ El costo del producto debe ser mayor a cero.")
            elif tasa <= 0 and moneda != "PYG":
                st.error("❌ La cotización del cambista debe ser mayor a cero.")
            elif ganancia_valor < 0:
                st.error("❌ La ganancia no puede ser negativa.")
            else:
                comision_map = {
                    "Efectivo / SIPAP": 0.0,
                    "Tarjeta de Crédito (3.3%)": 3.3,
                    "Débito / QR (2.2%)": 2.2
                }
                comision = comision_map[tipo_pago]
                
                precio_efectivo, precio_lista, desglose = calcular_precios(
                    costo_ext=costo, tasa=tasa, flete=flete,
                    ganancia_valor=ganancia_valor, ganancia_tipo=ganancia_tipo,
                    proteccion_cambio=proteccion_cambio, emitir_factura_con_iva=emitir_factura,
                    comision_porc=comision, moneda=moneda
                )
                
                st.markdown("---")
                col_r1, col_r2 = st.columns(2)
                col_r1.markdown(f"""
                    <div class="result-card" id="resultado-lista">
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
                
                mensaje = f"""📝 *PRESUPUESTO PRECIOJUSTO PY*
🇵🇾 *Producto:* {producto} {variante}
💳 *Precio Lista (Tarjeta/QR):* {formatear_guaranies(precio_lista)} ₲
💰 *Precio Efectivo:* {formatear_guaranies(precio_efectivo)} ₲
{"✅ *Incluye IVA 10% (factura legal)*" if emitir_factura else "❌ *Sin IVA (sin factura)*"}

_Generado con PrecioJusto PY_"""
                
                url_whatsapp = f"https://wa.me/?text={urllib.parse.quote(mensaje)}"
                st.markdown(f'<a href="{url_whatsapp}" target="_blank" style="text-decoration:none;">'
                            f'<div style="background-color:#25d366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">'
                            f'📲 ENVIAR POR WHATSAPP</div></a>', unsafe_allow_html=True)
                
                # Auto-scroll con JavaScript
                st.markdown("""
                    <script>
                        const element = document.querySelector('.result-card');
                        if(element) element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    </script>
                """, unsafe_allow_html=True)
                
                if st.button("🧹 NUEVA OPERACIÓN"):
                    st.rerun()
        except Exception as e:
            st.error(f"⚠️ Error inesperado: {str(e)}. Revisá los datos.")
    else:
        st.info("💡 Corregí los campos marcados e intentá de nuevo.")

st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:50px;'>🇵🇾 PRECIOJUSTO PY v3.2 - Validación de números | Scroll automático</p>", unsafe_allow_html=True)
