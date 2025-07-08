from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from bookings.models import BoxType

class VolumeCalcAPITest(APITestCase):
    def setUp(self):
        # Create BoxTypes with real model fields
        self.box_a = BoxType.objects.create(
            name="Small Box",
            length_cm=100, width_cm=100, height_cm=100,  # 1.0 m³
            price_per_kg=Decimal("0.00"),
            price_per_box=Decimal("100.00")
        )
        self.box_b = BoxType.objects.create(
            name="Large Box",
            length_cm=100, width_cm=100, height_cm=200,  # 2.0 m³
            price_per_kg=Decimal("0.00"),
            price_per_box=Decimal("250.00")
        )
        self.url = reverse('volume-calc')

    def test_volume_calc_success(self):
        payload = {
            "boxes": [
                {"type_id": self.box_a.id, "quantity": 2},  # 2 * 1.0m³, cost 2*100
                {"type_id": self.box_b.id, "quantity": 1},  # 1 * 2.0m³, cost 1*250
            ]
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Compute expected from the model directly
        expected_volume = float(self.box_a.volume_m3 * 2 + self.box_b.volume_m3 * 1)
        expected_cost = self.box_a.price_per_box * 2 + self.box_b.price_per_box * 1

        self.assertAlmostEqual(data['total_volume'], expected_volume)
        self.assertEqual(Decimal(data['total_cost']), expected_cost)

    def test_invalid_box_type(self):
        payload = {"boxes": [{"type_id": 9999, "quantity": 1}]}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BoxType(s) not found", str(response.json().get('non_field_errors', '')))

    def test_empty_boxes_list(self):
        payload = {"boxes": []}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The ListSerializer will reject empty lists on the 'boxes' field
        self.assertIn("This list may not be empty", str(response.json().get('boxes', [])))
