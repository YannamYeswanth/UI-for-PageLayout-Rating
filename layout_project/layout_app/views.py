import csv
from django.shortcuts import render, redirect
from django.conf import settings
from .utils import generate_layout_image
import json
import os
from django.http import HttpResponse

# File upload and render logic
def index(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        data = json.load(json_file)
        page_number = data.get("page_number")
        filename = f"layout_{page_number}.png"

        # Generate layout image
        image_path = generate_layout_image(data, filename)

        return render(request, 'layout_app/index.html', {
            'image_url': settings.MEDIA_URL + filename,
            'page_number': page_number,
        })

    return render(request, 'layout_app/index.html')


# New view for handling rating
def submit_rating(request):
    if request.method == 'POST':
        page_number = request.POST.get("page_number")
        rating = request.POST.get("rating")

        csv_path = os.path.join(settings.BASE_DIR, "ratings.csv")
        file_exists = os.path.isfile(csv_path)

        with open(csv_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["page_number", "rating"])
            writer.writerow([page_number, rating])

        return HttpResponse("Rating submitted successfully!")
