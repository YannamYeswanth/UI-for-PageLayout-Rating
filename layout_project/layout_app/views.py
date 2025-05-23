import os
import csv
import json
from PIL import Image, ImageDraw
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect


def draw_layout_image(items, width, height, color_map):
    base_image = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    for item in items:
        overlay = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        x, y = item['x'], item['y']
        w, h = item['width'], item['height']
        category = item.get('category', 'default')
        hex_color = color_map.get(category, '#888888')
        rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgba = rgb + (150,)
        draw.rectangle([x, y, x + w, y + h], fill=rgba, outline=(0, 0, 0, 100))
        base_image = Image.alpha_composite(base_image, overlay)
    return base_image.convert('RGB')


def write_rating_row(document_id, page_number, layout_name, rating, feedback):
    csv_path = os.path.join(settings.BASE_DIR, 'ratings.csv')
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['document_id', 'page_number', 'layout_name', 'rating', 'feedback'])
        writer.writerow([document_id, page_number, layout_name, rating, feedback])


def index(request):
    if request.method == 'GET' and not request.GET.get('page'):
        request.session.pop('rendered_pages', None)
        request.session.pop('json_data', None)

    show_layouts = False
    layouts_per_page = request.POST.get('layouts_per_page') or request.GET.get('layouts_per_page') or 4

    try:
        layouts_per_page = int(layouts_per_page)
    except ValueError:
        layouts_per_page = 4
    layouts_per_page = max(1, min(layouts_per_page, 15))

    if request.method == 'POST':
        if 'upload_json' in request.POST and request.FILES.get('json_file'):
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
            show_layouts = True
            return HttpResponseRedirect(f"?page=1&layouts_per_page={layouts_per_page}")

        elif 'rate_image' in request.POST:
            rendered_pages = request.session.get('rendered_pages', [])
            json_data = request.session.get('json_data', [])
            current_page = int(request.GET.get('page', 1))
            paginator = Paginator(rendered_pages, layouts_per_page)
            page_obj = paginator.get_page(current_page)

            for key in request.POST:
                if key.startswith("rating_"):
                    _, page_number, layout_name = key.split("_", 2)
                    rating = request.POST.get(key)
                    feedback_key = f"feedback_{page_number}_{layout_name}"
                    feedback = request.POST.get(feedback_key, "")

                    for page in json_data:
                        if str(page["page_number"]) == page_number:
                            document_id = page["document_id"]
                            break
                    else:
                        continue

                    write_rating_row(document_id, page_number, layout_name, rating, feedback)

            if page_obj.has_next():
                return HttpResponseRedirect(f"?page={page_obj.next_page_number()}&layouts_per_page={layouts_per_page}")

            request.session.pop('rendered_pages', None)
            request.session.pop('json_data', None)
            return redirect('index')

    rendered_pages = request.session.get('rendered_pages', [])
    paginator = Paginator(rendered_pages, layouts_per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    layouts_per_row = max(1, (layouts_per_page + 2) // 3)
    rows = [page_obj.object_list[i:i + layouts_per_row] for i in range(0, len(page_obj.object_list), layouts_per_row)]

    return render(request, 'layout_app/index.html', {
        'page_obj': page_obj,
        'rows': rows,
        'show_layouts': show_layouts or (bool(rendered_pages) and 'page' in request.GET),
        'layouts_per_page': layouts_per_page,
        'range_1_16': range(1, 16),
    })
