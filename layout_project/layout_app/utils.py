from PIL import Image, ImageDraw
import os

CATEGORY_COLORS = {
    "graphics": "skyblue",
    "textFrame": "gold",
}

def generate_layout_image(data, filename):
    # width = data["width"]
    # height = data["height"]
    # items = data["items"]

    # image = Image.new("RGB", (width, height), "white")
    # draw = ImageDraw.Draw(image)
    # draw.rectangle([0,0,width,height],outline="black")

    # for item in items:
    #     x, y = item["x"], item["y"]
    #     w, h = item["width"], item["height"]
    #     category = item["category"]
    #     color = CATEGORY_COLORS.get(category, "gray")
    #     draw.rectangle([x, y, x + w, y + h], fill=color, outline="black")

    width = data.get("width", 1920)
    height = data.get("height", 1080)

    # Create a white canvas
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Try to load a default font
    # try:
    #     font = ImageFont.truetype("arial.ttf", 20)
    # except:
    #     font = ImageFont.load_default()

    for item in data.get("items", []):
        x, y = item.get("x", 0), item.get("y", 0)
        w, h = item.get("width", 100), item.get("height", 50)
        category = item.get("category", "")

        if category == "graphics":
            # Blue rectangle for graphics
            draw.rectangle([x, y, x + w, y + h], fill="#3a7bd5", outline="#1e3f72", width=2)
        elif category == "textFrame":
            # Orange rectangle with text
            draw.rectangle([x, y, x + w, y + h], fill="#ffa64d", outline="#cc7a00", width=2)
            # Centered placeholder text
            # text = "Text Frame"
            # text_w, text_h = draw.textsize(text, font=font)
            # text_x = x + (w - text_w) / 2
            # text_y = y + (h - text_h) / 2
            # draw.text((text_x, text_y), text, fill="#5a3300", font=font)

    # Save the image
    # img.save(output_image_path)

    path = os.path.join("media", filename)
    image.save(path)
    return path
