from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .models import Link
import csv


def scrape(request):
    if request.method == "POST":
        site = request.POST.get('site', '').strip()

        if not site:
            return JsonResponse({'error': 'Site address cannot be empty.'})

        if not site.startswith(('http://', 'https://')):
            site = 'http://' + site

        try:
            page = requests.get(site)
            page.raise_for_status()
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f"Error fetching site: {e}"})

        soup = BeautifulSoup(page.text, 'html.parser')
        new_links = []

        for i, link in enumerate(soup.find_all('a')):
            if i >= 100:
                break

            link_address = link.get('href')
            if not link_address:
                continue

            full_url = urljoin(site, link_address)
            link_text = link.get_text(strip=True) or "Unnamed Link"

            if not Link.objects.filter(address=full_url).exists():
                new_link = Link.objects.create(address=full_url, name=link_text)
                new_links.append({'id': new_link.id, 'name': new_link.name, 'address': new_link.address})

        return JsonResponse({'success': True, 'links': new_links})

    else:
        search = request.GET.get('search', '')
        if search:
            data = Link.objects.filter(name__icontains=search) | Link.objects.filter(address__icontains=search)
        else:
            data = Link.objects.all()
        return render(request, 'myapp/result.html', {'data': data, 'search': search})


def clear(request):
    Link.objects.all().delete()
    return redirect('/')


def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scraped_links.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Link', 'Created At'])

    for link in Link.objects.all():
        writer.writerow([link.id, link.name, link.address, link.created_at])

    return response
