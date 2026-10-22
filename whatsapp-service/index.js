require('dotenv').config();
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const express = require('express');
const { makeWASocket, useMultiFileAuthState, DisconnectReason, makeCacheableSignalKeyStore, Browsers, downloadMediaMessage } = require('@whiskeysockets/baileys');
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
const LID_MAP_FILE = path.join(__dirname, 'data', 'lid_mappings.json');

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

// Prevent unexpected process exits on network drop or protocol rejections
process.on('unhandledRejection', (reason) => {
  logger.warn({ reason: String(reason) }, 'Unhandled Promise Rejection caught');
});
process.on('uncaughtException', (err) => {
  logger.error(err, 'Uncaught Exception caught');
});

// ─── Settings & LID helpers ──────────────────────────────────────────────────
function loadSettings() {
  try {
    if (fs.existsSync(SETTINGS_FILE)) return JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
  } catch {}
  return { ai_enabled: true, paused_until: null };
}
function saveSettings(s) {
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(s, null, 2));
}

function loadLidMappings() {
  try {
    if (fs.existsSync(LID_MAP_FILE)) return JSON.parse(fs.readFileSync(LID_MAP_FILE, 'utf8'));
  } catch {}
  return {};
}

function saveLidMapping(lid, phone) {
  try {
    const mappings = loadLidMappings();
    mappings[lid] = phone;
    fs.writeFileSync(LID_MAP_FILE, JSON.stringify(mappings, null, 2));
    logger.info({ lid, phone }, 'Saved LID to phone mapping');
  } catch (e) {
    logger.error(e, 'Failed to save LID mapping');
  }
}

