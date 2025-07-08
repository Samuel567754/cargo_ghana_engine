from django.db import migrations
import random
import string

def generate_unique_reference_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def populate_reference_codes(apps, schema_editor):
    Booking = apps.get_model('bookings', 'Booking')
    used_codes = set(Booking.objects.values_list('reference_code', flat=True))

    for booking in Booking.objects.all():
        if not booking.reference_code:
            code = generate_unique_reference_code()
            while code in used_codes:
                code = generate_unique_reference_code()
            booking.reference_code = code
            booking.save()
            used_codes.add(code)

class Migration(migrations.Migration):

    dependencies = [
    ('bookings', '0002_booking_reference_code_alter_booking_cost'),
]
 
    operations = [
        migrations.RunPython(populate_reference_codes),
    ]
