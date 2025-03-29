# shortener/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from .models import ShortURL, ClickEvent, DashboardPreference
import string
import random
import csv
import pandas as pd
from io import StringIO, BytesIO
import qrcode
import base64

# shortener/views.py

import qrcode
from io import BytesIO
import base64
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import ShortURL

def generate_short_code(length=5):
    import string
    import random
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def ensure_minimum_length(alias, min_length=5):
    if len(alias) < min_length:
        additional_chars = generate_short_code(min_length - len(alias))
        return alias + additional_chars
    return alias

@login_required
def shorten_url(request):
    if request.method == 'POST':
        original_url = request.POST['original_url']
        custom_alias = request.POST.get('custom_alias')
        expiration_date_str = request.POST.get('expiration_date')

        expiration_date = None
        if expiration_date_str:
            try:
                expiration_date = timezone.datetime.strptime(expiration_date_str, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return HttpResponse("Invalid date format. Please use 'YYYY-MM-DDTHH:MM:SS'.", status=400)

        existing_url = ShortURL.objects.filter(original_url=original_url).first()
        if existing_url:
            # Generate QR code for the existing URL
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(request.build_absolute_uri(f'/{existing_url.short_code}/'))
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            qr_code_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return render(request, 'shortener/shortened_url.html', {'short_code': existing_url.short_code, 'qr_code_img': qr_code_img})

        if custom_alias:
            custom_alias = ensure_minimum_length(custom_alias)
            if ShortURL.objects.filter(short_code=custom_alias).exists():
                return HttpResponse("Custom alias already in use. Please choose another one.", status=400)
            short_code = custom_alias
        else:
            short_code = generate_short_code()

        short_url = ShortURL.objects.create(
            original_url=original_url,
            short_code=short_code,
            user=request.user,
            expiration_date=expiration_date
        )

        # Generate QR code for the new shortened URL
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(request.build_absolute_uri(f'/{short_code}/'))
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_code_img = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return render(request, 'shortener/shortened_url.html', {'short_code': short_code, 'qr_code_img': qr_code_img})

    return render(request, 'shortener/index.html')

def redirect_url(request, short_code):
    url = get_object_or_404(ShortURL, short_code=short_code)

    if url.is_expired():
        return HttpResponse("Link Expired", status=404)

    if not url.is_active:
        return HttpResponse("Link Deactivated", status=404)

    ClickEvent.objects.create(
        short_url=url,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        referrer=request.META.get('HTTP_REFERER')
    )
    return redirect(url.original_url)

@login_required
def url_analytics(request, short_code):
    url = get_object_or_404(ShortURL, short_code=short_code, user=request.user)
    clicks = url.clicks.all()
    return render(request, 'shortener/analytics.html', {'url': url, 'clicks': clicks})

@login_required
def delete_url(request, short_code):
    url = get_object_or_404(ShortURL, short_code=short_code, user=request.user)
    url.delete()
    return redirect('shorten_url')

@login_required
def deactivate_url(request, short_code):
    url = get_object_or_404(ShortURL, short_code=short_code, user=request.user)
    url.is_active = False
    url.save()
    return redirect('shorten_url')

# shortener/views.py

@login_required
def bulk_upload(request):
    if request.method == 'POST':
        file = request.FILES['file']
        shortened_urls = []

        if file.name.endswith('.csv'):
            data = file.read().decode('utf-8')
            reader = csv.DictReader(StringIO(data))
            for row in reader:
                original_url = row.get('original_url')
                custom_alias = row.get('custom_alias', '')
                expiration_date_str = row.get('expiration_date', '')
                tags = row.get('tags', '')
                category = row.get('category', '')

                if not original_url:
                    continue

                expiration_date = None
                if expiration_date_str:
                    try:
                        expiration_date = timezone.datetime.strptime(expiration_date_str, '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        continue

                if custom_alias:
                    custom_alias = ensure_minimum_length(custom_alias)
                    if ShortURL.objects.filter(short_code=custom_alias).exists():
                        custom_alias = generate_short_code()
                    short_code = custom_alias
                else:
                    short_code = generate_short_code()

                short_url = ShortURL.objects.create(
                    original_url=original_url,
                    short_code=short_code,
                    user=request.user,
                    expiration_date=expiration_date,
                    tags=tags,
                    category=category
                )
                shortened_urls.append({
                    'original_url': original_url,
                    'short_url': f"http://127.0.0.1:8000/{short_code}/",
                    'short_code': short_code,
                    'expiration_date': expiration_date_str,
                    'tags': tags,
                    'category': category
                })

        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
            for index, row in df.iterrows():
                original_url = row.get('original_url')
                custom_alias = row.get('custom_alias', '')
                expiration_date_str = row.get('expiration_date', '')
                tags = row.get('tags', '')
                category = row.get('category', '')

                if not original_url:
                    continue

                expiration_date = None
                if expiration_date_str:
                    try:
                        expiration_date = timezone.datetime.strptime(expiration_date_str, '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        continue

                if custom_alias:
                    custom_alias = ensure_minimum_length(custom_alias)
                    if ShortURL.objects.filter(short_code=custom_alias).exists():
                        custom_alias = generate_short_code()
                    short_code = custom_alias
                else:
                    short_code = generate_short_code()

                short_url = ShortURL.objects.create(
                    original_url=original_url,
                    short_code=short_code,
                    user=request.user,
                    expiration_date=expiration_date,
                    tags=tags,
                    category=category
                )
                shortened_urls.append({
                    'original_url': original_url,
                    'short_url': f"http://127.0.0.1:8000/{short_code}/",
                    'short_code': short_code,
                    'expiration_date': expiration_date_str,
                    'tags': tags,
                    'category': category
                })

        if not shortened_urls:
            return HttpResponse("No valid URLs were processed.", status=400)

        # Generate the CSV file
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=shortened_urls[0].keys())
        writer.writeheader()
        writer.writerows(shortened_urls)

        # Save the file to a temporary location or in memory
        response_content = output.getvalue()

        # Render the success page with a download link
        return render(request, 'shortener/bulk_upload_success.html', {'csv_data': response_content})

    return render(request, 'shortener/bulk_upload.html')


@login_required
def dashboard(request):
    preferences, created = DashboardPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        preferences.show_clicks = 'show_clicks' in request.POST
        preferences.show_expiration = 'show_expiration' in request.POST
        preferences.show_tags = 'show_tags' in request.POST
        preferences.show_category = 'show_category' in request.POST
        preferences.save()
        return redirect('dashboard')

    urls = ShortURL.objects.filter(user=request.user)
    qr_codes = {}

    for url in urls:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(request.build_absolute_uri(f'/{url.short_code}/'))
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_codes[url.short_code] = base64.b64encode(buffer.getvalue()).decode('utf-8')

    context = {
        'urls': urls,
        'preferences': preferences,
        'qr_codes': qr_codes,
    }
    return render(request, 'shortener/dashboard.html', context)

@login_required
def download_qr_code(request, short_code):
    url = get_object_or_404(ShortURL, short_code=short_code, user=request.user)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(request.build_absolute_uri(f'/{short_code}/'))
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=f'{short_code}_qr.png')

from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'shortener/signup.html', {'form': form})


# shortener/views.py

from django.shortcuts import render

@login_required
def shorten_url(request):
    if request.method == 'POST':
        original_url = request.POST['original_url']
        custom_alias = request.POST.get('custom_alias')
        expiration_date_str = request.POST.get('expiration_date')

        expiration_date = None
        if expiration_date_str:
            try:
                expiration_date = timezone.datetime.strptime(expiration_date_str, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return HttpResponse("Invalid date format. Please use 'YYYY-MM-DDTHH:MM:SS'.", status=400)

        existing_url = ShortURL.objects.filter(original_url=original_url).first()
        if existing_url:
            return render(request, 'shortener/shortened_url.html', {'short_code': existing_url.short_code})

        if custom_alias:
            custom_alias = ensure_minimum_length(custom_alias)
            if ShortURL.objects.filter(short_code=custom_alias).exists():
                return HttpResponse("Custom alias already in use. Please choose another one.", status=400)
            short_code = custom_alias
        else:
            short_code = generate_short_code()

        short_url = ShortURL.objects.create(
            original_url=original_url,
            short_code=short_code,
            user=request.user,
            expiration_date=expiration_date
        )
        return render(request, 'shortener/shortened_url.html', {'short_code': short_code})

    return render(request, 'shortener/index.html')


