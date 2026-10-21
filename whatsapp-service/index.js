require('dotenv').config();
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const express = require('express');
const { makeWASocket, useMultiFileAuthState, DisconnectReason, makeCacheableSignalKeyStore } = require('@whiskeysockets/baileys');
const pino = require('pino');
const qrcode = require('qrcode');
const cron = require('node-cron');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3001;
const COGNIFY_BACKEND = process.env.COGNIFY_BACKEND_URL || 'http://localhost:8000';
const AUTH_DIR = path.join(__dirname, 'data', 'baileys_auth');
const SETTINGS_FILE = path.join(__dirname, 'data', 'whatsapp_ai_settings.json');

// Ensure data directory exists
if (!fs.existsSync(path.join(__dirname, 'data'))) fs.mkdirSync(path.join(__dirname, 'data'), { recursive: true });
if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true });

// ─── State ──────────────────────────────────────────────────────────────────
let sock = null;
let connectionState = 'disconnected'; // disconnected | connecting | qr_ready | connected
let latestQR = null;
let pairingCode = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 10;
const messageLog = []; // in-memory last 100 messages

const logger = pino({ level: 'info' }, pino.destination('./data/whatsapp.log'));

// ─── Settings helpers ────────────────────────────────────────────────────────
function loadSettings() {
  try {
    if (fs.existsSync(SETTINGS_FILE)) return JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
  } catch {}
  return { ai_enabled: true, paused_until: null };
}
function saveSettings(s) {
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(s, null, 2));
}

// ─── AI Intent & Language Detection ──────────────────────────────────────────
function detectLanguage(text) {
  const sn = ['mhoro', 'ndinoda', 'zvino', 'sei', 'kufunda', 'mari', 'tinotenda', 'makadii', 'zvakanaka'];
  const nd = ['sawubona', 'ngifuna', 'imali', 'ukufunda', 'sikhona', 'ngiyabonga', 'yebo', 'unjani'];
  const lower = text.toLowerCase();
  if (sn.some(w => lower.includes(w))) return 'sn';
  if (nd.some(w => lower.includes(w))) return 'nd';
  return 'en';
}

function detectIntent(text) {
  const lower = text.toLowerCase();
  if (/\b(fee|tuition|cost|price|payment|dollar|usd|pay|amount|charge)\b/.test(lower)) return 'pricing';
  if (/\b(course|program|diploma|certificate|module|study|learn|enroll|register)\b/.test(lower)) return 'programs';
  if (/\b(status|reference|application|applied|approved|rejected|pending)\b/.test(lower)) return 'application_status';
  if (/\b(receipt|proof|paid|payment proof|uploaded)\b/.test(lower)) return 'payment_proof';
  if (/\b(help|support|contact|office|call|email|assist)\b/.test(lower)) return 'support';
  if (/\b(hi|hello|hey|good morning|good afternoon|good evening|greetings|sawubona|mhoro)\b/.test(lower)) return 'greeting';
  return 'general';
}

