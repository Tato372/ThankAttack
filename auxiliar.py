# quitar_fondo.py
from PIL import Image
import os

def inspect_background(path):
    img = Image.open(path).convert("RGBA")
    w,h = img.size
    corners = [img.getpixel((0,0)), img.getpixel((w-1,0)),
               img.getpixel((0,h-1)), img.getpixel((w-1,h-1))]
    avg = tuple(sum(c[i] for c in corners)//4 for i in range(4))
    print("Tamaño:", img.size, "Formato detectado:", img.format)
    print("Esquinas (RGBA):", corners)
    print("Promedio esquinas (RGBA):", avg)

def remove_white_background(infile, outfile, threshold=240):
    """
    threshold: 0..255 - nivel a partir del cual consideramos 'cercano a blanco'.
               Valores altos = solo blancos muy puros; valores bajos = más pixels se vuelven transparentes.
    """
    img = Image.open(infile).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for (r,g,b,a) in datas:
        # intensidad máxima del pixel (mejor para detectar 'blancos cercanos')
        max_rgb = max(r, g, b)

        if max_rgb >= threshold:
            # calculamos alpha proporcional:
            # si max_rgb == 255 -> alpha = 0 (totalmente transparente)
            # si max_rgb == threshold -> alpha = 255 (opaco)
            denom = max(1, 255 - threshold)  # evitar división por 0
            alpha = int((255 - max_rgb) / denom * 255)
            alpha = max(0, min(255, alpha))

            # si el pixel ya tenía transparencia, combinamos (tomamos min para evitar aumentar la opacidad)
            final_alpha = min(a, alpha)
            new_data.append((r, g, b, final_alpha))
        else:
            # pixel suficientemente lejos de blanco -> lo dejamos opaco como estaba
            new_data.append((r, g, b, a))

    img.putdata(new_data)
    # guardar como PNG para mantener transparencia
    img.save(outfile, "PNG")
    print(f"Guardado: {outfile}")

if __name__ == "__main__":
    # EJEMPLO: cambialo por tus rutas
    entrada = r"C:\\Users\\tatoa\\OneDrive\\Escritorio\\TEC\\Semestres\\II_Semestre_2025\\Diseño de Software\\ThankAttack\\assets\\images\\tiles\\6.jpg"
    salida  = r"6.jpg"

    # inspeccionar (opcional) para entender cuál es el color real de fondo
    inspect_background(entrada)

    # prueba con distintos thresholds (ajusta si ves que quedan restos blancos)
    THRESHOLD = 240
    remove_white_background(entrada, salida, threshold=THRESHOLD)
    print("Proceso completado.")