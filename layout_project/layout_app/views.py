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



import random


import os
import json
import uuid
import random
# from PIL import Image, ImageDraw
# from django.conf import settings
# from django.shortcuts import render
# from django.http import HttpResponse


def apply_design_constraints(items, page_width, page_height, strength='medium', grid_size=10):
    new_items = []
    margin = 30
    shift_range = {
        'low': 10,
        'medium':  40,
        'high': 80
    }.get(strength, 40)

    size_variation = {
        'low': 0.05,
        'medium': 0.15,
        'high': 0.3
    }.get(strength, 0.15)

    for item in items:
        new_item = item.copy()

        # Position variation
        shift_x = random.randint(-shift_range, shift_range)
        shift_y = random.randint(-shift_range, shift_range)
        new_x = max(margin, min(page_width - new_item['width'] - margin, new_item['x'] + shift_x))
        new_y = max(margin, min(page_height - new_item['height'] - margin, new_item['y'] + shift_y))

        # Snap to grid
        new_item['x'] = round(new_x / grid_size) * grid_size
        new_item['y'] = round(new_y / grid_size) * grid_size

        # Size variation (preserve aspect ratio)
        if random.random() < 0.5:
            w_factor = 1 + random.uniform(-size_variation, size_variation)
            h_factor = w_factor if random.random() < 0.7 else 1 + random.uniform(-size_variation, size_variation)
            new_width = max(20, min(page_width - new_item['x'] - margin, int(new_item['width'] * w_factor)))
            new_height = max(20, min(page_height - new_item['y'] - margin, int(new_item['height'] * h_factor)))
            new_item['width'] = round(new_width / grid_size) * grid_size
            new_item['height'] = round(new_height / grid_size) * grid_size

        new_items.append(new_item)

    return new_items


def draw_layout_image(items, width, height):
    color_map = {
        'textFrame': '#FFD54F',
        'graphics': '#4FC3F7',
        'default': '#E0E0E0'
    }

    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    for item in items:
        x, y = item['x'], item['y']
        w, h = item['width'], item['height']
        category = item.get('category', 'default')
        color = color_map.get(category, color_map['default'])
        draw.rectangle([x, y, x + w, y + h], fill=color, outline='black')

    return image


def augment_layout(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        base_layout = json.load(json_file)

        num_variants = int(request.POST.get('num_variants', 5))
        strength = request.POST.get('strength', 'medium')

        augmented_data = []
        preview_images = []

        for i in range(num_variants):
            new_items = apply_design_constraints(
                base_layout['items'],
                base_layout['width'],
                base_layout['height'],
                strength
            )
            new_layout = {
                'document_id': base_layout['document_id'],
                'page_number': base_layout['page_number'],
                'width': base_layout['width'],
                'height': base_layout['height'],
                'items': new_items
            }
            augmented_data.append(new_layout)

            # Draw preview image
            img = draw_layout_image(new_items, base_layout['width'], base_layout['height'])
            filename = f"aug_{uuid.uuid4().hex}.png"
            path = os.path.join(settings.MEDIA_ROOT, filename)
            img.save(path)
            preview_images.append(settings.MEDIA_URL + filename)

        return render(request, 'layout_app/augment_result.html', {
            'augmented_json': json.dumps(augmented_data, indent=2),
            'image_paths': preview_images
        })

    return render(request, 'layout_app/augment_layout.html')
