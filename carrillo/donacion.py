import streamlit as st
import qrcode
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

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def save_data(categoria, monto, url):
    # Guardar los datos de una nueva donación en la base de datos
    donacion = Donacion(categoria=categoria, monto=monto, url=url)
    with Session() as session:
        session.add(donacion)
        session.commit()

def generar_qr(url, monto):
    """
    Genera una imagen de código QR a partir de una URL.
    """
    # Crear el código QR con configuración específica
    qr = qrcode.QRCode( version=1, box_size=10, border=4)
    qr.add_data(url)  # Agregar la URL a los datos del QR
    qr.make(fit=True)

    # Crear una imagen del QR
    img = qr.make_image(fill='black', back_color='white').convert("RGB")

    # Guardar la imagen en un objeto BytesIO
    buffered = BytesIO()
    img.save(buffered, format="PNG")  # Guardar la imagen como PNG en el buffer
    return buffered.getvalue()  # Devolver el contenido del buffer

def main():
    # Configurar la página principal de la aplicación
    st.set_page_config(page_title="Generador de Códigos QR", layout="wide")
    st.markdown("# :rainbow[Generador de Códigos QR para Donaciones]")

    # Barra lateral para ingresar datos
    categorias = ["Mercado Libre", "Modo"]
    link_cobro = ['https://mpago.la/22u2j9Y', 'https://www.modo.com.ar/coupon/?id=41PQqxwezOO5HM48WwkXyE']

    # Ingresar los montos una sola vez
    montos = []
    st.sidebar.header("Montos a donar")
    etiquetas = ["Mínimo", "Agradecido", "Generoso"]
    with st.sidebar:
        # Crear campos de entrada para los montos de donación
        for i, etiqueta in enumerate(etiquetas, start=1):
            monto = st.number_input(
                f"{etiqueta}",
                min_value=0.0,  # Valor mínimo permitido
                step=100.0,  # Paso de incremento
                format="%.0f",  # Formato del número
                value=[1000.00, 2000.00, 3000.00][i-1],  # Valor por defecto
                key=f"monto_{i}"  # Clave para identificar el campo
            )
            montos.append(monto)

        # Ingresar las URLs para cada categoría en la barra lateral
        datos = {categoria: [] for categoria in categorias}  # Inicializar diccionario para URLs
        for c, categoria in enumerate(categorias):
            with st.expander(f"{categoria.title()}", expanded=True):
                # Crear campos de entrada para las URLs de cada monto
                for i, monto in enumerate(montos, start=1):
                    url = st.text_input(
                        f"Ingrese URL Donar ${monto:.2f}",
                        key=f"{categoria}_url_{i}",
                        value=link_cobro[c]  # Valor por defecto para la URL
                    )
                    if url:
                        url = f"{url}?monto={monto:.2f}"  # Agregar monto a la URL
                    datos[categoria].append(url)  # Guardar la URL en el diccionario

        # Botón para guardar todos los datos
        if st.button("Guardar Todo"):
            # Guardar cada donación en la base de datos
            for categoria in categorias:
                for i, monto in enumerate(montos):
                    url = datos[categoria][i]
                    if url:
                        save_data(categoria, monto, url)
            st.success("Todos los datos han sido guardados exitosamente.")

    # Verificar que todas las URLs estén ingresadas
    for categoria in categorias:
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
                    buffer = generar_qr(url, monto)  # Generar el QR
                    st.image(buffer, width=300)  # Mostrar la imagen del QR
                    st.markdown(f"## Doná ${monto:.0f}\n---")  # Mostrar el monto

    # Mostrar los QR para cada categoría
    mostrar_qr("Mercado Libre", col_ml)
    mostrar_qr("Modo", col_modo)

if __name__ == "__main__":
    main()