const RESPONSES = {
  en: {
    greeting: `👋 Hello! Welcome to *Cognify* — Africa's AI-powered learning platform.\n\nI can help you with:\n📚 *Course & Program info*\n💰 *Fees & Payment*\n📋 *Application status*\n🎓 *Enrollment & Registration*\n\nHow can I assist you today?`,
    pricing: `💰 *Cognify Course Fees*\n\n• Individual Courses: from $10/month\n• Professional Certificates: from $25/month\n• Corporate Training Packages: Custom pricing\n• Organization Plans: Contact us for bulk pricing\n\n✅ All plans include AI mentor, quizzes & certificates.\n\nTo enroll, visit our platform or reply with *ENROLL* for next steps.`,
    programs: `📚 *Cognify Learning Programs*\n\n🎓 *Professional Certificates*\n• AI & Machine Learning\n• Data Science & Analytics\n• Cybersecurity Fundamentals\n• Cloud Computing\n\n💼 *Corporate Training*\n• Custom corporate upskilling\n• Team learning dashboards\n• Progress tracking & reporting\n\n🌍 Available in English, Shona & Ndebele.\n\nReply *ENROLL* to get started or visit our platform.`,
    application_status: `📋 *Application Status*\n\nTo check your application status, please provide your *reference number* (e.g. CGN-2026-XXXX).\n\nAlternatively, log into your Cognify account at our platform and check your dashboard.`,
    payment_proof: `✅ *Payment Submission*\n\nTo submit your payment proof:\n1. Log into your Cognify account\n2. Go to *Fees & Payments*\n3. Upload your receipt/proof of payment\n\nPayments are verified within 24 hours. For urgent queries, contact our admin office.`,
    support: `📞 *Cognify Support*\n\n🌐 Platform: Visit our website\n📧 Email: support@cognify.com\n⏰ Support hours: Mon–Fri, 8:00–17:00 (Harare)\n\nOur team will respond within 2 business hours.`,
    general: `🤖 Thank you for reaching out to *Cognify*!\n\nI can help with:\n• 📚 Courses & Programs\n• 💰 Fees & Payments\n• 📋 Application Status\n• 🎓 Enrollment\n\nPlease describe what you need or type one of the keywords above.`
  },
  sn: {
    greeting: `👋 Mhoro! Makadii ku *Cognify* — nzvimbo yekudzidza neAI muAfrica.\n\nNdinogona kukubatsira ne:\n📚 *Zvemakosi*\n💰 *Mubhadharo*\n📋 *Mamiriro ekunyorera*\n\nNdingakubatsirei nhasi?`,
    pricing: `💰 *Mitengo yeCognify*\n\n• Makosi: kutanga pa $10/mwedzi\n• Zvitupa: kutanga pa $25/mwedzi\n• Zvemakambani: Mitengo inotauriranwa\n\n✅ Zvese zvine AI mentor nezvitupa zvinotaridza kupasa.\n\nPindura *ENROLL* kana shanyira nzvimbo yedu.`,
    programs: `📚 *Zvirongwa zvedu zveDzidzo*\n\n🎓 *Zvitupa Zvepamusoro*\n• AI & Machine Learning\n• Data Science\n• Cybersecurity\n• Cloud Computing\n\n💼 *Dzidziso dzeMakambani*\n• Upskilling yevashandi\n• Team dashboards\n\nPindura *ENROLL* kuti utange.`,
    application_status: `📋 *Kutarisa Application*\n\nNdokumbira unyore *reference number* yako (semuenzaniso: CGN-2026-XXXX) kana kupinda pane dashboard rako paCognify.`,
    payment_proof: `✅ *Payment Proof*\n\nIsa umbowo hwekubhadhara pa portal pasi pe *Fees & Payments*. Verification inoitwa mukati memaawa 24.`,
    support: `📞 *Rubatsiro*\n\n📧 Email: support@cognify.com\n⏰ Muvhuro-Chishanu 8:00-17:00 Harare time.`,
    general: `🤖 Mazvita nekutaura neCognify! Nyorai muchidimbu zvamunoda kubatsirwa nazvo.`
  },
  nd: {
    greeting: `👋 Sawubona! Wamukelekile ku *Cognify* — inkundla yokufunda ye-AI e-Afrika.\n\nNgingakusiza nge:\n📚 *Izifundo nezinhlelo*\n💰 *Izimali zokufunda*\n📋 *Isimo sesicelo*\n\nNgingakusiza ngani namuhla?`,
    pricing: `💰 *Izindleko zeCognify*\n\n• Izifundo: kusukela ku-$10 ngenyanga\n• Izitifiketi: kusukela ku-$25 ngenyanga\n• Amabhizinisi: Amanani akhethekile\n\nPhendula ngokuthi *ENROLL* ukuze uqale.`,
    programs: `📚 *Izinhlelo zeCognify*\n\n🎓 *Izitifiketi Zobuchwepheshe*\n• AI & Machine Learning\n• Data Science\n• Cybersecurity\n• Cloud Computing\n\nPhendula *ENROLL* ukuze uqalise.`,
    application_status: `📋 *Isimo Sesicelo*\n\nSicela unikeze *i-reference number* yakho ukuze sihlolisise isimo sesicelo sakho.`,
    payment_proof: `✅ *Ubufakazi Bokukhokha*\n\nFaka irisidi lakho ku *Fees & Payments* ku portal. Kuqinisekiswa kungakapheli amahora angama-24.`,
    support: `📞 *Ukusekelwa*\n\n📧 Email: support@cognify.com\n⏰ NgoMvulo-Lwesihlanu 8:00-17:00 Harare time.`,
    general: `🤖 Siyabonga ngokuxhumana neCognify! Bhala ngokugcwele ukuthi ungathanda ukusizwa ngani.`
  }
};

