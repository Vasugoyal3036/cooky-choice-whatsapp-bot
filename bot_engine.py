"""
Core WhatsApp Bot Conversation State Machine for Cooky Choice Rice.
Supports hybrid B2C retail orders, B2B wholesale inquiries, AI advice, and order tracking.
"""
from datetime import datetime
from typing import Dict, Any, Tuple
from config import BRAND_NAME, BRAND_TAGLINE, BRAND_PHONE, BRAND_EMAIL, BRAND_ADDRESS
from database import (
    get_active_products,
    get_product,
    get_wholesale_rates,
    get_or_create_session,
    update_session,
    reset_session,
    create_order,
    get_connection
)
from ai_assistant import ask_rice_ai

def get_main_menu_text(customer_name: str = "") -> str:
    greeting = f"Namaste {customer_name}! " if customer_name else "Namaste! "
    return (
        f"🌾 *Welcome to {BRAND_NAME}* 🌾\n"
        f"_{BRAND_TAGLINE}_\n\n"
        f"{greeting}How can we serve you today?\n\n"
        "1️⃣ 🛍️ *Browse Rice Catalog & Prices* (Packs: 1kg, 5kg, 10kg, 26kg)\n"
        "2️⃣ 🏭 *Live Wholesale Rate Card & Bulk Quotes* (Dealers & Wholesalers)\n"
        "3️⃣ 🤖 *Ask Rice Advisor / Cooking Guide* (AI Assistant)\n"
        "4️⃣ 📞 *Mill Location & Contact Sales Head*\n\n"
        "👉 *Reply with a number (1-4)* or tap the **🛍️ View Catalog** button at the top of this chat to browse our visual store!"
    )

def format_cart(cart: list) -> Tuple[str, float]:
    if not cart:
        return "Your cart is currently empty.", 0.0
    lines = ["🛒 *Your Shopping Cart:*"]
    grand_total = 0.0
    for idx, item in enumerate(cart, 1):
        line_total = item["price"] * item["qty"]
        grand_total += line_total
        lines.append(f"{idx}. *{item['product_name']}* ({item['pack_size']})")
        lines.append(f"   Qty: {item['qty']} × Rs.{item['price']:.0f} = *Rs.{line_total:.0f}*")
    lines.append(f"\n💰 *Grand Total:* *Rs.{grand_total:,.0f}*")
    lines.append("🚚 *Free Delivery* on orders above Rs. 999")
    return "\n".join(lines), grand_total

def format_wholesale_rates_text() -> str:
    today_str = datetime.now().strftime("%d %b %Y")
    rates = get_wholesale_rates()
    lines = [
        f"🏭 *{BRAND_NAME} - Official Wholesale Rate Card*",
        f"📅 *Rates Effective:* {today_str} (Subject to market paddy arrivals)\n",
        "Direct Mill Supply • Sortex Cleaned • Buhler Processed\n"
    ]
    for idx, r in enumerate(rates, 1):
        lines.append(
            f"*{idx}. {r['product_name']}*\n"
            f"   • *Wholesale Rate:* Rs.{r['rate_per_unit']:.2f} {r['unit']}\n"
            f"   • *Minimum Order:* {r['moq']}\n"
            f"   • *Quality:* {r.get('note', 'A-Grade sortex')}\n"
        )
    lines.append(
        "💼 *Wholesale Actions:*\n"
        "• Reply *QUOTE* to get an official dispatch quotation with transport\n"
        "• Reply *CALL* to speak directly with our Mill Dispatcher\n"
        "• Reply *MENU* for main menu"
    )
    return "\n".join(lines)

