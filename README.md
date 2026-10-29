# 🌾 Cooky Choice Rice — WhatsApp Automation System

A production-ready, **100% Free-of-Cost** WhatsApp Automation platform designed specifically for a modern Rice Brand & Milling company (**Cooky Choice Rice**).

It handles both **Direct-to-Consumer (B2C)** retail pack orders and **B2B Wholesale / Distributor** bulk inquiries, backed by an **AI-powered Rice Advisor** and an **Operations Admin Console**.

---

## 🌟 Key Features

### 1. 🌾 Interactive B2C Retail Catalog & Quick Ordering
- Browse brand varieties: *Royal 1121 XXL Basmati, Super Tibar Basmati, Classic Sona Masoori, Wada Kolam / Jeera Rice, Brown Basmati, and Dubar Broken Rice*.
- Multi-pack sizing (*1 kg, 5 kg, 10 kg, 26 kg, 25 kg bags*).
- Interactive Cart management with subtotal calculation and free delivery threshold.
- Instant automated Order ID generation (`RET-261029-101`) with delivery address capture.

### 2. 🏭 Live Wholesale Daily Rate Card & B2B Inquiry Desk
- Real-time wholesale rate card with effective dates, sortex specs, and Minimum Order Quantities (MOQs).
- Generates official wholesale quotation tickets (`WHL-261029-102`) capturing buyer volume, destination city, and firm name.
- Direct notification to the mill dispatch manager.

### 3. 🤖 AI-Powered Rice Cooking Advisor & Knowledge Engine
- Recommends the exact rice variety based on the dish (e.g. *Royal 1121 for Royal Dum Biryani, Sona Masoori for daily meals & sambar, Kolam for Jeera rice, Brown Rice for diabetic/fitness diets*).
- Provides soaking time, water ratios, storage shelf-life advice, and certifications (ISO 22000, FSSAI).
- **Dual-Engine Architecture:**
  - **Zero-Cost Built-In Knowledge Engine:** Works 100% offline, requires 0 API keys and $0 forever.
  - **Gemini AI Engine (Optional):** Plug in a free Google AI Studio key for open-ended conversational intelligence.

### 4. 📦 Live Order Tracking
- Customers can track orders at any time by sending their Order ID (e.g., `RET-261029-101`) or typing `TRACK` or `MY ORDERS`.
- Displays real-time status: *Received & Verified at Mill ➔ Confirmed & In Packing ➔ Dispatched via Transport ➔ Delivered*.

### 5. 🖥️ Brand Owner Operations Console (`/admin`)
- **Live Wholesale Rate Card Editor:** Change today's wholesale rice rates with 1 click; updates reflect immediately in WhatsApp for all buyers.
- **Order & Lead Tracker:** Live dashboard of all B2C retail orders and B2B wholesale quotation leads with direct WhatsApp contact buttons.
- **Status Changer:** Update dispatch stages on the fly.

### 6. 📱 Built-in WhatsApp Web Simulator (`/`)
- Test and demo the entire automation end-to-end directly in your web browser with zero configuration!

---

## 💰 Why It Is 100% Free of Cost

| Component | Traditional WhatsApp Tools (Wati / Aisensy) | **Cooky Choice Custom Engine** |
| :--- | :--- | :--- |
| **Platform Subscription** | $30 – $120 / month (₹2,500 – ₹10,000/mo) | **₹0 Free** (Self-hosted) |
| **Meta Service Conversations** | Additional markups per chat | **1,000 Free Chats / month** (Meta Official Tier) |
| **Database** | Paid SaaS database | **₹0** (Built-in SQLite) |
| **AI Assistant** | Expensive per-query charges | **₹0 Free** (Built-in NLP + Free Gemini Tier) |

---

## 🚀 Quick Start Guide

### Step 1: Start the Server
Double-click `start.bat` or run in PowerShell:
```powershell
python main.py
```

### Step 2: Open in Your Browser
- **WhatsApp Chat Simulator:** Open [http://localhost:8000](http://localhost:8000)
- **Brand Owner Admin Dashboard:** Open [http://localhost:8000/admin](http://localhost:8000/admin)

### Step 3: Run Automated Tests
Verify all 13 core flows with:
```powershell
python test_flows.py
```

---

## 📲 Connecting Real WhatsApp (Meta WhatsApp Cloud API)

To connect this automation to a live WhatsApp Business number at **₹0 cost**:

1. **Create Free Meta App:**
   - Go to [developers.facebook.com](https://developers.facebook.com) and sign in.
   - Click **My Apps** ➔ **Create App** ➔ Select **Other** ➔ Choose **Business**.
   - Add the **WhatsApp** product.

2. **Expose your local server (for testing):**
   - Use free [ngrok](https://ngrok.com) or [Cloudflare Tunnel](https://developers.cloudflare.com/pages/how-to/preview-with-cloudflare-tunnel/):
     ```bash
     ngrok http 8000
     ```
   - Copy the forwarding HTTPS URL (e.g., `https://abc-123.ngrok-free.app`).

3. **Configure Webhook in Meta App:**
   - Under **WhatsApp** ➔ **Configuration** ➔ **Webhook**:
     - **Callback URL:** `https://your-ngrok-url.ngrok-free.app/webhook`
     - **Verify Token:** `cooky_choice_webhook_secret_2026`
   - Click **Verify and Save**.
   - In Webhook Fields, click **Manage** and subscribe to `messages`.

4. **Update `.env`:**
   - Add your `META_WA_PHONE_NUMBER_ID` and `META_WA_ACCESS_TOKEN` in `.env`.
   - All WhatsApp messages to your business number will now be automatically processed by Cooky Choice Bot!

---

## 📂 Project Architecture

```
cooky_choice_whatsapp_automation/
├── config.py              # Configuration & environment variables
├── database.py            # SQLite schema, catalog, sessions & orders
├── catalog_seed.py        # Seed script for rice products & rate card
├── ai_assistant.py        # Dual-engine AI advisor (Zero-cost built-in + Gemini)
├── bot_engine.py          # WhatsApp state machine & conversational flow
├── meta_api.py            # Official Meta Cloud API webhook & sender
├── main.py                # FastAPI server, endpoints & simulator APIs
├── test_flows.py          # 13 automated end-to-end integration tests
├── start.bat              # One-click Windows starter
├── templates/
│   ├── index.html         # High-fidelity WhatsApp Web Simulator
│   └── admin.html         # Brand Owner Admin Console & Rate Manager
├── .env                   # Live settings
└── requirements.txt       # Dependencies
```