function generateReply(text) {
  const settings = loadSettings();
  if (!settings.ai_enabled) return null;
  if (settings.paused_until && new Date() < new Date(settings.paused_until)) return null;
  
  const lang = detectLanguage(text);
  const intent = detectIntent(text);
  const r = RESPONSES[lang] || RESPONSES.en;
  return r[intent] || r.general;
}

// ─── Message logging ─────────────────────────────────────────────────────────
function logMessage(direction, from, to, text) {
  const entry = { direction, from, to, text, timestamp: new Date().toISOString() };
  messageLog.unshift(entry);
  if (messageLog.length > 100) messageLog.pop();
}

// ─── Baileys connection ──────────────────────────────────────────────────────
async function connectWhatsApp(usePairingCode = false, phoneNumber = null) {
  connectionState = 'connecting';
  latestQR = null;
  pairingCode = null;

  try {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    sock = makeWASocket({
      auth: { creds: state.creds, keys: makeCacheableSignalKeyStore(state.keys, logger) },
      printQRInTerminal: false,
      logger,
      browser: ['Cognify', 'Chrome', '1.0.0'],
      syncFullHistory: false,
    });

    if (usePairingCode && phoneNumber && !sock.authState.creds.registered) {
      setTimeout(async () => {
        try {
          const code = await sock.requestPairingCode(phoneNumber.replace(/\D/g, ''));
          pairingCode = code;
          connectionState = 'qr_ready';
          logger.info({ code }, 'Pairing code generated');
        } catch (e) {
          logger.error(e, 'Failed to get pairing code');
        }
      }, 3000);
    }

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
      if (qr) {
        connectionState = 'qr_ready';
        qrcode.toDataURL(qr, (err, url) => {
          if (!err) latestQR = url;
        });
        logger.info('QR code ready');
      }
      if (connection === 'open') {
        connectionState = 'connected';
        reconnectAttempts = 0;
        latestQR = null;
        pairingCode = null;
        logger.info('WhatsApp connected successfully');
      }
      if (connection === 'close') {
        connectionState = 'disconnected';
        const reason = lastDisconnect?.error?.output?.statusCode;
        const shouldReconnect = reason !== DisconnectReason.loggedOut;
        logger.info({ reason }, 'Connection closed');
        if (shouldReconnect && reconnectAttempts < MAX_RECONNECT) {
          reconnectAttempts++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
          logger.info({ delay, reconnectAttempts }, 'Reconnecting...');
          setTimeout(() => connectWhatsApp(false, null), delay);
        }
      }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
      if (type !== 'notify') return;
      for (const msg of messages) {
        if (msg.key.fromMe || !msg.message) continue;
        const from = msg.key.remoteJid;
        const text = msg.message?.conversation || msg.message?.extendedTextMessage?.text || '';
        if (!text) continue;

        logMessage('inbound', from, 'bot', text);
        logger.info({ from, text }, 'Inbound message');

        // Safe jitter delay between 1.5s - 3s to mimic human response
        const delay = 1500 + Math.random() * 1500;
        await new Promise(r => setTimeout(r, delay));

        const reply = generateReply(text);
        if (reply && sock && connectionState === 'connected') {
          try {
            await sock.sendMessage(from, { text: reply });
            logMessage('outbound', 'bot', from, reply);
          } catch (e) {
            logger.error(e, 'Failed to send reply');
          }
        }
      }
    });
  } catch (err) {
    connectionState = 'disconnected';
    logger.error(err, 'Error initializing WhatsApp socket');
  }
}

