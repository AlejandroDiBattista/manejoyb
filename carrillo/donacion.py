import streamlit as st
import qrcode
from io import BytesIO
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fpdf import FPDF  # Asegúrate de que sea fpdf2
import os

# Configurar la base de datos
DATABASE_URL = "sqlite:///donaciones.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Definir el modelo de datos
class Donacion(Base):
    __tablename__ = 'donaciones'
    id = Column(Integer, primary_key=True, autoincrement=True)
    categoria = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    url = Column(String, nullable=False)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def save_data(categoria, monto, url):
    # Guardar los datos de una nueva donación en la base de datos
    donacion = Donacion(categoria=categoria, monto=monto, url=url)
    with Session() as session:
        session.add(donacion)
        session.commit()

def generar_qr(url, monto):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white').convert("RGB")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    buffered.seek(0)
    return buffered  # Retorna el objeto BytesIO

def generar_pdf(datos, montos):
    pdf = FPDF()
    pdf.add_page()
    
    # Agregar título grande y centrado
    pdf.set_font("Helvetica", 'B', 24)
    pdf.cell(0, 15, txt="Hospital Carrillo - Donaciones", ln=True, align='C')
    pdf.ln(10)  # Espacio después del título
    
    # Obtener el ancho total de la página
    page_width = pdf.w  # Ancho total de la página en puntos
    
    # Calcular el margen y el ancho de las columnas automáticamente
    # Basado en la relación 3M + 2C = W, donde M = W/7 y C = 2W/7
    margin = page_width / 7
    column_width = 2 * page_width / 7
    space_between = margin  # El espacio entre columnas es igual al margen
    
    # Coordenadas para la columna izquierda y derecha
    x_left = margin
    y_left = pdf.get_y()
    x_right = margin + column_width + space_between
    y_right = pdf.get_y()
    
    categorias = ['Mercado Libre', 'Modo']
    
    for categoria in categorias:
        if categoria == 'Mercado Libre':
            x = x_left
            y = y_left
        else:
            x = x_right
            y = y_right
        
        # Título de la categoría
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", 'B', 16)
        pdf.multi_cell(column_width, 10, txt=categoria, align='C')
        y += 12  # Espacio después del título
        
        # Resetear la fuente para los montos
        pdf.set_font("Helvetica", size=12)
        
        for monto, url in zip(montos, datos[categoria]):
            if monto > 0 and url:
                # Agregar el monto
                pdf.set_xy(x, y)
                pdf.multi_cell(column_width, 8, txt=f"Doná ${monto:.0f}", align='L')
                y += 8  # Espacio después del texto
                
                # Agregar el QR
                pdf.set_xy(x, y)
                qr_img = generar_qr(url, monto)
                # Asegúrate de que el ancho del QR no exceda el ancho de la columna
                qr_size = min(40, column_width - 10)  # Deja un pequeño margen
                pdf.image(qr_img, x=x, y=y, w=qr_size, h=qr_size, type='PNG')
                y += qr_size + 5  # Espacio después del QR (altura del QR + espacio)
        
        # Actualizar la posición 'y' de cada columna
        if categoria == 'Mercado Libre':
            y_left = y
        else:
            y_right = y
    
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

def main():
    # Configurar la página principal de la aplicación
    st.set_page_config(page_title="Generador de Códigos QR", layout="wide")
    st.markdown("# :rainbow[Generador de Códigos QR para Donaciones]")

    # Lista de diccionarios que contiene categorías, enlaces de cobro y montos por defecto
    categorias_info = [
        {"categoria": "Mercado Libre", "link_cobro": "https://mpago.la/22u2j9Y", "montos_default": [1000.00, 2000.00, 3000.00]},
        {"categoria": "Modo", "link_cobro": "https://www.modo.com.ar/coupon/?id=41PQqxwezOO5HM48WwkXyE", "montos_default": [1000.00, 2000.00, 3000.00]}
    ]

    # Ingresar los montos una sola vez
    montos = []
    st.sidebar.header("Montos a donar")
    etiquetas = ["Mínimo", "Agradecido", "Generoso"]
    
    # Crear tres columnas para los montos
    columnas = st.sidebar.columns(3)
    
    for i, (etiqueta, columna) in enumerate(zip(etiquetas, columnas), start=1):
        with columna:
            monto = st.number_input(
                f"{etiqueta}",
                min_value=0.0,  # Valor mínimo permitido
                step=100.0,  # Paso de incremento
                format="%.0f",  # Formato del número
                value=categorias_info[0]["montos_default"][i-1],  # Valor por defecto
                key=f"monto_{i}"
            )
            montos.append(monto)

    # Ingresar las URLs para cada categoría en la barra lateral
    datos = {info["categoria"]: [] for info in categorias_info}
    for info in categorias_info:
        categoria = info["categoria"]
        link_cobro = info["link_cobro"]
        with st.sidebar.expander(f"{categoria.title()}", expanded=True):
            for i, monto in enumerate(montos, start=1):
                url = st.text_input(
                    f"Ingrese URL Donar ${monto:.2f}",
                    key=f"{categoria}_url_{i}",
                    value=link_cobro
                )
                if url:
                    separator = '&' if '?' in url else '?'
                    url = f"{url}{separator}monto={monto:.2f}"
                datos[categoria].append(url)

    # Botón para guardar todos los datos
    if st.sidebar.button("Guardar Todo"):
        # Guardar cada donación en la base de datos
        for info in categorias_info:
            categoria = info["categoria"]
            for i, monto in enumerate(montos):
                url = datos[categoria][i]
                if url:
                    save_data(categoria, monto, url)
        st.success("Todos los datos han sido guardados exitosamente.")

    # Verificar que todas las URLs estén ingresadas
    for info in categorias_info:
        categoria = info["categoria"]
        for idx, url in enumerate(datos[categoria], start=1):
            if not url:
                st.warning(f"Por favor, ingresa la URL {idx} para {categoria}.")
                return

    # Crear dos columnas en la pantalla principal para mostrar los QR
    col_ml, col_modo = st.columns(2)

    def mostrar_qr(categoria, columna):
        # Mostrar los códigos QR en la columna correspondiente
        with columna:
            st.header(categoria)
            for monto, url in zip(montos, datos[categoria]):
                if monto > 0 and url:
                    buffer = generar_qr(url, monto)
                    st.image(buffer, width=300)
                    st.markdown(f"## Doná ${monto:.0f}\n---")

    # Mostrar los QR para cada categoría
    mostrar_qr("Mercado Libre", col_ml)
    mostrar_qr("Modo", col_modo)

    # Botón para generar y descargar el PDF
    if st.button("Generar PDF"):
        pdf_output = generar_pdf(datos, montos)
        st.download_button(
            label="Descargar PDF",
            data=pdf_output,
            file_name="donaciones.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()