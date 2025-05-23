# views.py
import os
import uuid
import csv
import json
from PIL import Image, ImageDraw
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse


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
            rendered_pages = request.session.get('rendered_pages', [])
            current_page = int(request.GET.get('page', 1))
            paginator = Paginator(rendered_pages, 4)
            page_obj = paginator.get_page(current_page)

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

            # Move to next page if available
            if page_obj.has_next():
                next_page = page_obj.next_page_number()
                return HttpResponseRedirect(f"?page={next_page}")

            return redirect('index')  # Or redirect to summary/thank you page

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
    paginator = Paginator(rendered_pages, 4)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    rows = [rendered_pages[i:i+2] for i in range((page_obj.number - 1) * 4, min(page_obj.number * 4, len(rendered_pages)), 2)]

    return render(request, 'layout_app/index.html', {
        'page_obj': page_obj,
        'rows': rows
    })