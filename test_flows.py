"""
Automated Integration Test for Cooky Choice Rice WhatsApp Automation Flows.
"""
import sys
import asyncio

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from bot_engine import handle_incoming_message
from database import get_all_orders, get_wholesale_rates, update_wholesale_rate

async def run_tests():
    phone = "+919988776655"
    name = "Vikram Sharma"
    print("==================================================")
    print("1. Testing Main Menu:")
    resp = await handle_incoming_message(phone, "Hi", name)
    print(resp)
    assert "Welcome to Cooky Choice Rice" in resp

    print("\n==================================================")
    print("2. Testing Catalog Browsing (Option 1):")
    resp = await handle_incoming_message(phone, "1", name)
    print(resp)
    assert "Product Catalog" in resp

    print("\n==================================================")
    print("3. Testing Select Product 1 (Royal 1121):")
    resp = await handle_incoming_message(phone, "1", name)
    print(resp)
    assert "Select Pack Size" in resp

    print("\n==================================================")
    print("4. Testing Select Variant 2 (5 kg Bag):")
    resp = await handle_incoming_message(phone, "2", name)
    print(resp)
    assert "How many bags/pouches" in resp

    print("\n==================================================")
    print("5. Testing Enter Qty 2:")
    resp = await handle_incoming_message(phone, "2", name)
    print(resp)
    assert "Added to Cart" in resp

    print("\n==================================================")
    print("6. Testing Checkout:")
    resp = await handle_incoming_message(phone, "CHECKOUT", name)
    print(resp)
    assert "Delivery Address" in resp

    print("\n==================================================")
    print("7. Testing Enter Address:")
    resp = await handle_incoming_message(phone, "Flat 402, Green Valley Apts, Sector 14, Gurgaon 122001", name)
    print(resp)
    assert "ORDER BOOKED SUCCESSFULLY" in resp

    orders = get_all_orders()
    assert len(orders) > 0
    latest_order_code = orders[0]["order_code"]
    print(f"\nOrder created with code: {latest_order_code}")

    print("\n==================================================")
    print("8. Testing WhatsApp Catalog & Price Request:")
    resp = await handle_incoming_message(phone, "Show catalog", name)
    print(resp)
    assert "Product Catalog & Prices" in resp

    print("\n==================================================")
    print("9. Testing Wholesale Rate Card (Wholesale):")
    resp = await handle_incoming_message(phone, "Wholesale", name)
    print(resp)
    assert "Official Wholesale Rate Card" in resp

    print("\n==================================================")
    print("10. Testing Wholesale Quote Request (QUOTE):")
    resp = await handle_incoming_message(phone, "QUOTE", name)
    print(resp)
    assert "Wholesale Bulk Quote Request" in resp

    resp = await handle_incoming_message(phone, "1", name) # Royal 1121
    print(resp)
    assert "What quantity do you require" in resp

    resp = await handle_incoming_message(phone, "50 Bags (25kg each)", name)
    print(resp)
    assert "Destination City" in resp

    resp = await handle_incoming_message(phone, "Jaipur, Rajasthan", name)
    print(resp)
    assert "Business Details" in resp

    resp = await handle_incoming_message(phone, "Jaipur Grain Mart - Mr. Vikram", name)
    print(resp)
    assert "WHOLESALE QUOTATION TICKET GENERATED" in resp

    print("\n==================================================")
    print("11. Testing AI Rice Advisor (Dish recommendation):")
    resp = await handle_incoming_message(phone, "Which rice is best for biryani?", name)
    print(resp)
    assert "Royal 1121 XXL Basmati" in resp

    print("\n==================================================")
    print("12. Testing AI Rice Advisor (Diabetes / Health):")
    resp = await handle_incoming_message(phone, "Do you have rice for diabetes or sugar patients?", name)
    print(resp)
    assert "Brown Basmati" in resp

    print("\n==================================================")
    print("13. Testing Admin Wholesale Rate Update:")
    update_wholesale_rate(product_id=1, rate_per_unit=112.50, moq="15 Quintals", unit="per kg (ex-mill)", note="New premium harvest")
    rates = get_wholesale_rates()
    prod1_rate = next(r for r in rates if r["product_id"] == 1)
    assert prod1_rate["rate_per_unit"] == 112.50
    print(f"Product 1 updated rate: Rs.{prod1_rate['rate_per_unit']}/kg")

    print("\n==================================================")
    print("ALL 13 TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    asyncio.run(run_tests())
