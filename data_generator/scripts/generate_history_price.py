import csv
import os
from dotenv import load_dotenv
import random
from datetime import date, timedelta
import requests
load_dotenv()

API_URL = os.getenv("API_URL")
OUTPUT_FILE = "data_generator/output/price_history.csv"

# Rentang periode price history
PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 6, 30)   # titik terakhir per produk

# Jumlah titik harga per produk
# Weighted supaya rata-rata sekitar 3-3.5 titik/produk
NUM_POINTS_CHOICES = [1, 2, 3, 4, 5, 6]
NUM_POINTS_WEIGHTS = [1, 2, 4, 4, 2, 1]

# Variasi harga titik paling lama dibanding current_price
OLDEST_PRICE_MIN_RATIO = 0.92
OLDEST_PRICE_MAX_RATIO = 0.95

random.seed(42)


def fetch_products():
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def generate_effective_dates(num_points: int, start: date, end: date):
    """
    Generate `num_points` tanggal untuk satu produk.

    - Kalau num_points == 1: cuma 1 tanggal, di paruh kedua periode
      (current_price dianggap berlaku sejak titik itu, tidak pernah berubah
      sebelumnya).
    - Kalau num_points > 1: (num_points - 1) tanggal tersebar di paruh
      PERTAMA periode (harga-harga lama), lalu 1 tanggal terakhir di paruh
      KEDUA periode (titik current_price).
    """
    total_days = (end - start).days
    midpoint = total_days // 2

    if num_points == 1:
        offset = random.randint(midpoint, total_days)
        return [start + timedelta(days=offset)]

    earlier_offsets = set()
    while len(earlier_offsets) < num_points - 1:
        earlier_offsets.add(random.randint(0, midpoint))
    offsets = sorted(earlier_offsets)

    latest_offset = random.randint(midpoint, total_days)
    offsets.append(latest_offset)

    return [start + timedelta(days=o) for o in offsets]


def generate_prices(current_price: float, num_points: int):
    """
    Generate `num_points` harga untuk satu produk.

    Titik terakhir = current_price.
    Titik-titik sebelumnya (kalau ada) dibuat dengan sedikit random walk,
    dimulai dari harga yang cukup lebih murah dari current_price.
    """
    if num_points == 1:
        return [current_price]

    prices = []
    price = round(current_price * random.uniform(OLDEST_PRICE_MIN_RATIO, OLDEST_PRICE_MAX_RATIO), 2)
    prices.append(price)

    for _ in range(num_points - 2):
        change_pct = random.uniform(-0.05, 0.08)
        price = round(price * (1 + change_pct), 2)
        prices.append(price)

    prices.append(current_price)
    return prices


def generate_price_history(products):
    rows = []

    for product in products:
        product_id = product["id"]
        current_price = round(product["price"], 2)

        num_points = random.choices(NUM_POINTS_CHOICES, weights=NUM_POINTS_WEIGHTS)[0]

        dates = generate_effective_dates(num_points, PERIOD_START, PERIOD_END)
        prices = generate_prices(current_price, num_points)

        for d, p in zip(dates, prices):
            rows.append(
                {
                    "product_id": product_id,
                    "effective_date": d.isoformat(),
                    "price": p,
                }
            )

    rows.sort(key=lambda r: (r["effective_date"]))
    return rows


def save_to_csv(rows, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id", "effective_date", "price"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("Fetching produk dari Fake Store API...")
    products = fetch_products()

    print("Generating price history...")
    rows = generate_price_history(products)

    save_to_csv(rows, OUTPUT_FILE)
    print(f"{OUTPUT_FILE}")


if __name__ == "__main__":
    main()