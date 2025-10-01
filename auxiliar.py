from PIL import Image

img = Image.open("C:\\Users\\tatoa\\Documents\\GitHub\\ThankAttack\\assets\\images\\tiles\\4.jpg").convert("RGBA")
datas = img.getdata()

newData = []
for item in datas:
    # Suponiendo que el fondo es blanco
    if item[:3] == (255, 255, 255):
        newData.append((255, 255, 255, 0))
    else:
        newData.append(item)

img.putdata(newData)
img.save("pixelart_transparente.png")