function extractPhoneFromTextOrJid(text, participantJid) {
  const cleanText = (text || '').replace(/[\s\-\(\)]/g, ' ');

  // 1. Check if user typed a local Zimbabwe number (e.g. 0771234567, 078..., 071..., 073...)
  const zwLocalMatch = cleanText.match(/\b(07[1-8]\d{7})\b/);
  if (zwLocalMatch) {
    return '263' + zwLocalMatch[1].slice(1);
  }

  // 2. Check if user typed an international Zimbabwe number (+2637... or 2637...)
  const zwIntlMatch = cleanText.match(/\b(?:\+?263)([1-9]\d{8})\b/);
  if (zwIntlMatch) {
    return '263' + zwIntlMatch[1];
  }

  // 3. Generic international number with + (9 to 13 digits)
  const genericMatch = cleanText.match(/(?:\+)([1-9]\d{8,12})\b/);
  if (genericMatch) {
    return genericMatch[1];
  }

  // 4. Check if participant JID has real phone number (@s.whatsapp.net)
  if (participantJid && participantJid.endsWith('@s.whatsapp.net')) {
    const rawDigits = participantJid.split('@')[0].split(':')[0].replace(/\D/g, '');
    if (rawDigits.length >= 9 && rawDigits.length <= 13) {
      return rawDigits;
    }
  }

  // 5. Check if this participant LID was previously mapped
  const lidKey = participantJid ? participantJid.split('@')[0].split(':')[0] : '';
  if (lidKey) {
    const mappings = loadLidMappings();
    if (mappings[lidKey]) {
      return mappings[lidKey];
    }
  }

  return null;
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
    pricing: `💰 *Cognify Course Fees* for @{USER}\n\n• Individual Courses: from $10/month\n• Professional Certificates: from $25/month\n• Corporate Training Packages: Custom pricing\n• Organization Plans: Contact us for bulk pricing\n\n✅ All plans include AI mentor, quizzes & certificates.\n\n💳 *Pay Instantly via Paynow:*\n👉 https://www.paynow.co.zw/aiia\n_(Supports EcoCash, OneMoney, InnBucks, Visa & Mastercard)_\n\nTo enroll, reply with *ENROLL* for instant step-by-step guidance.`,
    programs: `📚 *Cognify Learning Programs* for @{USER}\n\n🎓 *Professional Certificates*\n• AI & Machine Learning\n• Data Science & Analytics\n• Cybersecurity Fundamentals\n• Cloud Computing\n\n💼 *Corporate Training*\n• Custom corporate upskilling\n• Team learning dashboards\n• Progress tracking & reporting\n\n🌍 Available in English, Shona & Ndebele.\n\nReply *ENROLL* to get the registration steps!`,
    application_status: `📋 *Application Status* for @{USER}\n\nTo check your application status, please provide your *reference number* (e.g. CGN-2026-XXXX).\n\nAlternatively, log into your Cognify account at our platform and check your dashboard.`,
    payment_proof: `✅ *Payment & Billing Portal* for @{USER}\n\n💳 *Pay Directly via Paynow:*\n👉 https://www.paynow.co.zw/aiia\n\nTo submit your payment proof:\n1. Log into your Cognify account\n2. Go to *Fees & Payments*\n3. Upload your receipt/proof of payment\n\nPayments are verified within 24 hours. For urgent queries, contact our admin office.`,
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
    pricing: `💰 *Mitengo yeCognify* ye @{USER}\n\n• Makosi: kutanga pa $10/mwedzi\n• Zvitupa: kutanga pa $25/mwedzi\n• Zvemakambani: Mitengo inotauriranwa\n\n✅ Zvese zvine AI mentor nezvitupa zvinotaridza kupasa.\n\n💳 *Bhadhara paPaynow:*\n👉 https://www.paynow.co.zw/aiia\n\nPindura *ENROLL* kuti uwane matanho ekunyoresa.`,
    programs: `📚 *Zvirongwa zvedu zveDzidzo* zve @{USER}\n\n🎓 *Zvitupa Zvepamusoro*\n• AI & Machine Learning\n• Data Science\n• Cybersecurity\n• Cloud Computing\n\n💼 *Dzidziso dzeMakambani*\n• Upskilling yevashandi\n• Team dashboards\n\nPindura *ENROLL* kuti utange.`,
    application_status: `📋 *Kutarisa Application* ya @{USER}\n\nNdokumbira unyore *reference number* yako (semuenzaniso: CGN-2026-XXXX) kana kupinda pane dashboard rako paCognify.`,
    payment_proof: `✅ *Mubhadharo paPaynow* we @{USER}\n\n💳 *Bhadhara paPaynow:*\n👉 https://www.paynow.co.zw/aiia\n\nIsa umbowo hwekubhadhara pa portal pasi pe *Fees & Payments*. Verification inoitwa mukati memaawa 24.`,
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

        // ── Resolve sender JID ───────────────────────────────────────────────
        // In group chats: remoteJid = group@g.us, participant = sender JID (may be @lid or @s.whatsapp.net)
        // In DMs:         remoteJid = sender JID (@s.whatsapp.net or @lid)
        const isGroup = from.endsWith('@g.us');
        const participantJid = isGroup ? (msg.key.participant || '') : from;
        const replyJid = from;
        const mentionJid = participantJid || replyJid;

        // ── Group message filter: only respond if bot is @tagged ──────────────
        // In DMs (not group) → always respond.
        // In a group → ONLY respond when the bot (@263786434988) is @mentioned.
        if (isGroup) {
          const botPhone = sock.user?.id?.split(':')[0] || '263786434988';
          const mentions =
            msg.message?.extendedTextMessage?.contextInfo?.mentionedJid ||
            msg.message?.audioMessage?.contextInfo?.mentionedJid ||
            [];
          const botTagged = mentions.some(jid =>
            jid.replace(/:\d+@.*$/, '').replace(/@.*$/, '') === botPhone ||
            jid.startsWith(botPhone)
          );
          if (!botTagged) {
            logger.info({ from, text: '(ignored – bot not @tagged)' }, 'Group message ignored');
            continue; // silently skip — do NOT reply
          }
        }

        // Check if message is audio (voice note or audio file)
        const isAudio = Boolean(msg.message?.audioMessage);
        let audioTranscribedText = '';

        if (isAudio) {
          logger.info({ replyJid, participantJid }, 'Received WhatsApp audio message. Transcribing...');
          try {
            const buffer = await downloadMediaMessage(
              msg,
              'buffer',
              {},
              { logger, reuploadRequest: sock.updateMediaMessage }
            );
            if (buffer && buffer.length > 0) {
              const transRes = await axios.post(`${COGNIFY_BACKEND}/api/whatsapp/transcribe-audio`, {
                audio_base64: buffer.toString('base64'),
                lang: 'en'
              });
              if (transRes.data?.ok && transRes.data?.text) {
                audioTranscribedText = transRes.data.text;
                logger.info({ replyJid, audioTranscribedText }, 'Audio successfully transcribed');
              }
            }
          } catch (audioErr) {
            logger.warn({ err: audioErr.message }, 'Failed transcribing incoming audio message');
          }
        }

        // Use transcribed audio text if audio message, otherwise regular text
        const text = audioTranscribedText || msg.message?.conversation || msg.message?.extendedTextMessage?.text || '';
        if (!text) continue;

        // Extract phone number from text, real JID, or LID mappings
        const realPhone = extractPhoneFromTextOrJid(text, mentionJid);

        logMessage('inbound', replyJid, isAudio ? 'user-voice' : 'bot', text);
        logger.info({ replyJid, participantJid, realPhone, isAudio, text }, 'Inbound message');

        // Safe jitter delay between 1.5s - 3s to mimic human response
        const delay = 1500 + Math.random() * 1500;
        await new Promise(r => setTimeout(r, delay));

        // Detect if user wants to enroll (keyword, sending a phone number, or voice note enrollment)
        const intent = detectIntent(text);
        const isStandalonePhone = /^(?:\+?263\s?[1-9]\d{8}|07[1-8]\d{7})$/.test(text.trim().replace(/[\s\-\(\)]/g, ''));
        const isEnrollIntent = intent === 'enroll' || isStandalonePhone || (isAudio && (text.toLowerCase().includes('enroll') || realPhone));

        if (isEnrollIntent && sock && connectionState === 'connected') {
          try {
            await handleEnrollmentFlow(replyJid, mentionJid, realPhone, text, msg.pushName, isAudio);
          } catch (e) {
            logger.error(e, 'Failed handleEnrollmentFlow');
          }
          continue;
        }

        // Regular AI auto-responder
        const replyData = generateReply(text, mentionJid);
        if (replyData && sock && connectionState === 'connected') {
          try {
            await sock.sendMessage(replyJid, {
              text: replyData.text,
              mentions: replyData.mentions || []
            });
            logMessage('outbound', 'bot', replyJid, replyData.text);
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
// Export sock getter for internal helper
function getSock() { return sock; }
function getConnectionState() { return connectionState; }

// Full enrollment handler with real phone resolution & OTP delivery
async function handleEnrollmentFlow(replyJid, mentionJid, realPhone, text, pushName, isAudio = false) {
  if (!sock || connectionState !== 'connected') return;
  const lang = detectLanguage(text);
  const userTag = mentionJid ? mentionJid.split('@')[0] : 'there';
  const mentionTag = `@${userTag}`;
  const lidKey = mentionJid ? mentionJid.split('@')[0].split(':')[0] : '';

  // 1. If we don't have a verified real phone number yet, ask the user for it
  if (!realPhone) {
    logger.info({ mentionJid, isAudio }, 'Real phone not resolved yet — prompting user for mobile number');
    let promptMsg = '';
    let promptVoiceText = '';

    if (lang === 'sn') {
      promptMsg = `🎓 *Kunyoresa Pakarepo paCognify* emi ${mentionTag}\n\n` +
        `Kuti tigadzire account yenyu yeCognify nekukutumirai OTP ye login, ndapota pindurai nenhamba yenyu ye mobile (ne audio kana kunyora):\n\n` +
        `👉 *ENROLL <nhamba-yefoni>*\n` +
        `_Semuenzaniso: *ENROLL 0771234567* kana *ENROLL +263771234567*_\n\n` +
        `Account yenyu inobva yagadzirwa ipapo nenhamba yenyu chaiyo!`;
      promptVoiceText = `Mhoro! Makadii ku Cognify. Kuti tigadzire account yenyu ye Cognify nekukutumirai code ye login, ndapota pindurai nenhamba yenyu ye foni kana kutaura audio message nenhamba yenyu.`;
    } else if (lang === 'nd') {
      promptMsg = `🎓 *Ukubhalisa Ngokushesha kuCognify* kwakho ${mentionTag}\n\n` +
        `Ukuze sakhe i-akhawunti yakho ye-Cognify futhi sikuthumelele i-OTP yokungena, sicela uphendule ngenombolo yakho yocingo:\n\n` +
        `👉 *ENROLL <inombolo-yocingo>*\n` +
        `_Isibonelo: *ENROLL 0771234567* noma *ENROLL +263771234567*_\n\n` +
        `I-akhawunti yakho izokwenziwa ngokushesha ngenombolo yakho yangempela!`;
      promptVoiceText = `Sawubona! Wamukelekile ku Cognify. Ukuze sakhe i-akhawunti yakho, sicela uphendule ngenombolo yakho yocingo nge-voice note noma ngombhalo.`;
    } else {
      promptMsg = `🎓 *Cognify Instant WhatsApp Enrollment* for ${mentionTag}\n\n` +
        `To create your Cognify account and send your secure 6-digit login OTP, please reply with your mobile phone number (by voice note or text):\n\n` +
        `👉 *ENROLL <your-phone-number>*\n` +
        `_Example: *ENROLL 0771234567* or *ENROLL +263771234567*_\n\n` +
        `Your account will be created immediately with your real mobile number, and your login code will appear right here!`;
      promptVoiceText = `Hello! Welcome to Cognify Africa. To create your learning account and receive your six digit login code, please reply with your mobile phone number by sending a voice note or typing your number.`;
    }

    await sock.sendMessage(replyJid, {
      text: promptMsg,
      mentions: [mentionJid]
    });
    logMessage('outbound', 'bot', replyJid, promptMsg);

    // If incoming message was voice or requested, also send spoken voice prompt
    try {
      const vPromptRes = await axios.post(`${COGNIFY_BACKEND}/api/whatsapp/generate-voice`, {
        text: promptVoiceText,
        lang: lang === 'sn' ? 'sn' : 'en'
      });
      if (vPromptRes.data?.ok && vPromptRes.data?.audio_base64) {
        const audioBuffer = Buffer.from(vPromptRes.data.audio_base64, 'base64');
        await sock.sendMessage(replyJid, {
          audio: audioBuffer,
          mimetype: 'audio/ogg; codecs=opus',
          ptt: true
        });
        logger.info({ replyJid }, 'Sent audio voice note prompt for mobile number');
      }
    } catch (e) {
      logger.warn({ err: e.message }, 'Could not send audio prompt');
    }
    return;
  }

  // 2. If sender had an LID, persist mapping so future messages auto-recognize them
  if (mentionJid.includes('@lid') && lidKey) {
    saveLidMapping(lidKey, realPhone);
  }

  // 3. Call backend /api/whatsapp/direct-enroll with the real phone number
  try {
    const res = await axios.post(`${COGNIFY_BACKEND}/api/whatsapp/direct-enroll`, {
      phone_number: realPhone,
      name: pushName || null
    });

    const { code, is_new_user, phone } = res.data;
    const displayPhone = phone || `+${realPhone}`;

    // 4. Build bundled text response with real phone number + OTP
    let finalMessage = '';
    if (lang === 'sn') {
      finalMessage = `🎓 *Kunyoresa Pakarepo paCognify* emi ${mentionTag}\n\n` +
        `🎉 *Account yenyu yagadzirwa ipapo!*\n\n` +
        `🔐 *Code Yenyu yeOTP*: *${code}*\n\n` +
        `1️⃣ *Zvinhu zvekupinda nazvo*:\n` +
        `• Nhamba yeFoni: *${displayPhone}*\n` +
        `• Code yeOTP: *${code}*\n\n` +
        `2️⃣ *Kupinda muPortal*:\n` +
        `• Vhura: http://localhost:3000/login\n` +
        `• Sarudza *Phone (OTP)*\n` +
        `• Isa nhamba: *${displayPhone}* ne code: *${code}*\n\n` +
        `3️⃣ *Profile Yako*:\n` +
        `• Kana wangopinda, zadzisa zita nezvidzidzo pasi pe *Settings*!\n\n` +
        `🎙️ _Teererai voice note riri pazasi kuitira mirairo yekupinda!_\n` +
        `🚀 _Tanga kudzidza ne AI Mentor pakarepo!_`;
    } else if (lang === 'nd') {
      finalMessage = `🎓 *Ukubhalisa Ngokushesha kuCognify* kwakho ${mentionTag}\n\n` +
        `🎉 *I-akhawunti yakho isidaliwe ngqo!*\n\n` +
        `🔐 *Ikhodi Yakho ye-OTP*: *${code}*\n\n` +
        `1️⃣ *Imininingwane Yokungena*:\n` +
        `• Inombolo Yocingo: *${displayPhone}*\n` +
        `• Ikhodi ye-OTP: *${code}*\n\n` +
        `2️⃣ *Ukungena ku-Portal*:\n` +
        `• Vakashela: http://localhost:3000/login\n` +
        `• Khetha *Phone (OTP)*\n` +
        `• Faka inombolo: *${displayPhone}* nekhodi: *${code}*\n\n` +
        `3️⃣ *Qedela I-Profile*:\n` +
        `• Uma ungena, qedela igama nezifundo ku *Settings*!\n\n` +
        `🎙️ _Lalela i-voice note ngezansi ukuze uthole imiyalelo yokungena!_\n` +
        `🚀 _Qala ukufunda ne-AI Mentor ngokushesha!_`;
    } else {
      finalMessage = `🎓 *Cognify Instant WhatsApp Enrollment* for ${mentionTag}\n\n` +
        `🎉 *Your Cognify account has been created!*\n\n` +
        `🔐 *Your Secure Login OTP*: *${code}*\n\n` +
        `1️⃣ *Your Login Credentials*:\n` +
        `• Mobile Number: *${displayPhone}*\n` +
        `• 6-Digit OTP Code: *${code}*\n\n` +
        `2️⃣ *One-Click Direct Login*:\n` +
        `• Go to: http://localhost:3000/login\n` +
        `• Select *Login with Phone (OTP)*\n` +
        `• Enter your number: *${displayPhone}* and Code: *${code}*\n\n` +
        `3️⃣ *Complete Your Profile*:\n` +
        `• Head to *Settings / Profile* after login to customize your tracks & goals.\n\n` +
        `🎙️ _Listen to the voice note audio below for spoken instructions!_\n` +
        `🚀 _Your courses and AI Mentor are waiting for you!_`;
    }

    await sock.sendMessage(replyJid, {
      text: finalMessage,
      mentions: [mentionJid]
    });
    logMessage('outbound', 'bot', replyJid, finalMessage);
    logger.info({ replyJid, mentionJid, displayPhone, code }, 'Bundled enrollment text message sent successfully');

    // 5. Send Audio Voice Note with spoken enrollment instructions and OTP code
    try {
      const cleanDigits = code.split('').join(' ');
      const phoneDigits = displayPhone.replace(/\+/g, 'plus ').split('').join(' ');

      let voiceScript = '';
      if (lang === 'sn') {
        voiceScript = `Mhoro! Makadii ku Cognify Africa. Account yenyu yagadzirwa zvakanaka. Nhamba yenyu ye foni ndeinoti ${phoneDigits}. Code yenyu ye OTP yekupinda nayo inoti: ${cleanDigits}. Ndapota endai pa webhusaiti yedu pa localhost 3000 slash login, musarudze phone OTP, moisa nhamba yenyu pamwe chete ne code iyi kuti mutange kudzidza.`;
      } else if (lang === 'nd') {
        voiceScript = `Sawubona! Wamukelekile ku Cognify Africa. I-akhawunti yakho isidaliwe. Inombolo yakho yocingo ithi ${phoneDigits}. Ikhodi yakho ye OTP ithi: ${cleanDigits}. Sicela uvakashele i-website yethu ku localhost 3000 slash login, ukhethe i-phone OTP, bese ufaka inombolo yakho nekhodi ukuze uqalise ukufunda.`;
      } else {
        voiceScript = `Hello! Welcome to Cognify Africa. Your learning account has been created successfully. Your mobile number is ${phoneDigits}, and your secure 6-digit login verification code is ${cleanDigits}. Please open your browser, visit http://localhost:3000/login, choose Login with Phone, and enter your number and code to access your courses and AI mentor right away!`;
      }

      const voiceRes = await axios.post(`${COGNIFY_BACKEND}/api/whatsapp/generate-voice`, {
        text: voiceScript,
        lang: lang === 'sn' ? 'sn' : 'en'
      });

      if (voiceRes.data?.ok && voiceRes.data?.audio_base64) {
        const audioBuffer = Buffer.from(voiceRes.data.audio_base64, 'base64');
        await sock.sendMessage(replyJid, {
          audio: audioBuffer,
          mimetype: 'audio/ogg; codecs=opus',
          ptt: true
        });
        logger.info({ replyJid, displayPhone }, 'Sent audio voice note instructions');
      }
    } catch (voiceErr) {
      logger.warn({ err: voiceErr.message }, 'Could not send audio voice note');
    }
  } catch (err) {
    logger.error(err, 'Failed in handleEnrollmentFlow');
    const errMsg = `⚠️ Unable to complete enrollment: ${err?.response?.data?.detail || err.message}. Please reply with *ENROLL <your-phone-number>*.`;
    await sock.sendMessage(replyJid, { text: errMsg, mentions: [mentionJid] });
  }
}
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
  const { to, message, tag_all, mentions } = req.body;
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'WhatsApp not connected' });
  }
  try {
    let jid = to.trim();
    if (jid.endsWith('@lid') || jid.endsWith('@g.us')) {
      // Keep exact LID or group JID
    } else {
      let cleanDigits = jid.replace(/\D/g, '');
      if (cleanDigits.startsWith('0') && cleanDigits.length === 10) cleanDigits = '263' + cleanDigits.slice(1);
      jid = cleanDigits + '@s.whatsapp.net';
    }

    let mentionJids = [];
    if (jid.endsWith('@g.us') && tag_all) {
      try {
        const metadata = await sock.groupMetadata(jid);
        mentionJids = (metadata.participants || []).map(p => p.id);
        logger.info({ jid, count: mentionJids.length }, 'Fetched group participants for tag_all');
      } catch (metaErr) {
        logger.warn({ err: metaErr.message }, 'Failed to fetch group participants for tag_all');
      }
    } else if (Array.isArray(mentions)) {
      mentionJids = mentions;
    }

    const delay = 1500 + Math.random() * 1500;
    await new Promise(r => setTimeout(r, delay));

    const sendPayload = { text: message };
    if (mentionJids.length > 0) {
      sendPayload.mentions = mentionJids;
    }

    await sock.sendMessage(jid, sendPayload);
    logMessage('outbound', 'server', jid, message);
    res.json({ ok: true, to: jid, mentioned_count: mentionJids.length });
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