// ─── REST API ────────────────────────────────────────────────────────────────
app.get('/status', (req, res) => {
  res.json({
    status: connectionState,
    qr: latestQR,
    pairing_code: pairingCode,
    ai_enabled: loadSettings().ai_enabled,
    paused_until: loadSettings().paused_until,
    message_count: messageLog.length
  });
});

app.post('/connect', async (req, res) => {
  const { method, phone_number } = req.body;
  try {
    await connectWhatsApp(method === 'pairing', phone_number);
    res.json({ ok: true, method });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/disconnect', async (req, res) => {
  try {
    if (sock) {
      await sock.logout().catch(() => {});
      sock = null;
    }
    connectionState = 'disconnected';
    fs.rmSync(AUTH_DIR, { recursive: true, force: true });
    fs.mkdirSync(AUTH_DIR, { recursive: true });
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/send', async (req, res) => {
  const { to, message } = req.body;
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'WhatsApp not connected' });
  }
  try {
    let jid = to.replace(/\D/g, '');
    if (jid.startsWith('0') && jid.length === 10) jid = '263' + jid.slice(1);
    if (!jid.includes('@')) jid = jid + '@s.whatsapp.net';

    const delay = 1500 + Math.random() * 1500;
    await new Promise(r => setTimeout(r, delay));
    await sock.sendMessage(jid, { text: message });
    logMessage('outbound', 'server', jid, message);
    res.json({ ok: true, to: jid });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/messages', (req, res) => {
  res.json({ messages: messageLog.slice(0, 50) });
});

app.get('/settings', (req, res) => res.json(loadSettings()));
app.post('/settings', (req, res) => {
  const s = { ...loadSettings(), ...req.body };
  saveSettings(s);
  res.json(s);
});

app.post('/settings/toggle-ai', (req, res) => {
  const s = loadSettings();
  s.ai_enabled = !s.ai_enabled;
  saveSettings(s);
  res.json(s);
});

app.post('/settings/pause', (req, res) => {
  const { hours } = req.body;
  const s = loadSettings();
  s.paused_until = new Date(Date.now() + (hours || 1) * 3600 * 1000).toISOString();
  saveSettings(s);
  res.json(s);
});

app.get('/community-url', (req, res) => {
  res.json({ url: process.env.WHATSAPP_COMMUNITY_URL || '' });
});

// ─── Scheduled Executive Reports ─────────────────────────────────────────────
async function fetchAndSendReport(type) {
  if (connectionState !== 'connected' || !sock) return;
  try {
    const r = await axios.get(`${COGNIFY_BACKEND}/api/whatsapp/report/${type}`);
    const { message, recipients } = r.data;
    if (!message || !recipients?.length) return;
    for (const phone of recipients) {
      let jid = phone.replace(/\D/g, '');
      if (jid.startsWith('0') && jid.length === 10) jid = '263' + jid.slice(1);
      if (!jid.includes('@')) jid = jid + '@s.whatsapp.net';
      const delay = 1500 + Math.random() * 1500;
      await new Promise(r2 => setTimeout(r2, delay));
      await sock.sendMessage(jid, { text: message });
      logger.info({ type, jid }, 'Report sent');
    }
  } catch (e) {
    logger.error(e, `Failed to send ${type} report`);
  }
}

if (process.env.REPORT_ENABLED === 'true') {
  // Morning briefing: 08:00 Harare (UTC+2 = 06:00 UTC)
  cron.schedule('0 6 * * *', () => fetchAndSendReport('morning'), { timezone: 'UTC' });
  // Evening reconciliation: 18:00 Harare (UTC+2 = 16:00 UTC)
  cron.schedule('0 16 * * *', () => fetchAndSendReport('evening'), { timezone: 'UTC' });
  // Weekly report: Monday 08:30 Harare (UTC+2 = 06:30 UTC)
  cron.schedule('30 6 * * 1', () => fetchAndSendReport('weekly'), { timezone: 'UTC' });
}

// ─── Start ───────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[Cognify WhatsApp Service] Running on port ${PORT}`);
  connectWhatsApp().catch(e => console.error('Initial connect failed:', e));
});
