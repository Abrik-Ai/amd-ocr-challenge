from PIL import Image

picture = Image.open("input/image_01.png")
new_picture = picture.convert("RGB")
new_picture.save("input/image_02.jpg")
new_picture.save("input/image_03.tiff")
