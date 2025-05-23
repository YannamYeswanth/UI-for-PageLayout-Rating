# views.py
import os
import uuid
import csv
import json
from PIL import Image, ImageDraw
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.paginator import Paginator


def draw_layout_image(items, width, height, color_map):
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    for item in items:
        x, y = item['x'], item['y']
        w, h = item['width'], item['height']
        category = item.get('category', 'unknown')
        color = color_map.get(category, color_map.get('default', 'gray'))
        draw.rectangle([x, y, x + w, y + h], fill=color, outline='black')

    return image


def write_rating_row(document_id, page_number, layout_name, rating):
    csv_path = os.path.join(settings.BASE_DIR, 'ratings.csv')
    file_exists = os.path.isfile(csv_path)

    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['document_id', 'page_number', 'layout_name', 'rating'])
        writer.writerow([document_id, page_number, layout_name, rating])


def index(request):
    if request.method == 'POST':
        if 'rate_image' in request.POST:
            json_data = request.session.get('json_data', [])

            for key in request.POST:
                if key.startswith("rating_"):
                    _, page_number, layout_name = key.split("_", 2)
                    rating = request.POST.get(key)

                    for page in json_data:
                        if str(page["page_number"]) == page_number:
                            document_id = page["document_id"]
                            break
                    else:
                        continue

                    write_rating_row(document_id, page_number, layout_name, rating)

            return redirect('index')

        elif 'json_file' in request.FILES:
            json_file = request.FILES['json_file']
            pages_data = json.load(json_file)
            request.session['json_data'] = pages_data

            color_map = {
                'textFrame': '#FFD54F',
                'graphics': '#4FC3F7',
                'default': '#E0E0E0'
            }

            rendered_pages = []
            layout_keys = ['items', 'predicted_items_0', 'predicted_items_1', 'predicted_items_2', 'predicted_items_3']

            for page in pages_data:
                width = page['width']
                height = page['height']
                page_number = page['page_number']
                document_id = page['document_id']

                for layout_name in layout_keys:
                    if layout_name not in page:
                        continue

                    items = page[layout_name]
                    img = draw_layout_image(items, width, height, color_map)

                    filename = f"layout_{document_id}_{page_number}_{layout_name}.png"
                    image_path = os.path.join(settings.MEDIA_ROOT, filename)
                    img.save(image_path)

                    rendered_pages.append({
                        'image_url': settings.MEDIA_URL + filename,
                        'page_number': page_number,
                        'layout_name': layout_name,
                        'document_id': document_id
                    })

            request.session['rendered_pages'] = rendered_pages

    rendered_pages = request.session.get('rendered_pages', [])
    paginator = Paginator(rendered_pages, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Group by 3s for rows in the template (handled in view to avoid needing 'batch' filter)
    rows = [rendered_pages[i:i+3] for i in range((page_obj.number - 1) * 6, min(page_obj.number * 6, len(rendered_pages)), 3)]

    return render(request, 'layout_app/index.html', {
        'page_obj': page_obj,
        'rows': rows
    })