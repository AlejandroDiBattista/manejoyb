import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os

def generate_qr_with_style(url, amount_text, output_file):
    # Parámetros de estilo
    qr_box_size = 20  # Tamaño de cada caja del QR
    qr_border = 4     # Borde interno del QR
    qr_fill_color = "blue"
    qr_back_color = "white"
    qr_border_size = 20  # Tamaño del borde alrededor del QR (ajustado según el tamaño del QR)
    background_color = (173, 216, 230)  # Color de fondo del lienzo (azul claro)
    font_size = 80  # Tamaño de la fuente (duplicado respecto al original de 40)
    text_color = "black"
    text_padding = 20  # Espacio entre el QR y el texto

    # Selección de una fuente que exista en macOS
    # Lista de rutas comunes de fuentes en macOS
    mac_fonts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Helvetica.ttf",
        "/Library/Fonts/Verdana.ttf",
        "/Library/Fonts/Times New Roman.ttf"
    ]
    
    # Intentar encontrar una fuente válida
    font_path = None
    for path in mac_fonts:
        if os.path.exists(path):
            font_path = path
            break
    
    if font_path is None:
        print("No se encontró una fuente predeterminada. Usando fuente predeterminada de PIL.")
    
    # Crear el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=qr_box_size,
        border=qr_border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Generar imagen del código QR con color personalizado
    qr_img = qr.make_image(fill_color=qr_fill_color, back_color=qr_back_color).convert('RGB')

    # Añadir un borde alrededor del QR
    qr_with_border = ImageOps.expand(qr_img, border=qr_border_size, fill=background_color)

    # Redondear las esquinas del QR con borde
    img_width, img_height = qr_with_border.size
    corner_radius = int(img_width * 0.05)  # 5% del ancho del QR
    rounded_mask = Image.new('L', (img_width, img_height), 0)
    draw = ImageDraw.Draw(rounded_mask)
    draw.rounded_rectangle([(0, 0), (img_width, img_height)], radius=corner_radius, fill=255)
    
    qr_rounded = Image.new('RGBA', (img_width, img_height))
    qr_rounded.paste(qr_with_border, (0, 0))
    qr_rounded.putalpha(rounded_mask)

    # Crear un lienzo nuevo más grande para incluir el texto debajo
    text_height_estimate = font_size + text_padding  # Estimación de la altura del texto
    total_height = img_height + text_height_estimate + qr_border_size  # Altura total del lienzo
    canvas = Image.new('RGB', (img_width, total_height), background_color)

    # Pegar el código QR redondeado en el lienzo
    canvas.paste(qr_rounded, (0, 0), qr_rounded)

    # Añadir texto debajo del QR
    draw_canvas = ImageDraw.Draw(canvas)
    
    # Cargar la fuente
    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except IOError:
        font = ImageFont.load_default()
        print("No se pudo cargar la fuente especificada. Usando fuente predeterminada de PIL.")
    
    # Calcular el tamaño del texto
    text_bbox = draw_canvas.textbbox((0, 0), amount_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Posición del texto centrado
    text_x = (img_width - text_width) // 2
    text_y = img_height + qr_border_size + text_padding // 2
    draw_canvas.text((text_x, text_y), amount_text, font=font, fill=text_color)

    # Guardar la imagen final
    canvas.save(output_file)
    print(f"QR code guardado en {output_file}")

# Parámetros
url = {'modo': "https://www.modo.com.ar/coupon/?id=3LcBSSHketzDiYppIMZ6JK", 'mercadopago': "https://mpago.la/1VMcbqD"}
amount_text = "Dona $1.000"
for nombre, url in url.items():
    output_file = f"qr_{nombre}.png"
    # Generar el QR con estilo
    generate_qr_with_style(url, amount_text, output_file)
