"""
AI Rice Assistant and Knowledge Engine.
Supports:
1. Zero-cost built-in expert matcher (requires 0 API keys, completely free forever).
2. Gemini API LLM integration (optional free tier via Google AI Studio).
"""
import re
import json
import httpx
from typing import Dict, Any, List
from config import GEMINI_API_KEY, BRAND_NAME, BRAND_PHONE, BRAND_EMAIL
from database import get_active_products, get_wholesale_rates, get_connection

SYSTEM_PROMPT_TEMPLATE = """
You are the master Rice Sommelier and Sales Consultant for "{brand_name}".
Your job is to provide warm, knowledgeable, and polite guidance to WhatsApp customers.

Brand Details:
- Brand Name: {brand_name}
- Contact Phone: {brand_phone}
- Email: {brand_email}

Active Products & Retail Packs:
{catalog_text}

Wholesale Rates & Minimum Order Quantities (MOQs):
{wholesale_text}

Guidelines:
1. Be concise and friendly. Format with WhatsApp-friendly markdown (*bold*, bullet points, emojis).
2. Suggest the right rice variety based on the dish (e.g. Royal 1121 for Royal Biryani, Sona Masoori for Daily South Indian/Sambar, Kolam for Jeera Rice/Dal, Brown Rice for diabetic/fitness diets).
3. Always mention pack sizes and prices when recommending a variety.
4. If the customer asks for bulk, commercial, dealer, or wholesale rates, share the wholesale rates and guide them to reply 'QUOTE' to get an official mill dispatch quote.
5. If you do not know an exact answer, invite them to reply 'AGENT' to speak with the sales head.
"""

def get_catalog_context() -> str:
    products = get_active_products()
    lines = []
    for p in products:
        variants_str = ", ".join([f"{v['pack_size']}: Rs.{v['retail_price']:.0f}" for v in p.get("variants", [])])
        lines.append(f"- {p['name']} ({p['category']}): {p['description']}. Packs: [{variants_str}]. Tips: {p['cooking_tips']}")
    return "\n".join(lines)

def get_wholesale_context() -> str:
    rates = get_wholesale_rates()
    lines = []
    for r in rates:
        lines.append(f"- {r['product_name']}: Rs.{r['rate_per_unit']:.2f} {r['unit']} (MOQ: {r['moq']}). Spec: {r.get('note', '')}")
    return "\n".join(lines)

