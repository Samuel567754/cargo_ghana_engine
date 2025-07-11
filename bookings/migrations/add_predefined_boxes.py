from django.db import migrations

def add_predefined_boxes(apps, schema_editor):
    BoxType = apps.get_model('bookings', 'BoxType')
    
    predefined_boxes = [
        {
            'name': 'Small Box (S)',
            'length_cm': 30,
            'width_cm': 20,
            'height_cm': 15,
            'price_per_kg': 2.50,
            'price_per_box': 50.00
        },
        {
            'name': 'Medium Box (M)',
            'length_cm': 45,
            'width_cm': 30,
            'height_cm': 30,
            'price_per_kg': 2.50,
            'price_per_box': 100.00
        },
        {
            'name': 'Large Box (L)',
            'length_cm': 60,
            'width_cm': 45,
            'height_cm': 45,
            'price_per_kg': 2.50,
            'price_per_box': 200.00
        },
        {
            'name': 'Extra Large Box (XL)',
            'length_cm': 90,
            'width_cm': 60,
            'height_cm': 60,
            'price_per_kg': 2.50,
            'price_per_box': 400.00
        }
    ]
    
    for box_data in predefined_boxes:
        BoxType.objects.create(**box_data)

class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0008_booking_referral_alter_booking_cost_and_more'),
    ]

    operations = [
        migrations.RunPython(add_predefined_boxes)
    ]