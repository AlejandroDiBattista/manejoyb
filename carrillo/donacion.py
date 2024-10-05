import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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

# Crear la tabla en la base de datos
Base.metadata.create_all(engine)

# Crear una sesión
Session = sessionmaker(bind=engine)
session = Session()

def save_data(categoria, monto, url):
    nueva_donacion = Donacion(categoria=categoria, monto=monto, url=url)
    session.add(nueva_donacion)
    session.commit()

def generar_qr(url, monto):
    """
    Genera una imagen de código QR a partir de una URL y agrega el texto "Doná $<monto>".
    """
    # Crear el código QR
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Crear una imagen del QR
    img = qr.make_image(fill='black', back_color='white')

    # Agregar el texto "Doná $<monto>"
    img = img.convert("RGBA")
    txt = Image.new('RGBA', img.size, (255, 255, 255, 0))

    # Usar PIL para agregar texto a la imagen
    draw = ImageDraw.Draw(txt)
    font = ImageFont.load_default()
    text = f"Doná ${monto:.2f}"
    textwidth, textheight = draw.textsize(text, font)
    width, height = img.size
    x = (width - textwidth) / 2
    y = height - textheight - 10
    draw.text((x, y), text, font=font, fill=(0, 0, 0, 255))

    combined = Image.alpha_composite(img, txt)

    # Guardar la imagen en un objeto BytesIO
    buffered = BytesIO()
    combined.save(buffered, format="PNG")
    return buffered.getvalue()

def main():
    st.set_page_config(page_title="Generador de Códigos QR", layout="wide")
    st.markdown("# :rainbow[Generador de Códigos QR para Donaciones]")

    # Barra lateral para ingresar datos
    categorias = ["Mercado Libre", "Modo"]
    link_cobro = ['https://mpago.la/22u2j9Y','https://www.modo.com.ar/coupon/?id=41PQqxwezOO5HM48WwkXyE']

    num_montos = 3  # Número de montos a ingresar

    # Ingresar los montos una sola vez
    montos = []
    st.sidebar.header("Montos a donar")
    etiquetas = ["Mínimo", "Agradecido", "Generoso"]
    with st.sidebar:
        cols = st.columns(3)
        for i, (col, etiqueta) in enumerate(zip(cols, etiquetas), start=1):
            with col:
                monto = st.number_input(
                    f"{etiqueta}",
                    min_value=0.0,
                    step=100.0,
                    format="%.0f",
                    value=[1000.00, 2000.00, 3000.00][i-1],
                    key=f"monto_{i}"
                )
                montos.append(monto)

        # Ingresar las URLs para cada categoría en la barra lateral
        datos = {categoria: {"urls": []} for categoria in categorias}
        for c, categoria in enumerate(categorias):
            with st.expander(f"{categoria.title()}", expanded=True):
                for i, monto in enumerate(montos, start=1):
                    url = st.text_input(
                        f"Ingrese URL Donar ${monto:.2f}",
                        key=f"{categoria}_url_{i}",
                        value=link_cobro[c]
                    )
                    if url:
                        url = f"{url}?monto={monto:.2f}"
                    datos[categoria]["urls"].append(url)

        # Botón para guardar todos los datos
        if st.button("Guardar Todo"):
            for categoria in categorias:
                for i, monto in enumerate(montos):
                    url = datos[categoria]["urls"][i]
                    if url:
                        save_data(categoria, monto, url)
            st.success("Todos los datos han sido guardados exitosamente.")

    # Verificar que todas las URLs estén ingresadas
    for categoria in categorias:
        for idx, url in enumerate(datos[categoria]["urls"], start=1):
            if not url:
                st.warning(f"Por favor, ingresa la URL {idx} para {categoria}.")
                return

    # Crear dos columnas en la pantalla principal
    col_ml, col_modo = st.columns(2)

if __name__ == "__main__":
    main()
