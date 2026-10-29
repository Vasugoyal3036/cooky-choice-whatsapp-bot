import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import pino from 'pino';
import QRCode from 'qrcode';
import fs from 'fs';
import path from 'path';
import http from 'http';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const STATUS_FILE = path.join(__dirname, 'qr_status.json');
const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');
const SERVER_PORT = process.env.PORT || 8000;
const PYTHON_API_URL = `http://127.0.0.1:${SERVER_PORT}/api/simulate`;

function writeStatus(data) {
    try {
        fs.writeFileSync(STATUS_FILE, JSON.stringify(data, null, 2));
    } catch (err) {
        console.error('Error writing status:', err.message);
    }
}

// Initial status
writeStatus({ status: 'STARTING', message: 'Initializing WhatsApp Web Bridge...', updatedAt: Date.now() });

async function sendToPythonBot(phoneNumber, messageText, senderName) {
    return new Promise((resolve) => {
        const payload = JSON.stringify({
            phone_number: phoneNumber,
            message_text: messageText,
            sender_name: senderName || ''
        });

        const req = http.request(PYTHON_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payload)
            },
            timeout: 8000
        }, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(body);
                    resolve(parsed.reply || null);
                } catch (e) {
                    resolve(null);
                }
            });
        });

        req.on('error', (err) => {
            console.error('Error contacting Python bot:', err.message);
            resolve(null);
        });

        req.write(payload);
        req.end();
    });
}

async function startWhatsAppBridge() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: false,
        logger: pino({ level: 'silent' }),
        browser: ['Cooky Choice Automation', 'Chrome', '1.0.0']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n[BRIDGE] New QR Code generated! Ready to scan.');
            try {
                const qrDataUrl = await QRCode.toDataURL(qr, { margin: 2, scale: 8 });
                writeStatus({
                    status: 'QR_READY',
                    qrImage: qrDataUrl,
                    qrRaw: qr,
                    updatedAt: Date.now()
                });
            } catch (err) {
                console.error('Failed to generate QR data URL:', err);
            }
        }

        if (connection === 'open') {
            const userPhone = sock.user?.id ? sock.user.id.split(':')[0] : 'Unknown';
            const userName = sock.user?.name || 'Cooky Choice Rice';
            console.log(`\n🎉 [BRIDGE] WhatsApp Device Paired! Logged in as: +${userPhone} (${userName})\n`);

            writeStatus({
                status: 'CONNECTED',
                phone: userPhone,
                name: userName,
                updatedAt: Date.now()
            });
        }

        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('[BRIDGE] Connection closed. Reconnecting:', shouldReconnect);

            if (shouldReconnect) {
                writeStatus({ status: 'RECONNECTING', updatedAt: Date.now() });
                setTimeout(startWhatsAppBridge, 3000);
            } else {
                writeStatus({ status: 'LOGGED_OUT', updatedAt: Date.now() });
                console.log('[BRIDGE] Logged out. Clearing session for fresh QR...');
                try {
                    fs.rmSync(AUTH_DIR, { recursive: true, force: true });
                } catch (e) {}
                setTimeout(startWhatsAppBridge, 2000);
            }
        }
    });

    // Listen to incoming messages
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            // Ignore messages sent by ourselves or status broadcasts
            if (!msg.message || msg.key.fromMe || msg.key.remoteJid === 'status@broadcast') continue;

            const jid = msg.key.remoteJid;
            const rawPhone = jid.split('@')[0];
            const senderName = msg.pushName || '';

            let text = '';
            if (msg.message.conversation) {
                text = msg.message.conversation;
            } else if (msg.message.extendedTextMessage?.text) {
                text = msg.message.extendedTextMessage.text;
            } else if (msg.message.imageMessage?.caption) {
                text = msg.message.imageMessage.caption;
            }

            if (!text || !text.trim()) continue;

            console.log(`[MSG RECEIVED] From +${rawPhone} (${senderName}): "${text}"`);

            // Send to Python AI Bot engine
            const reply = await sendToPythonBot('+' + rawPhone, text, senderName);

            if (reply) {
                console.log(`[BOT REPLY] Sending reply to +${rawPhone}...`);
                await sock.sendMessage(jid, { text: reply });
            }
        }
    });
}

startWhatsAppBridge().catch(err => {
    console.error('Fatal bridge error:', err);
    writeStatus({ status: 'ERROR', error: err.message, updatedAt: Date.now() });
});