async def handle_incoming_message(phone_number: str, message_text: str, sender_name: str = "") -> str:
    """
    Main processor for inbound WhatsApp text messages.
    Maintains user session state in SQLite.
    """
    text = (message_text or "").strip()
    session = get_or_create_session(phone_number, sender_name)
    state = session.get("current_state", "MAIN_MENU")
    cart = session.get("cart", [])
    temp_data = session.get("temp_data", {})
    customer_name = session.get("customer_name") or sender_name

    lower_text = text.lower()

    # Universal command handlers
    if lower_text in ["menu", "hi", "hello", "start", "namaste", "hey", "restart", "home"]:
        update_session(phone_number, state="MAIN_MENU")
        return get_main_menu_text(customer_name)

    if lower_text in ["cart", "view cart", "basket"]:
        cart_txt, _ = format_cart(cart)
        if not cart:
            return f"{cart_txt}\n\nReply *1* to browse rice catalog and add items."
        return (
            f"{cart_txt}\n\n"
            "Options:\n"
            "• Reply *CHECKOUT* to complete your order\n"
            "• Reply *CLEAR* to empty cart\n"
            "• Reply *1* to add more rice\n"
            "• Reply *MENU* to return to main menu"
        )

    if lower_text in ["clear", "empty cart"]:
        update_session(phone_number, cart=[])
        return "🗑️ Your cart has been cleared.\n\nReply *1* to browse rice or *MENU* for main menu."

    if lower_text in ["agent", "call", "human", "sales", "contact"]:
        return (
            f"📞 *{BRAND_NAME} - Direct Mill Support*\n\n"
            f"• *Sales & Mill Dispatch Desk:* {BRAND_PHONE}\n"
            f"• *Email:* {BRAND_EMAIL}\n"
            f"• *Factory & Packing Unit:* {BRAND_ADDRESS}\n"
            "• *Working Hours:* Mon - Sat, 9:00 AM to 7:30 PM\n\n"
            "Would you like us to have a sales representative call you? "
            "Reply *CALL ME* or reply *MENU* to return to options."
        )

    if lower_text in ["call me"]:
        create_order("CALL_REQUEST", phone_number, customer_name, "Customer requested phone callback from sales desk", 0.0, "")
        return (
            f"✅ Thank you {customer_name}! Our Sales Desk has received your callback request. "
            "One of our executives will call you shortly on this number.\n\n"
            "Reply *MENU* to continue browsing."
        )

    # -------------------------------------------------------------
    # Intelligent Natural Language Reply Engine (Free & Dynamic)
    # -------------------------------------------------------------

    # 1. Native WhatsApp Catalog Order Hook
    if text.startswith("CATALOG_ORDER:"):
        order_summary = text.replace("CATALOG_ORDER:", "").strip()
        temp_data["catalog_order_summary"] = order_summary
        update_session(phone_number, state="CHECKOUT_ADDRESS", temp_data=temp_data)
        return (
            f"🛒 *WhatsApp Catalog Order Received!*\n\n"
            f"Items:\n{order_summary}\n\n"
            f"📍 Please reply with your full *Delivery Address* (Street, Landmark, City & Pincode) "
            "to confirm your booking:"
        )

    # 2. Delivery, Shipping & Payment Questions
    if any(k in lower_text for k in ["cod", "cash on delivery", "delivery", "shipping", "transport", "pincode", "courier", "payment", "upi", "gpay", "phonepe"]):
        return (
            f"🚚 *{BRAND_NAME} Delivery & Payment Policy:*\n\n"
            "• *Shipping:* We dispatch across India via express courier (retail packs) and licensed transport trucks (wholesale orders).\n"
            "• *Free Shipping:* Free delivery on retail orders above Rs. 999.\n"
            "• *Payment Methods:* Cash on Delivery (COD), UPI (GPay/PhonePe/Paytm), and Bank Transfer.\n"
            "• *Dispatch Timeline:* Dispatched within 24 hours directly from our mill.\n\n"
            "👉 Reply *1* to view rice catalog, *2* for wholesale rates, or *MENU*."
        )

    # 3. Direct Natural Language Ordering (e.g., "I want 2 bags of 26kg sona masoori", "order 5kg basmati")
    if any(w in lower_text for w in ["want", "need", "order", "buy", "send", "book", "chahiye", "bhejo"]) and any(r in lower_text for r in ["basmati", "1121", "tibar", "sona", "masoori", "kolam", "brown", "broken", "mogra", "dubar", "kg", "bag"]):
        products = get_active_products()
        matched_prod = None
        for p in products:
            p_name_lower = p["name"].lower()
            if "1121" in lower_text and "1121" in p_name_lower:
                matched_prod = p; break
            elif "tibar" in lower_text and "tibar" in p_name_lower:
                matched_prod = p; break
            elif ("sona" in lower_text or "masoori" in lower_text) and "sona masoori" in p_name_lower:
                matched_prod = p; break
            elif ("kolam" in lower_text or "jeera" in lower_text) and "kolam" in p_name_lower:
                matched_prod = p; break
            elif "brown" in lower_text and "brown" in p_name_lower:
                matched_prod = p; break
            elif ("broken" in lower_text or "mogra" in lower_text or "dubar" in lower_text) and "broken" in p_name_lower:
                matched_prod = p; break
            elif any(part in lower_text for part in p_name_lower.split() if len(part) > 3):
                matched_prod = p; break

        if matched_prod:
            # Find matched pack size
            matched_variant = None
            for v in matched_prod.get("variants", []):
                v_num = "".join(filter(str.isdigit, v["pack_size"]))
                if v_num and f"{v_num}kg" in lower_text.replace(" ", ""):
                    matched_variant = v
                    break
            
            # Default to largest or first variant if not specified
            if not matched_variant and matched_prod.get("variants"):
                matched_variant = matched_prod["variants"][-1]

            # Detect quantity
            import re
            qty_match = re.search(r'\b(\d+)\s*(?:bags?|pack|pouch|packets?|units?|tin)?\b', lower_text)
            qty = int(qty_match.group(1)) if qty_match else 1
            if qty > 50: qty = 1 # Avoid accidental huge numbers

            cart.append({
                "product_id": matched_prod["id"],
                "variant_id": matched_variant["id"],
                "product_name": matched_prod["name"],
                "pack_size": matched_variant["pack_size"],
                "price": matched_variant["retail_price"],
                "qty": qty
            })
            update_session(phone_number, state="CHECKOUT_ADDRESS", cart=cart, customer_name=customer_name)
            cart_txt, grand_total = format_cart(cart)

            return (
                f"✅ *Added to Your Order!*\n"
                f"• {qty} × *{matched_prod['name']}* ({matched_variant['pack_size']}) = Rs.{matched_variant['retail_price'] * qty:.0f}\n\n"
                f"{cart_txt}\n\n"
                f"📍 Please reply with your complete *Delivery Address* (Street, Landmark, City & Pincode) to complete your order:\n"
                f"_(Or reply *CLEAR* to cancel)_"
            )

    # 4. Direct Product Information / Price Inquiry (e.g. "What is the price of sona masoori?", "1121 details")
    for p in get_active_products():
        p_name_lower = p["name"].lower()
        key_identifiers = [p_name_lower]
        if "1121" in p_name_lower: key_identifiers.extend(["1121", "royal basmati"])
        if "tibar" in p_name_lower: key_identifiers.extend(["tibar"])
        if "sona masoori" in p_name_lower: key_identifiers.extend(["sona masoori", "sonamasoori", "masoori"])
        if "kolam" in p_name_lower: key_identifiers.extend(["wada kolam", "kolam", "jeera rice"])
        if "brown" in p_name_lower: key_identifiers.extend(["brown rice", "brown basmati"])
        if "broken" in p_name_lower: key_identifiers.extend(["broken rice", "mogra", "dubar", "kheer rice"])

        if any(k in lower_text for k in key_identifiers):
            variants = p.get("variants", [])
            lines = [
                f"🌾 *{p['name']}*",
                f"_{p['description']}_\n",
                f"👨‍🍳 *Chef Tip:* {p['cooking_tips']}\n",
                "📦 *Available Pack Sizes & Prices:*"
            ]
            for v_idx, v in enumerate(variants, 1):
                lines.append(f"*{v_idx}.* {v['pack_size']} — *Rs.{v['retail_price']:.0f}*")

            temp_data["selected_product_id"] = p["id"]
            temp_data["selected_product_name"] = p["name"]
            update_session(phone_number, state="SELECT_VARIANT", temp_data=temp_data)

            lines.append(f"\n👉 Reply with *Pack Number (1-{len(variants)})* to order, or type _'Order 2 bags of {variants[0]['pack_size']}'_, or *MENU*.")
            return "\n".join(lines)

    # 5. Direct Wholesale / Bulk Rate Inquiry
    if any(k in lower_text for k in ["wholesale", "bulk", "rate card", "rates", "dealer", "distributor", "per ton", "quintal", "lorry", "mandi"]):
        update_session(phone_number, state="WHOLESALE_OPTIONS")
        return format_wholesale_rates_text()

    # 6. Direct Catalog / Price List Request
    if any(k in lower_text for k in ["catalog", "price list", "menu", "varieties", "all rice", "kya kya hai", "list", "bhejo"]):
        products = get_active_products()
        lines = [
            f"🌾 *{BRAND_NAME} - Product Catalog & Prices*",
            "_(You can also view photos and pack sizes anytime by tapping the 🛍️ **'View Catalog'** icon above)_\n",
            "Select a rice variety to view details and pack sizes:\n"
        ]
        for idx, p in enumerate(products, 1):
            starting_price = p["variants"][0]["retail_price"] if p["variants"] else 0
            lines.append(f"*{idx}. {p['name']}* ({p['category']})")
            lines.append(f"   _{p['description']}_")
            lines.append(f"   Starts from: Rs.{starting_price:.0f}\n")
        lines.append("👉 *Reply with the number (1-6)* of the rice you want to view, or type the name directly (e.g. 'Sona Masoori').")
        update_session(phone_number, state="SELECT_PRODUCT")
        return "\n".join(lines)

    # STATE: MAIN_MENU
    if state == "MAIN_MENU":
        if text == "1" or "catalog" in lower_text or "buy" in lower_text or "order" in lower_text:
            products = get_active_products()
            lines = [
                f"🌾 *{BRAND_NAME} - Product Catalog & Prices*",
                "_(You can also tap the 🛍️ **'View Catalog'** icon at the top of this WhatsApp screen to browse photos and bag sizes)_\n",
                "Select a rice variety to view details and pack sizes:\n"
            ]
            for idx, p in enumerate(products, 1):
                starting_price = p["variants"][0]["retail_price"] if p["variants"] else 0
                lines.append(f"*{idx}. {p['name']}* ({p['category']})")
                lines.append(f"   _{p['description']}_")
                lines.append(f"   Starts from: Rs.{starting_price:.0f}\n")
            lines.append("👉 *Reply with number (1-6)* to choose pack sizes, or reply *MENU*.")
            update_session(phone_number, state="SELECT_PRODUCT")
            return "\n".join(lines)

        elif text == "2" or "wholesale" in lower_text or "rate" in lower_text or "bulk" in lower_text:
            update_session(phone_number, state="WHOLESALE_OPTIONS")
            return format_wholesale_rates_text()

        elif text == "3" or "ai" in lower_text or "advisor" in lower_text or "tips" in lower_text or "cooking" in lower_text:
            update_session(phone_number, state="AI_CHAT")
            return (
                f"🤖 *{BRAND_NAME} AI Rice Advisor*\n\n"
                "I am your personal rice cooking and buying guide. You can ask me questions like:\n"
                "• _Which rice is best for Chicken Dum Biryani?_\n"
                "• _What is the difference between 1121 Basmati and Tibar?_\n"
                "• _Do you have sugar-free / low GI rice for diabetes?_\n"
                "• _What is the soaking time and water ratio for Sona Masoori?_\n\n"
                "💬 *What would you like to know?* (Type your question below, or reply *MENU* to exit)"
            )

        elif text == "4" or "contact" in lower_text or "mill" in lower_text:
            return (
                f"🏭 *About {BRAND_NAME}*\n"
                f"_{BRAND_TAGLINE}_\n\n"
                f"📍 *Mill & Packaging:* {BRAND_ADDRESS}\n"
                f"📞 *Sales Desk:* {BRAND_PHONE}\n"
                f"✉️ *Email:* {BRAND_EMAIL}\n"
                "🌾 *Standards:* ISO 22000:2018 & FSSAI Certified\n"
                "🚛 *Dispatch:* Pan-India transport and local courier delivery.\n\n"
                "👉 Reply *1* to order retail packs, *2* for wholesale rates, or *MENU*."
            )
        else:
            # Check if user asked an AI question directly from main menu
            ai_reply = await ask_rice_ai(text)
            return ai_reply

    # STATE: SELECT_PRODUCT
    elif state == "SELECT_PRODUCT":
        products = get_active_products()
        selected_prod = None
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(products):
                selected_prod = products[idx]

        if not selected_prod:
            for p in products:
                if text.lower() in p["name"].lower():
                    selected_prod = p
                    break

        if not selected_prod:
            return "⚠️ Please reply with a valid product number (1 to 6) from the list above, or reply *MENU*."

        temp_data["selected_product_id"] = selected_prod["id"]
        temp_data["selected_product_name"] = selected_prod["name"]

        variants = selected_prod.get("variants", [])
        lines = [
            f"🌾 *{selected_prod['name']}*",
            f"_{selected_prod['description']}_\n",
            f"👨‍🍳 *Chef Tip:* {selected_prod['cooking_tips']}\n",
            "📦 *Select Pack Size:*"
        ]
        for v_idx, v in enumerate(variants, 1):
            lines.append(f"*{v_idx}.* {v['pack_size']} — *Rs.{v['retail_price']:.0f}*")

        lines.append(f"\n👉 Reply with *Pack Number (1-{len(variants)})* to choose, or *M* to view all rice varieties.")
        update_session(phone_number, state="SELECT_VARIANT", temp_data=temp_data)
        return "\n".join(lines)

    # STATE: SELECT_VARIANT
    elif state == "SELECT_VARIANT":
        if lower_text == "m":
            update_session(phone_number, state="MAIN_MENU")
            return get_main_menu_text(customer_name)

        prod_id = temp_data.get("selected_product_id")
        product = get_product(prod_id) if prod_id else None
        if not product:
            update_session(phone_number, state="MAIN_MENU")
            return "Session expired. " + get_main_menu_text(customer_name)

        variants = product.get("variants", [])
        selected_var = None
        if text.isdigit():
            v_idx = int(text) - 1
            if 0 <= v_idx < len(variants):
                selected_var = variants[v_idx]

        if not selected_var:
            return f"⚠️ Please enter a valid number (1 to {len(variants)}) for the pack size, or reply *M* for menu."

        temp_data["selected_variant_id"] = selected_var["id"]
        temp_data["selected_pack_size"] = selected_var["pack_size"]
        temp_data["selected_price"] = selected_var["retail_price"]

        update_session(phone_number, state="ENTER_QTY", temp_data=temp_data)
        return (
            f"Selected: *{product['name']} - {selected_var['pack_size']}* (Rs.{selected_var['retail_price']:.0f})\n\n"
            "🔢 *How many bags/pouches would you like to order?*\n"
            "(Reply with quantity, e.g. *1*, *2*, *5*)"
        )

    # STATE: ENTER_QTY
    elif state == "ENTER_QTY":
        if not text.isdigit() or int(text) <= 0:
            return "⚠️ Please reply with a valid number for quantity (e.g. 1, 2, 5)."

        qty = int(text)
        prod_name = temp_data.get("selected_product_name", "Rice")
        pack_size = temp_data.get("selected_pack_size", "Pack")
        price = temp_data.get("selected_price", 0.0)

        # Append to cart
        cart.append({
            "product_id": temp_data.get("selected_product_id"),
            "variant_id": temp_data.get("selected_variant_id"),
            "product_name": prod_name,
            "pack_size": pack_size,
            "price": price,
            "qty": qty
        })

        line_total = price * qty
        cart_txt, grand_total = format_cart(cart)

        update_session(phone_number, state="CART_ACTION", cart=cart, temp_data={})
        return (
            f"✅ *Added to Cart!*\n"
            f"• {qty} × {prod_name} ({pack_size}) = Rs.{line_total:.0f}\n\n"
            f"{cart_txt}\n\n"
            "👉 *What would you like to do next?*\n"
            "• Reply *1* to Add More Rice\n"
            "• Reply *CHECKOUT* to Place Order\n"
            "• Reply *MENU* for Main Menu"
        )

    # STATE: CART_ACTION
    elif state == "CART_ACTION":
        if text == "1":
            update_session(phone_number, state="MAIN_MENU")
            return await handle_incoming_message(phone_number, "1", sender_name)
        elif lower_text in ["checkout", "order", "2", "yes"]:
            if not cart:
                update_session(phone_number, state="MAIN_MENU")
                return "Your cart is empty. Reply *1* to browse rice varieties."

            if customer_name and customer_name.strip():
                # We already have their name, ask directly for address
                temp_data["checkout_name"] = customer_name
                update_session(phone_number, state="CHECKOUT_ADDRESS", temp_data=temp_data)
                return (
                    f"Great, {customer_name}! 🚚\n\n"
                    "📍 Please reply with your complete *Delivery Address*:\n"
                    "_(Include House/Flat No., Street, Landmark, City & Pincode)_"
                )
            else:
                update_session(phone_number, state="CHECKOUT_NAME")
                return (
                    "🛍️ *Checkout - Step 1 of 2*\n\n"
                    "Please reply with your *Full Name*:"
                )
        else:
            update_session(phone_number, state="MAIN_MENU")
            return get_main_menu_text(customer_name)

    # STATE: CHECKOUT_NAME
    elif state == "CHECKOUT_NAME":
        name = text.strip()
        if len(name) < 2:
            return "Please provide your full name to proceed with the delivery."
        temp_data["checkout_name"] = name
        update_session(phone_number, state="CHECKOUT_ADDRESS", temp_data=temp_data, customer_name=name)
        return (
            f"Thank you, *{name}*! 👍\n\n"
            "📍 *Checkout - Step 2 of 2:*\n"
            "Please reply with your complete *Delivery Address*:\n"
            "_(Include House/Flat No., Street, Landmark, City & Pincode)_"
        )

    # STATE: CHECKOUT_ADDRESS
    elif state == "CHECKOUT_ADDRESS":
        address = text.strip()
        if len(address) < 6:
            return "Please enter a detailed address including street, city, and pincode so our delivery partner can reach you."

        cust_name = temp_data.get("checkout_name") or customer_name or "Valued Customer"
        cart_txt, grand_total = format_cart(cart)

        # Generate order record in SQLite
        order_code = create_order(
            order_type="RETAIL",
            phone_number=phone_number,
            customer_name=cust_name,
            summary=cart_txt,
            total_amount=grand_total,
            address_or_location=address
        )

        # Reset session
        reset_session(phone_number)
        update_session(phone_number, customer_name=cust_name)

        return (
            f"🎉 *ORDER BOOKED SUCCESSFULLY!* 🎉\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔖 *Order ID:* `{order_code}`\n"
            f"👤 *Customer:* {cust_name}\n"
            f"📞 *Mobile:* {phone_number}\n"
            f"📍 *Delivery To:*\n{address}\n\n"
            f"{cart_txt}\n\n"
            f"💳 *Payment Mode:* Cash on Delivery (COD) / UPI Scan on Delivery\n"
            f"🚚 *Estimated Delivery:* 24 - 48 Hours\n\n"
            f"🌾 Freshly packed directly from *{BRAND_NAME}* mill.\n"
            f"Our dispatch team will keep you updated on WhatsApp. Reply *MENU* for main menu."
        )

    # STATE: WHOLESALE_OPTIONS
    elif state == "WHOLESALE_OPTIONS":
        if lower_text in ["quote", "book", "1", "inquiry"]:
            update_session(phone_number, state="WHL_PRODUCT", temp_data={})
            products = get_active_products()
            lines = ["🏭 *Wholesale Bulk Quote Request*\nWhich rice variety are you interested in purchasing?\n"]
            for idx, p in enumerate(products, 1):
                lines.append(f"*{idx}.* {p['name']}")
            lines.append("\n👉 Reply with number (1-6) or type the variety name.")
            return "\n".join(lines)
        elif lower_text in ["call", "2"]:
            update_session(phone_number, state="MAIN_MENU")
            return (
                f"📞 *Direct Mill Dispatch Desk:* {BRAND_PHONE}\n"
                f"Talk directly to our Mill Manager for truckload / container quotes.\n\n"
                "Reply *MENU* for main menu."
            )
        else:
            update_session(phone_number, state="MAIN_MENU")
            return get_main_menu_text(customer_name)

    # STATE: WHL_PRODUCT
    elif state == "WHL_PRODUCT":
        products = get_active_products()
        prod_name = text
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(products):
                prod_name = products[idx]["name"]

        temp_data["whl_product"] = prod_name
        update_session(phone_number, state="WHL_QTY", temp_data=temp_data)
        return (
            f"Selected Variety: *{prod_name}*\n\n"
            "📦 *What quantity do you require?*\n"
            "(e.g., _'25 Bags (26kg each)'_, _'50 Quintals'_, _'1 Full Truckload / 15 MT'_)"
        )

    # STATE: WHL_QTY
    elif state == "WHL_QTY":
        temp_data["whl_qty"] = text.strip()
        update_session(phone_number, state="WHL_CITY", temp_data=temp_data)
        return (
            "📍 *Destination City & State:*\n"
            "Where should this consignment be dispatched? (Needed for freight & GST calculation)"
        )

    # STATE: WHL_CITY
    elif state == "WHL_CITY":
        temp_data["whl_city"] = text.strip()
        update_session(phone_number, state="WHL_NAME", temp_data=temp_data)
        return (
            "🏢 *Business Details:*\n"
            "Please provide your *Firm / Business Name* and your *Name*:\n"
            "_(e.g., Sri Laxmi Traders - Mr. Ramesh)_"
        )

    # STATE: WHL_NAME
    elif state == "WHL_NAME":
        firm_info = text.strip()
        prod = temp_data.get("whl_product", "Assorted Rice")
        qty = temp_data.get("whl_qty", "Bulk")
        city = temp_data.get("whl_city", "India")

        summary = (
            f"WHOLESALE INQUIRY:\n"
            f"• Variety: {prod}\n"
            f"• Required Qty: {qty}\n"
            f"• Destination: {city}\n"
            f"• Firm & Contact: {firm_info}"
        )

        ticket_code = create_order(
            order_type="WHOLESALE_INQUIRY",
            phone_number=phone_number,
            customer_name=firm_info,
            summary=summary,
            total_amount=0.0,
            address_or_location=city
        )

        reset_session(phone_number)
        return (
            f"📋 *WHOLESALE QUOTATION TICKET GENERATED!* 📋\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔖 *Ticket No:* `{ticket_code}`\n"
            f"🏢 *Firm:* {firm_info}\n"
            f"🌾 *Variety:* {prod}\n"
            f"📦 *Volume:* {qty}\n"
            f"📍 *Destination:* {city}\n\n"
            f"✅ Our Mill Dispatch Head will contact you on this WhatsApp number within *30 minutes* "
            f"with the ex-mill rate and best lorry freight charges.\n\n"
            f"For immediate priority dispatch, call us directly at: *{BRAND_PHONE}*.\n\n"
            f"Reply *MENU* to return to main options."
        )

    # STATE: AI_CHAT
    elif state == "AI_CHAT":
        if lower_text in ["menu", "exit", "stop", "back"]:
            update_session(phone_number, state="MAIN_MENU")
            return get_main_menu_text(customer_name)
        ai_reply = await ask_rice_ai(text)
        return (
            f"{ai_reply}\n\n"
            "──────────────────\n"
            "💬 _Ask another question or reply *MENU* to return to options._"
        )

    # Fallback to main menu
    update_session(phone_number, state="MAIN_MENU")
    return get_main_menu_text(customer_name)
