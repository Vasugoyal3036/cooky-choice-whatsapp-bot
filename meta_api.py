"""
Meta WhatsApp Cloud API Client.
Handles official Meta Cloud API Webhook verification, payload parsing, and message sending.
Zero platform cost: Uses Meta's free tier of 1,000 monthly service conversations!
"""
import logging
import httpx
from typing import Dict, Any, Optional
from config import (
    META_WA_PHONE_NUMBER_ID,
    META_WA_ACCESS_TOKEN,
    META_WA_VERIFY_TOKEN,
    META_WA_API_VERSION
)

logger = logging.getLogger(__name__)

def verify_meta_webhook(mode: str, token: str, challenge: str) -> Optional[str]:
    """
    Validates Meta webhook subscription handshake.
    """
    if mode == "subscribe" and token == META_WA_VERIFY_TOKEN:
        logger.info("Meta Webhook verification succeeded.")
        return challenge
    logger.warning("Meta Webhook verification failed. Token mismatch.")
    return None

def parse_incoming_webhook_payload(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Parses incoming Meta WhatsApp webhook payload.
    Extracts phone number, customer name, and text message.
    """
    try:
        entries = payload.get("entry", [])
        if not entries:
            return None

        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])

                if not messages:
                    continue

                msg = messages[0]
                phone_number = msg.get("from")
                msg_type = msg.get("type")

                customer_name = ""
                if contacts:
                    customer_name = contacts[0].get("profile", {}).get("name", "")

                text_content = ""
                if msg_type == "text":
                    text_content = msg.get("text", {}).get("body", "")
                elif msg_type == "interactive":
                    interactive = msg.get("interactive", {})
                    itype = interactive.get("type")
                    if itype == "button_reply":
                        text_content = interactive.get("button_reply", {}).get("title", "")
                    elif itype == "list_reply":
                        text_content = interactive.get("list_reply", {}).get("id", "") or interactive.get("list_reply", {}).get("title", "")
                elif msg_type == "button":
                    text_content = msg.get("button", {}).get("text", "")
                elif msg_type == "order":
                    # WhatsApp Native Catalog Order event
                    order_data = msg.get("order", {})
                    items = order_data.get("product_items", [])
                    item_strs = []
                    for it in items:
                        item_strs.append(f"{it.get('quantity', 1)}x SKU:{it.get('product_retailer_id', '')} (@Rs.{it.get('item_price', '')})")
                    notes = order_data.get("text", "")
                    text_content = f"CATALOG_ORDER: {', '.join(item_strs)}" + (f" | Note: {notes}" if notes else "")

                if phone_number and text_content:
                    return {
                        "phone_number": phone_number,
                        "customer_name": customer_name,
                        "message_text": text_content
                    }
        return None
    except Exception as e:
        logger.error(f"Error parsing Meta payload: {e}")
        return None

async def send_whatsapp_message(to_phone: str, text: str) -> bool:
    """
    Sends a WhatsApp message via Meta Cloud API.
    """
    if not META_WA_PHONE_NUMBER_ID or not META_WA_ACCESS_TOKEN:
        logger.info(f"[SIMULATION / LOG] To {to_phone}: {text[:80]}... (Meta credentials not configured in .env)")
        return False

    url = f"https://graph.facebook.com/{META_WA_API_VERSION}/{META_WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_WA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                return True
            else:
                logger.error(f"Meta API error {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Exception sending WhatsApp message: {e}")
        return False
