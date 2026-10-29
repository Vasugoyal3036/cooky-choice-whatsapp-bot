"""
Main FastAPI server for Cooky Choice Rice WhatsApp Automation.
Handles:
- Meta WhatsApp Cloud API webhooks (Free Tier)
- Interactive WhatsApp Web Simulator
- Brand Owner Admin Dashboard (Live Daily Rates, Orders & Wholesale Leads)
"""
import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request, Response, Query, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from config import (
    BRAND_NAME,
    BRAND_TAGLINE,
    BRAND_PHONE,
    BRAND_EMAIL,
    BRAND_ADDRESS,
    META_WA_VERIFY_TOKEN,
    PORT,
    HOST,
    DEBUG
)
from database import (
    init_db,
    get_active_products,
    get_wholesale_rates,
    update_wholesale_rate,
    get_all_orders,
    update_order_status,
    reset_session,
    add_product,
    delete_product,
    toggle_product_status,
    generate_meta_catalog_csv
)
from bot_engine import handle_incoming_message
from meta_api import verify_meta_webhook, parse_incoming_webhook_payload, send_whatsapp_message

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cooky_choice")

app = FastAPI(
    title=f"{BRAND_NAME} WhatsApp Automation",
    description="Official Meta WhatsApp Automation Backend & Admin Dashboard",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Ensure DB is created
init_db()

# -------------------------------------------------------------
# Request Models
# -------------------------------------------------------------
class SimulateMessageRequest(BaseModel):
    phone_number: str
    message_text: str
    sender_name: Optional[str] = ""

class UpdateRateRequest(BaseModel):
    product_id: int
    rate_per_unit: float
    unit: Optional[str] = None
    moq: Optional[str] = None
    note: Optional[str] = None

class UpdateOrderStatusRequest(BaseModel):
    order_id: int
    status: str

class ResetSessionRequest(BaseModel):
    phone_number: str

class VariantItem(BaseModel):
    pack_size: str
    retail_price: float

class WholesaleItem(BaseModel):
    moq: str
    rate: float
    unit: str
    note: Optional[str] = ""

class CreateProductRequest(BaseModel):
    name: str
    category: str
    description: str
    cooking_tips: Optional[str] = ""
    variants: List[VariantItem]
    wholesale: Optional[WholesaleItem] = None

# -------------------------------------------------------------
# Web Views (Simulator & Admin Dashboard)
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def simulator_view(request: Request):
    """
    Interactive WhatsApp Web Simulator for instant zero-setup testing.
    """
    context = {
        "brand_name": BRAND_NAME,
        "brand_tagline": BRAND_TAGLINE,
        "brand_phone": BRAND_PHONE,
        "brand_email": BRAND_EMAIL,
        "brand_address": BRAND_ADDRESS
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)

@app.get("/admin", response_class=HTMLResponse)
async def admin_view(request: Request):
    """
    Brand Owner Operations Console: Daily Wholesale Rates & Orders.
    """
    wholesale_rates = get_wholesale_rates()
    orders = get_all_orders(limit=100)
    products = get_active_products()

    context = {
        "brand_name": BRAND_NAME,
        "wholesale_rates": wholesale_rates,
        "orders": orders,
        "products": products
    }
    return templates.TemplateResponse(request=request, name="admin.html", context=context)

# -------------------------------------------------------------
# Meta WhatsApp Cloud API Webhook Endpoints
# -------------------------------------------------------------
@app.get("/webhook")
async def meta_webhook_verification(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Meta Developer Hub verification endpoint.
    Called by Meta when setting up or verifying the Webhook URL.
    """
    logger.info(f"Webhook verification request: mode={hub_mode}, verify_token={hub_verify_token}")
    challenge = verify_meta_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")

@app.post("/webhook")
async def meta_webhook_handler(request: Request):
    """
    Receives real incoming WhatsApp messages from Meta Cloud API.
    """
    try:
        payload = await request.json()
        parsed = parse_incoming_webhook_payload(payload)
        if parsed:
            phone_number = parsed["phone_number"]
            customer_name = parsed["customer_name"]
            message_text = parsed["message_text"]

            logger.info(f"Incoming WhatsApp message from {phone_number} ({customer_name}): {message_text}")
            
            # Generate automated response
            bot_reply = await handle_incoming_message(phone_number, message_text, customer_name)
            
            # Send message back to customer on WhatsApp
            await send_whatsapp_message(phone_number, bot_reply)

        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        logger.error(f"Error handling Meta webhook: {e}")
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=200)

# -------------------------------------------------------------
# Simulator & Internal Admin APIs
# -------------------------------------------------------------
@app.post("/api/simulate")
async def simulate_message(req: SimulateMessageRequest):
    """
    Endpoint used by the built-in browser WhatsApp simulator.
    """
    reply = await handle_incoming_message(
        phone_number=req.phone_number,
        message_text=req.message_text,
        sender_name=req.sender_name
    )
    return {"reply": reply}

@app.post("/api/admin/rates")
async def update_rate(req: UpdateRateRequest):
    update_wholesale_rate(
        product_id=req.product_id,
        rate_per_unit=req.rate_per_unit,
        moq=req.moq,
        unit=req.unit,
        note=req.note
    )
    return {"success": True, "message": "Wholesale rate updated successfully"}

@app.post("/api/admin/order-status")
async def change_status(req: UpdateOrderStatusRequest):
    update_order_status(req.order_id, req.status)
    return {"success": True, "message": "Order status updated successfully"}

@app.post("/api/reset-session")
async def reset_phone_session(req: ResetSessionRequest):
    reset_session(req.phone_number)
    return {"success": True, "message": f"Session reset for {req.phone_number}"}

@app.post("/api/admin/products")
async def create_product_endpoint(req: CreateProductRequest):
    variants_dict = [{"pack_size": v.pack_size, "retail_price": v.retail_price} for v in req.variants]
    wholesale_dict = req.wholesale.model_dump() if req.wholesale else None
    prod_id = add_product(
        name=req.name,
        category=req.category,
        description=req.description,
        cooking_tips=req.cooking_tips or "",
        variants=variants_dict,
        wholesale=wholesale_dict
    )
    return {"success": True, "product_id": prod_id, "message": "Product added to catalog successfully"}

@app.post("/api/admin/products/{product_id}/delete")
async def delete_product_endpoint(product_id: int):
    delete_product(product_id)
    return {"success": True, "message": "Product removed from catalog"}

@app.post("/api/admin/products/{product_id}/toggle")
async def toggle_product_endpoint(product_id: int):
    new_status = toggle_product_status(product_id)
    return {"success": True, "is_active": new_status}

@app.get("/api/admin/export-catalog-csv")
async def export_catalog_csv():
    """
    Downloads Meta / WhatsApp Commerce Manager CSV file for direct upload into WhatsApp Business Catalog!
    """
    csv_data = generate_meta_catalog_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cooky_choice_whatsapp_catalog.csv"}
    )

@app.get("/pair", response_class=HTMLResponse)
async def pair_view(request: Request):
    """
    WhatsApp Web QR code pairing page for physical phones.
    """
    ensure_bridge_running()
    context = {"brand_name": BRAND_NAME}
    return templates.TemplateResponse(request=request, name="pair.html", context=context)

@app.get("/api/device/status")
async def get_device_status():
    """
    Returns live QR code image and pairing status from Baileys bridge.
    """
    ensure_bridge_running()
    status_file = BASE_DIR / "whatsapp_bridge" / "qr_status.json"
    if status_file.exists():
        try:
            import json
            data = json.loads(status_file.read_text(encoding="utf-8"))
            return data
        except Exception:
            pass
    return {"status": "STARTING", "message": "Starting WhatsApp Bridge..."}

@app.post("/api/device/disconnect")
async def disconnect_device():
    """
    Clears WhatsApp session so user can scan a new QR code.
    """
    import shutil
    auth_dir = BASE_DIR / "whatsapp_bridge" / "auth_info_baileys"
    if auth_dir.exists():
        shutil.rmtree(auth_dir, ignore_errors=True)
    status_file = BASE_DIR / "whatsapp_bridge" / "qr_status.json"
    if status_file.exists():
        status_file.unlink(missing_ok=True)
    restart_bridge()
    return {"success": True, "message": "WhatsApp device unlinked."}

BRIDGE_PROC = None

def ensure_bridge_running():
    global BRIDGE_PROC
    import subprocess
    import shutil
    if BRIDGE_PROC is None or BRIDGE_PROC.poll() is not None:
        node_cmd = shutil.which("node") or "node"
        if not shutil.which("node") and Path("C:/Users/h/nodejs/node.exe").exists():
            node_cmd = "C:/Users/h/nodejs/node.exe"

        bridge_script = BASE_DIR / "whatsapp_bridge" / "bridge.js"
        if bridge_script.exists():
            env = os.environ.copy()
            if Path("C:/Users/h/nodejs").exists():
                env["PATH"] = "C:\\Users\\h\\nodejs;" + env.get("PATH", "")
            try:
                BRIDGE_PROC = subprocess.Popen(
                    [str(node_cmd), str(bridge_script)],
                    cwd=str(BASE_DIR / "whatsapp_bridge"),
                    env=env
                )
                logger.info(f"Launched WhatsApp Web Multi-Device Bridge subprocess using '{node_cmd}'.")
            except Exception as e:
                logger.error(f"Failed to launch WhatsApp bridge: {e}")

def restart_bridge():
    global BRIDGE_PROC
    if BRIDGE_PROC and BRIDGE_PROC.poll() is None:
        try:
            BRIDGE_PROC.terminate()
        except Exception:
            pass
    BRIDGE_PROC = None
    ensure_bridge_running()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "brand": BRAND_NAME,
        "service": "Cooky Choice Rice WhatsApp Automation"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {BRAND_NAME} WhatsApp Automation Server on http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
