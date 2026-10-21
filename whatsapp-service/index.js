require('dotenv').config();
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const express = require('express');
const { makeWASocket, useMultiFileAuthState, DisconnectReason, makeCacheableSignalKeyStore, Browsers } = require('@whiskeysockets/baileys');
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
  const lower = text.trim().toLowerCase();
  // Exact or prominent enroll trigger
  if (/^(enroll|enrol|register|join|kunyoresa|bhalisa)\b/i.test(lower) || /\b(enroll|enrol)\b/i.test(lower)) return 'enroll';
  if (/\b(fee|tuition|cost|price|payment|dollar|usd|pay|amount|charge)\b/.test(lower)) return 'pricing';
  if (/\b(course|program|diploma|certificate|module|study|learn)\b/.test(lower)) return 'programs';
  if (/\b(status|reference|application|applied|approved|rejected|pending)\b/.test(lower)) return 'application_status';
  if (/\b(receipt|proof|paid|payment proof|uploaded)\b/.test(lower)) return 'payment_proof';
  if (/\b(help|support|contact|office|call|email|assist)\b/.test(lower)) return 'support';
  if (/\b(hi|hello|hey|good morning|good afternoon|good evening|greetings|sawubona|mhoro)\b/.test(lower)) return 'greeting';
  return 'general';
}

