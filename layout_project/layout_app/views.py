import os
import uuid
import csv
import json
from PIL import Image, ImageDraw
from django.shortcuts import render, redirect
from django.conf import settings

# Helper to draw layout image
def draw_layout_image(items, width, height, color_map):
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    for item in items:
        x, y = item['x'], item['y']
        w, h = item['width'], item['height']
        category = item.get('category', 'unknown')
        color = color_map.get(category, 'gray')
        draw.rectangle([x, y, x + w, y + h], fill=color, outline='black')

    return image

# Save a row to ratings.csv
def write_rating_row(document_id, page_number, layout_name, rating):
    csv_path = os.path.join(settings.BASE_DIR, 'ratings.csv')
    file_exists = os.path.isfile(csv_path)

    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['document_id', 'page_number', 'layout_name', 'rating'])
        writer.writerow([document_id, page_number, layout_name, rating])


# MAIN view
def index(request):
    if request.method == 'POST':
        # 🟡 Rating Submission
        if 'rate_image' in request.POST:
            json_data = request.session.get('json_data', [])

            for key in request.POST:
                if key.startswith("rating_"):
                    _, page_number, layout_name = key.split("_", 2)
                    rating = request.POST.get(key)

                    # Get document_id from session data
                    for page in json_data:
                        if str(page["page_number"]) == page_number:
                            document_id = page["document_id"]
                            break
                    else:
                        continue  # skip if not found

                    write_rating_row(document_id, page_number, layout_name, rating)

            return redirect('index')

        # 🟢 JSON Upload and Image Generation
        elif 'json_file' in request.FILES:
            json_file = request.FILES['json_file']
            pages_data = json.load(json_file)
            request.session['json_data'] = pages_data  # store for later during rating

            color_map = {
                'textFrame': '#FFD54F',
                'graphics': '#4FC3F7',
                'default': '#E0E0E0'
            }

            rendered_pages = []

            for page in pages_data:
                width = page['width']
                height = page['height']
                page_number = page['page_number']
                document_id = page['document_id']

                # Render all known layout keys (original & predictions)
                for layout_name in page:
                    if layout_name.startswith('items'):
                        items = page[layout_name]

                        img = draw_layout_image(items, width, height, color_map)
                        filename = f"layout_{document_id}_{page_number}_{layout_name}_{uuid.uuid4().hex}.png"
                        image_path = os.path.join(settings.MEDIA_ROOT, filename)
                        img.save(image_path)

                        rendered_pages.append({
                            'image_url': settings.MEDIA_URL + filename,
                            'page_number': page_number,
                            'layout_name': layout_name,
                            'document_id': document_id
                        })

            return render(request, 'layout_app/index.html', {
                'rendered_pages': rendered_pages
            })

    return render(request, 'layout_app/index.html')