def rule_based_rice_advisor(user_message: str) -> str:
    """
    Intelligent 100% free offline knowledge engine.
    Scans for intent, dish types, rice varieties, and FAQs.
    """
    msg = user_message.lower().strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs")
    faqs = cursor.fetchall()
    conn.close()

    # 1. Match FAQs by keyword
    best_faq_match = None
    max_score = 0
    for faq in faqs:
        keywords = [k.strip().lower() for k in faq["keywords"].split(",") if k.strip()]
        score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', msg))
        if score > max_score and score >= 1:
            max_score = score
            best_faq_match = faq["answer"]

    if best_faq_match and max_score >= 1:
        return (
            f"💡 *{BRAND_NAME} Rice Advice:*\n\n"
            f"{best_faq_match}\n\n"
            "💬 *Quick Actions:*\n"
            "• Reply *1* to browse and order this rice\n"
            "• Reply *2* for wholesale bulk rates\n"
            "• Reply *MENU* to view main options"
        )

    # 2. Specific Dish Recommendations
    if any(k in msg for k in ["biryani", "pulao", "biriyani", "dum"]):
        return (
            f"👑 *Best Rice for Biryani & Pulao:*\n\n"
            f"For authentic royal dum biryani, we recommend our flagship **Cooky Choice Royal 1121 XXL Basmati Rice**!\n\n"
            "✨ *Why choose Royal 1121:*\n"
            "• Grain length: 8.35mm+ aged basmati\n"
            "• Elongates up to 2.5x after boiling without breaking\n"
            "• Zero stickiness, perfect fluffiness and royal aroma\n\n"
            "📦 *Available Sizes:* 1kg (Rs.140), 5kg (Rs.680), 10kg (Rs.1,320), 25kg (Rs.3,150)\n\n"
            "👉 Reply *1* to place an order or *MENU* for all options."
        )

    if any(k in msg for k in ["sambar", "curd rice", "daily", "south indian", "rasam", "regular meals"]):
        return (
            f"🌾 *Best Rice for Everyday Meals & Sambar Rice:*\n\n"
            f"Our **Cooky Choice Classic Sona Masoori (Aged 12+ Months)** is the top choice for everyday cooking!\n\n"
            "✨ *Highlights:*\n"
            "• Delicate, non-sticky grains, very gentle on digestion\n"
            "• Naturally aged for superior fluffiness and taste\n"
            "• Ideal for lunchboxes, sambar rice, rasam, and daily dal\n\n"
            "📦 *Available Sizes:* 5kg (Rs.340), 10kg (Rs.650), 26kg Standard Bag (Rs.1,580)\n\n"
            "👉 Reply *1* to order now."
        )

    if any(k in msg for k in ["jeera rice", "khichdi", "dal", "kolam"]):
        return (
            f"🍚 *Best Rice for Jeera Rice & Khichdi:*\n\n"
            f"Try our **Cooky Choice Premium Wada Kolam (Jeera Rice)**!\n\n"
            "✨ *Highlights:*\n"
            "• Small pearly white grains with natural subtle sweetness\n"
            "• Tender, melt-in-mouth texture\n"
            "• Loved for restaurant-style Jeera Rice, Tadka Dal, and Khichdi\n\n"
            "📦 *Available Sizes:* 5kg (Rs.380), 10kg (Rs.740), 25kg (Rs.1,750)\n\n"
            "👉 Reply *1* to add to cart."
        )

    if any(k in msg for k in ["diabetes", "sugar", "diet", "weight", "gym", "fitness", "brown"]):
        return (
            f"🥗 *Best Healthy Rice for Diabetes & Weight Control:*\n\n"
            f"Our **Cooky Choice Healthy Brown Basmati Rice** is 100% whole grain with bran intact!\n\n"
            "✨ *Health Benefits:*\n"
            "• Low Glycemic Index (Low GI) prevents sudden insulin spikes\n"
            "• Rich in dietary fiber, selenium, and magnesium\n"
            "• Keeps you feeling full for longer hours\n\n"
            "📦 *Available Sizes:* 1kg (Rs.125), 5kg (Rs.590)\n\n"
            "👉 Reply *1* to order health pack."
        )

    if any(k in msg for k in ["kheer", "payasam", "batter", "idli", "dosa", "broken"]):
        return (
            f"🥣 *Best for Kheer, Desserts & Batter:*\n\n"
            f"Our **Cooky Choice Dubar & Mogra Broken Basmati** is rich in starch and aroma!\n\n"
            "✨ *Highlights:*\n"
            "• Thickens kheer and sweet dishes into rich creamy texture\n"
            "• Economical price for high-volume commercial batters\n\n"
            "📦 *Available Sizes:* 10kg (Rs.480), 25kg (Rs.1,150)\n\n"
            "👉 Reply *1* to order."
        )

    if any(k in msg for k in ["shelf life", "expiry", "store", "storage"]):
        return (
            f"📦 *Storage & Shelf Life Advice:*\n\n"
            "• *Shelf Life:* Cooky Choice Rice has a shelf life of *24 months* from the packaging date when stored in cool, dry conditions.\n"
            "• *Storage Tip:* Store in an airtight container away from moisture and direct sunlight. Adding a few dried neem leaves or cloves keeps natural insects away.\n\n"
            "👉 Reply *MENU* to view options."
        )

    # Default fallback
    return (
        f"🤖 *Hello from {BRAND_NAME} Rice Advisor!*\n\n"
        "I can help you with:\n"
        "• Which rice is best for Biryani, Daily Meals, or Jeera Rice\n"
        "• Rice recommendations for Diabetes, Fitness, or Weight Loss\n"
        "• Cooking ratios and soaking time advice\n"
        "• Wholesale rates and dealer inquiries\n\n"
        "💬 *Try asking:* _'Which rice is best for mutton biryani?'_ or _'Do you have brown rice for diabetes?'_\n\n"
        "Or reply:\n"
        "• *1* - View Catalog & Buy\n"
        "• *2* - Live Wholesale Rates\n"
        "• *MENU* - Main Menu"
    )

async def ask_rice_ai(user_message: str) -> str:
    """
    Main AI function: checks if GEMINI_API_KEY is available.
    If yes, calls Gemini for deep natural language responses.
    If not, instantly falls back to the zero-cost rule_based_rice_advisor.
    """
    if not GEMINI_API_KEY:
        return rule_based_rice_advisor(user_message)

    try:
        catalog_text = get_catalog_context()
        wholesale_text = get_wholesale_context()
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            brand_name=BRAND_NAME,
            brand_phone=BRAND_PHONE,
            brand_email=BRAND_EMAIL,
            catalog_text=catalog_text,
            wholesale_text=wholesale_text
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System context:\n{system_prompt}\n\nCustomer question: {user_message}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 450
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
            else:
                return rule_based_rice_advisor(user_message)
    except Exception:
        # Graceful fallback on network or API error
        return rule_based_rice_advisor(user_message)