const RESPONSES = {
  en: {
    greeting: `👋 Hello @{USER}! Welcome to *Cognify* — Africa's AI-powered learning platform.\n\nI can help you with:\n📚 *Course & Program info*\n💰 *Fees & Payment*\n📋 *Application status*\n🎓 *Enrollment & Registration*\n\nHow can I assist you today?`,
    enroll: `🎓 *Cognify Instant WhatsApp Enrollment* for @{USER}

🎉 *Your Cognify account has been created directly here on WhatsApp!*

You do not need to fill out a website registration form. Follow these quick steps to access your learning portal:

1️⃣ *Your Login Credentials*:
• Mobile Number: @{USER}
• Verification Code: *Sent below via WhatsApp OTP*

2️⃣ *Direct One-Click Login*:
• Go to: http://localhost:3000/login
• Select *Login with Phone (OTP)*
• Enter your number: @{USER} and your 6-digit WhatsApp OTP.

3️⃣ *Complete Your Profile*:
• Once logged in, go to *Settings / Profile* to choose your learning track, set your career goals, and add your name.

4️⃣ *Start Learning*:
• Access your AI Mentor, interactive quizzes, courses, and certifications immediately!

📌 Check your next incoming WhatsApp message for your secure 6-digit login OTP code.`,
    pricing: `💰 *Cognify Course Fees* for @{USER}\n\n• Individual Courses: from $10/month\n• Professional Certificates: from $25/month\n• Corporate Training Packages: Custom pricing\n• Organization Plans: Contact us for bulk pricing\n\n✅ All plans include AI mentor, quizzes & certificates.\n\nTo enroll, reply with *ENROLL* for instant step-by-step guidance.`,
    programs: `📚 *Cognify Learning Programs* for @{USER}\n\n🎓 *Professional Certificates*\n• AI & Machine Learning\n• Data Science & Analytics\n• Cybersecurity Fundamentals\n• Cloud Computing\n\n💼 *Corporate Training*\n• Custom corporate upskilling\n• Team learning dashboards\n• Progress tracking & reporting\n\n🌍 Available in English, Shona & Ndebele.\n\nReply *ENROLL* to get the registration steps!`,
    application_status: `📋 *Application Status* for @{USER}\n\nTo check your application status, please provide your *reference number* (e.g. CGN-2026-XXXX).\n\nAlternatively, log into your Cognify account at our platform and check your dashboard.`,
    payment_proof: `✅ *Payment Submission* for @{USER}\n\nTo submit your payment proof:\n1. Log into your Cognify account\n2. Go to *Fees & Payments*\n3. Upload your receipt/proof of payment\n\nPayments are verified within 24 hours. For urgent queries, contact our admin office.`,
    support: `📞 *Cognify Support* for @{USER}\n\n🌐 Platform: Visit our website\n📧 Email: support@cognify.com\n⏰ Support hours: Mon–Fri, 8:00–17:00 (Harare)\n\nOur team will respond within 2 business hours.`,
    general: `🤖 Hello @{USER}! Thank you for reaching out to *Cognify*!\n\nI can help with:\n• 📚 Courses & Programs\n• 🎓 Enrollment Steps (Reply *ENROLL*)\n• 💰 Fees & Payments\n• 📋 Application Status\n\nPlease describe what you need or reply with one of the keywords above.`
  },
  sn: {
    greeting: `👋 Mhoro @{USER}! Makadii ku *Cognify* — nzvimbo yekudzidza neAI muAfrica.\n\nNdinogona kukubatsira ne:\n📚 *Zvemakosi*\n💰 *Mubhadharo*\n📋 *Mamiriro ekunyorera*\n\nNdingakubatsirei nhasi?`,
    enroll: `🎓 *Kunyoresa Pakarepo paWhatsApp* emi @{USER}

🎉 *Account yenyu yeCognify yagadzirwa ipapo paWhatsApp!*

Hapana chikonzero chekuvhura fomu pawebhusaiti:

1️⃣ *Zvinhu zvekupinda nazvo*:
• Nhamba: @{USER}
• Code yeOTP: *Yatove kuuya paWhatsApp yako*

2️⃣ *Kupinda muPortal*:
• Endai pa: http://localhost:3000/login
• Sarudzai *Phone (OTP)*
• Isa nhamba @{USER} ne code yawakatumirwa.

3️⃣ *Pedzisa Profile Yako*:
• Kana wangopinda, zadzisa zita rako nezvidzidzo zvaunoda pasi pe *Settings*.

4️⃣ *Tanga Kudzidza*:
• AI Mentor nemakosi ose zvatovhurwa!`,
    pricing: `💰 *Mitengo yeCognify* ye @{USER}\n\n• Makosi: kutanga pa $10/mwedzi\n• Zvitupa: kutanga pa $25/mwedzi\n• Zvemakambani: Mitengo inotauriranwa\n\n✅ Zvese zvine AI mentor nezvitupa zvinotaridza kupasa.\n\nPindura *ENROLL* kuti uwane matanho ekunyoresa.`,
    programs: `📚 *Zvirongwa zvedu zveDzidzo* zve @{USER}\n\n🎓 *Zvitupa Zvepamusoro*\n• AI & Machine Learning\n• Data Science\n• Cybersecurity\n• Cloud Computing\n\n💼 *Dzidziso dzeMakambani*\n• Upskilling yevashandi\n• Team dashboards\n\nPindura *ENROLL* kuti utange.`,
    application_status: `📋 *Kutarisa Application* ya @{USER}\n\nNdokumbira unyore *reference number* yako (semuenzaniso: CGN-2026-XXXX) kana kupinda pane dashboard rako paCognify.`,
    payment_proof: `✅ *Payment Proof* ye @{USER}\n\nIsa umbowo hwekubhadhara pa portal pasi pe *Fees & Payments*. Verification inoitwa mukati memaawa 24.`,
    support: `📞 *Rubatsiro* rwe @{USER}\n\n📧 Email: support@cognify.com\n⏰ Muvhuro-Chishanu 8:00-17:00 Harare time.`,
    general: `🤖 Mazvita nekutaura neCognify @{USER}! Nyorai *ENROLL* kana muchida kunyoresa makosi.`
  },
  nd: {
    greeting: `👋 Sawubona @{USER}! Wamukelekile ku *Cognify* — inkundla yokufunda ye-AI e-Afrika.\n\nNgingakusiza nge:\n📚 *Izifundo nezinhlelo*\n💰 *Izimali zokufunda*\n📋 *Isimo sesicelo*\n\nNgingakusiza ngani namuhla?`,
    enroll: `🎓 *Ukubhalisa Ngokushesha kuWhatsApp* kwakho @{USER}

🎉 *I-akhawunti yakho yeCognify isidaliwe ngqo lapha kuWhatsApp!*

Akudingeki ugcwalise ifomu lewebhusayithi:

1️⃣ *Imininingwane Yakho Yokungena*:
• Inombolo: @{USER}
• Ikhodi ye-OTP: *Ithunyelwe ngqo kuWhatsApp yakho*

2️⃣ *Ukungena ku-Portal*:
• Vakashela: http://localhost:3000/login
• Khetha *Phone (OTP)*
• Faka inombolo @{USER} nekhodi oyitholile.

3️⃣ *Qedela I-Profile Yakho*:
• Uma ungena, yiya ku *Settings* ukuze uqedele igama lakho nezifundo ozithandayo.

4️⃣ *Qala Ukufunda*:
• I-AI Mentor nezifundo kukulindile!`,
    pricing: `💰 *Izindleko zeCognify* zakho @{USER}\n\n• Izifundo: kusukela ku-$10 ngenyanga\n• Izitifiketi: kusukela ku-$25 ngenyanga\n• Amabhizinisi: Amanani akhethekile\n\nPhendula ngokuthi *ENROLL* ukuze uthole izinyathelo zokubhalisa.`,
    programs: `📚 *Izinhlelo zeCognify* zakho @{USER}\n\n🎓 *Izitifiketi Zobuchwepheshe*\n• AI & Machine Learning\n• Data Science\n• Cybersecurity\n• Cloud Computing\n\nPhendula *ENROLL* ukuze uqalise.`,
    application_status: `📋 *Isimo Sesicelo* sakho @{USER}\n\nSicela unikeze *i-reference number* yakho ukuze sihlolisise isimo sesicelo sakho.`,
    payment_proof: `✅ *Ubufakazi Bokukhokha* bakho @{USER}\n\nFaka irisidi lakho ku *Fees & Payments* ku portal. Kuqinisekiswa kungakapheli amahora angama-24.`,
    support: `📞 *Ukusekelwa* kwakho @{USER}\n\n📧 Email: support@cognify.com\n⏰ NgoMvulo-Lwesihlanu 8:00-17:00 Harare time.`,
    general: `🤖 Siyabonga ngokuxhumana neCognify @{USER}! Phendula ngokuthi *ENROLL* ukuze ubhalise ezifundweni.`
  }
};

