"""
Seed script for Cooky Choice Rice catalog, packaging sizes, wholesale rate card, and FAQs.
"""
from database import init_db, get_connection

def seed_database():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing demo data
    cursor.execute("DELETE FROM faqs")
    cursor.execute("DELETE FROM wholesale_rates")
    cursor.execute("DELETE FROM variants")
    cursor.execute("DELETE FROM products")

    products = [
        {
            "name": "Cooky Choice Royal 1121 XXL Basmati Rice",
            "category": "Basmati Special",
            "description": "Premium aged 8.35mm+ long grain basmati with royal aroma. Elongates over 2x upon cooking without breaking.",
            "cooking_tips": "Soak in cold water for 35 mins. Cook with 1:2 water ratio. Best for Royal Biryani, Mughlai Pulao, and special dinner parties.",
            "variants": [
                ("1 kg Pouch", 140.0),
                ("5 kg Bag", 680.0),
                ("10 kg Bag", 1320.0),
                ("25 kg Bag", 3150.0)
            ],
            "wholesale": {
                "moq": "10 Quintals (1,000 kg)",
                "rate": 105.0,
                "unit": "per kg (ex-mill)",
                "note": "Grade A+ Sortex cleaned, 2-year aged stock."
            }
        },
        {
            "name": "Cooky Choice Super Tibar Basmati Rice",
            "category": "Basmati Everyday",
            "description": "Medium-long 7.2mm aged basmati with authentic rich fragrance. Fluffy and aromatic for weekly enjoyment.",
            "cooking_tips": "Soak 20-25 mins. Perfect for Dum Biryani, Chicken Pulao, Fried Rice, and Jeera Rice.",
            "variants": [
                ("1 kg Pouch", 105.0),
                ("5 kg Bag", 500.0),
                ("10 kg Bag", 970.0),
                ("25 kg Bag", 2350.0)
            ],
            "wholesale": {
                "moq": "10 Quintals (1,000 kg)",
                "rate": 82.0,
                "unit": "per kg (ex-mill)",
                "note": "Sortex cleaned, consistent grain quality."
            }
        },
        {
            "name": "Cooky Choice Classic Sona Masoori (Aged)",
            "category": "Daily South Indian",
            "description": "Lightweight, delicate, non-sticky rice aged over 12 months. Very gentle on the stomach and easy to digest.",
            "cooking_tips": "Cook in pressure cooker with 1:2.5 water for 3 whistles. Best for daily Sambar Rice, Rasam, Curd Rice, and meals.",
            "variants": [
                ("5 kg Bag", 340.0),
                ("10 kg Bag", 650.0),
                ("26 kg Bag (Standard)", 1580.0)
            ],
            "wholesale": {
                "moq": "20 Bags (520 kg)",
                "rate": 1420.0,
                "unit": "per 26 kg Bag",
                "note": "Aged Kurnool/Raichur origin paddy, moisture < 13%."
            }
        },
        {
            "name": "Cooky Choice Premium Wada Kolam (Jeera Rice)",
            "category": "Daily Fragrant",
            "description": "Small, pearly, highly aromatic short grain rice. Soft texture with natural sweet aroma.",
            "cooking_tips": "Wash gently without rubbing. Cook with 1:2 water. Superb for Jeera Rice, Tadka Dal Chawal, and Khichdi.",
            "variants": [
                ("5 kg Bag", 380.0),
                ("10 kg Bag", 740.0),
                ("25 kg Bag", 1750.0)
            ],
            "wholesale": {
                "moq": "15 Bags (375 kg)",
                "rate": 1580.0,
                "unit": "per 25 kg Bag",
                "note": "Double polished, silky soft texture."
            }
        },
        {
            "name": "Cooky Choice Healthy Brown Basmati",
            "category": "Health & Fitness",
            "description": "100% unpolished whole grain basmati with nutrient-rich bran intact. Low glycemic index, ideal for diabetic & fitness diets.",
            "cooking_tips": "Soak 45-60 mins in warm water. Boil with 1:2.5 water for 25 mins. Hearty nutty flavor and rich fiber.",
            "variants": [
                ("1 kg Pouch", 125.0),
                ("5 kg Bag", 590.0)
            ],
            "wholesale": {
                "moq": "5 Quintals (500 kg)",
                "rate": 92.0,
                "unit": "per kg (ex-mill)",
                "note": "Fresh unpolished lot, maximum fiber & nutrients."
            }
        },
        {
            "name": "Cooky Choice Dubar & Mogra Broken Basmati",
            "category": "Economy & Batter",
            "description": "Aromatic broken basmati grains. High fragrance at an economical price point.",
            "cooking_tips": "Cooks fast. Ideal for aromatic Rice Kheer, Pongal, Pithi, and grinding idli/dosa batter.",
            "variants": [
                ("10 kg Bag", 480.0),
                ("25 kg Bag", 1150.0)
            ],
            "wholesale": {
                "moq": "25 Bags (625 kg)",
                "rate": 980.0,
                "unit": "per 25 kg Bag",
                "note": "Popular with restaurants, caterers, and food joints."
            }
        }
    ]

    for p in products:
        cursor.execute("""
            INSERT INTO products (name, category, description, cooking_tips, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (p["name"], p["category"], p["description"], p["cooking_tips"]))
        prod_id = cursor.lastrowid

        for size, price in p["variants"]:
            cursor.execute("""
                INSERT INTO variants (product_id, pack_size, retail_price, in_stock)
                VALUES (?, ?, ?, 1)
            """, (prod_id, size, price))

        ws = p["wholesale"]
        cursor.execute("""
            INSERT INTO wholesale_rates (product_id, moq, rate_per_unit, unit, note)
            VALUES (?, ?, ?, ?, ?)
        """, (prod_id, ws["moq"], ws["rate"], ws["unit"], ws["note"]))

    # Seed common rice knowledge FAQs
    faqs = [
        ("Biryani Advice", "Which rice is best for Biryani?", "biryani,dum,special,longest", 
         "For restaurant-style dum biryani, our **Cooky Choice Royal 1121 XXL Basmati** is the champion. The grains elongate to over 22mm when cooked, remain separated, and absorb ghee and spices wonderfully."),
        
        ("Daily Cooking", "Which rice is best for daily lunch / South Indian meals?", "daily,lunch,sambar,curd,regular", 
         "For everyday meals, our **Cooky Choice Classic Sona Masoori (Aged)** is the #1 customer favorite. It is lightweight, non-sticky, very easy to digest, and pairs perfectly with dal, sambar, and curries."),
         
        ("Health & Diet", "Do you have rice for diabetes or weight loss?", "diet,sugar,diabetes,healthy,weight,brown", 
         "Yes! Our **Cooky Choice Healthy Brown Basmati** has a low glycemic index (Low GI) and retains the bran layer loaded with natural fiber, magnesium, and antioxidants. It helps maintain steady blood sugar levels."),
        
        ("Wholesale & Dealership", "How does wholesale / dealership work?", "dealership,wholesale,bulk,distributor,agency", 
         "We supply direct from mill to wholesalers, supermarkets, and caterers across India. Minimum wholesale orders start from 10 Bags or 5 Quintals. We offer customized white-labeling and transport dispatch support."),
         
        ("Quality & Mill", "Where is Cooky Choice milled and are you certified?", "fssai,quality,mill,certificate,pure", 
         "Cooky Choice Rice is processed in ISO 22000 & FSSAI certified high-tech Buhler Sortex milling plants. Every single lot undergoes 7-stage quality checks: moisture testing, sortex cleaning, and grain elongation tests.")
    ]

    for cat, q, kw, a in faqs:
        cursor.execute("""
            INSERT INTO faqs (category, question, keywords, answer)
            VALUES (?, ?, ?, ?)
        """, (cat, q, kw, a))

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully with Cooky Choice Rice catalog!")

if __name__ == "__main__":
    seed_database()
