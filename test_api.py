import unittest

from app import app, KARNATAKA_DISTRICTS


class KarnatakaDistrictTests(unittest.TestCase):
    def test_home_has_all_karnataka_districts(self):
        client = app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        for district in KARNATAKA_DISTRICTS:
            self.assertIn(district.encode("utf-8"), response.data)

    def test_home_has_clickable_market_button(self):
        client = app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="market-price-btn"', response.data)
        self.assertIn(b'action="/recommendations" method="post"', response.data)

    def test_workflow_shows_15_crops_and_every_district_market(self):
        client = app.test_client()
        farm = {
            "district": "Hassan",
            "taluk": "Hassan",
            "village": "Malali",
            "landArea": "4.8",
            "soilType": "Black Soil",
            "waterAvailability": "Some Water Available",
        }

        recommendations = client.post("/recommendations", data=farm)
        self.assertEqual(recommendations.status_code, 200)
        self.assertEqual(recommendations.data.count(b'class="recommendation-item crop-detail-card'), 15)
        self.assertIn(b"Best crop for your farm", recommendations.data)

        markets = client.post("/markets", data={**farm, "crop": "Tomato"})
        self.assertEqual(markets.status_code, 200)
        self.assertEqual(markets.data.count(b"data-market="), len(KARNATAKA_DISTRICTS))

    def test_analyze_accepts_any_karnataka_district(self):
        client = app.test_client()
        for district in ["Hassan", "Mysuru", "Belagavi", "Ballari", "Dakshina Kannada"]:
            response = client.post(
                "/api/analyze",
                json={"crop": "Tomato", "location": district, "quantity": 10},
            )
            self.assertEqual(response.status_code, 200, district)
            payload = response.get_json()
            self.assertTrue(payload["location"].endswith("Karnataka"), payload)


if __name__ == "__main__":
    unittest.main()