function generateReply(text, senderJid = '') {
  const settings = loadSettings();
  if (!settings.ai_enabled) return null;
  if (settings.paused_until && new Date() < new Date(settings.paused_until)) return null;
  
  const lang = detectLanguage(text);
  const intent = detectIntent(text);
  const r = RESPONSES[lang] || RESPONSES.en;
  let replyText = r[intent] || r.general;

  // Extract phone number to tag (e.g., 263786434988)
  const userPhone = senderJid ? senderJid.split('@')[0] : '';
  const mentionTag = userPhone ? `@${userPhone}` : 'there';
  replyText = replyText.replace(/@{USER}/g, mentionTag);

  return {
    text: replyText,
    mentions: userPhone ? [senderJid] : []
  };
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
    if (sock) {
      try { sock.end(undefined); } catch {}
      sock = null;
    }

    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    sock = makeWASocket({
      auth: { creds: state.creds, keys: makeCacheableSignalKeyStore(state.keys, logger) },
      printQRInTerminal: false,
      logger,
      browser: Browsers.macOS('Desktop'),
      syncFullHistory: false,
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async ({ connection, lastDisconnect, qr }) => {
      if (qr) {
        connectionState = 'qr_ready';
        qrcode.toDataURL(qr, (err, url) => {
          if (!err) latestQR = url;
        });
        logger.info('QR code ready');

        // If user requested pairing code, request it as soon as the socket is ready for registration
        if (usePairingCode && phoneNumber && !sock.authState.creds.registered && !pairingCode) {
          try {
            const rawNum = phoneNumber.replace(/\D/g, '');
            const code = await sock.requestPairingCode(rawNum);
            pairingCode = code;
            logger.info({ code }, 'Pairing code generated successfully');
          } catch (e) {
            logger.error(e, 'Error generating pairing code');
          }
        }
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
        logger.info({ reason }, 'Connection closed');
        
        if (reason === 401 || reason === DisconnectReason.loggedOut) {
          logger.warn('Auth invalid or logged out, resetting session credentials');
          fs.rmSync(AUTH_DIR, { recursive: true, force: true });
          fs.mkdirSync(AUTH_DIR, { recursive: true });
          return;
        }

        if (reconnectAttempts < MAX_RECONNECT) {
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

        const replyData = generateReply(text, from);
        if (replyData && sock && connectionState === 'connected') {
          try {
            await sock.sendMessage(from, {
              text: replyData.text,
              mentions: replyData.mentions || []
            });
            logMessage('outbound', 'bot', from, replyData.text);

            // If intent is ENROLL, automatically trigger direct account creation & OTP dispatch
            const intent = detectIntent(text);
            if (intent === 'enroll') {
              const cleanPhone = from.replace(/@.*$/, '').replace(/\D/g, '');
              const senderPushName = msg.pushName || null;
              try {
                logger.info({ cleanPhone }, 'Triggering direct WhatsApp account creation and OTP...');
                await axios.post(`${COGNIFY_BACKEND}/api/whatsapp/direct-enroll`, {
                  phone_number: cleanPhone,
                  name: senderPushName
                });
              } catch (apiErr) {
                logger.error(apiErr.response?.data || apiErr.message, 'Failed calling direct-enroll API');
              }
            }
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
