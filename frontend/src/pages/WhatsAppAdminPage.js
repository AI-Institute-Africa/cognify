import React, { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { 
  MessageCircle, Wifi, WifiOff, QrCode, Phone, Power, 
  PauseCircle, Users, Send, RefreshCw, Plus, Trash2,
  CheckCircle, AlertCircle, Loader, Bot, BotOff
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export default function WhatsAppAdminPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connectMethod, setConnectMethod] = useState('qr');
  const [phoneInput, setPhoneInput] = useState('+263786434988');
  const [recipients, setRecipients] = useState([]);
  const [messages, setMessages] = useState([]);
  const [newRecipient, setNewRecipient] = useState({ name: '', phone: '', alerts: ['morning', 'evening', 'weekly', 'registration'] });
  const [sendTo, setSendTo] = useState('');
  const [sendMsg, setSendMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [activeTab, setActiveTab] = useState('connection');

  const getHeaders = () => {
    const token = localStorage.getItem('cognify_token') || localStorage.getItem('token') || '';
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    };
  };

  const fetchStatus = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/whatsapp/status`, { headers: getHeaders() });
      if (r.ok) setStatus(await r.json());
    } catch {}
    setLoading(false);
  }, []);

  const fetchRecipients = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/whatsapp/recipients`, { headers: getHeaders() });
      if (r.ok) { const d = await r.json(); setRecipients(d.recipients || []); }
    } catch {}
  }, []);

  const fetchMessages = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/whatsapp/messages`, { headers: getHeaders() });
      if (r.ok) { const d = await r.json(); setMessages(d.messages || []); }
    } catch {}
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchRecipients();
    fetchMessages();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchRecipients, fetchMessages]);

  const handleConnect = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/whatsapp/connect`, {
        method: 'POST', 
        headers: getHeaders(),
        body: JSON.stringify({ method: connectMethod, phone_number: phoneInput })
      });
      if (r.ok) {
        toast.success('Connection initiated');
        setTimeout(fetchStatus, 2000);
      } else {
        toast.error('Failed to initiate connection');
      }
    } catch { 
      toast.error('Connection request failed'); 
    }
    setLoading(false);
  };

  const handleDisconnect = async () => {
    if (!window.confirm('This will log out the WhatsApp session. Continue?')) return;
    try {
      const r = await fetch(`${API}/api/whatsapp/disconnect`, { method: 'POST', headers: getHeaders() });
      if (r.ok) { toast.success('Disconnected'); fetchStatus(); }
    } catch {
      toast.error('Disconnect failed');
    }
  };

  const handleToggleAI = async () => {
    try {
      const r = await fetch(`${API}/api/whatsapp/settings/toggle-ai`, { method: 'POST', headers: getHeaders() });
      if (r.ok) { toast.success('AI status updated'); fetchStatus(); }
    } catch {
      toast.error('Failed to toggle AI');
    }
  };

  const handlePause = async (hours) => {
    try {
      const r = await fetch(`${API}/api/whatsapp/settings/pause`, {
        method: 'POST', headers: getHeaders(), body: JSON.stringify({ hours })
      });
      if (r.ok) toast.success(`AI paused for ${hours}h`);
      fetchStatus();
    } catch {
      toast.error('Failed to pause AI');
    }
  };

  const handleSend = async () => {
    if (!sendTo || !sendMsg) return toast.error('Phone and message required');
    setSending(true);
    try {
      const r = await fetch(`${API}/api/whatsapp/send`, {
        method: 'POST', headers: getHeaders(), body: JSON.stringify({ to: sendTo, message: sendMsg })
      });
      if (r.ok) { 
        toast.success('Message dispatched'); 
        setSendMsg(''); 
        fetchMessages(); 
      } else {
        toast.error('Send failed — make sure WhatsApp is connected');
      }
    } catch {
      toast.error('Error sending message');
    }
    setSending(false);
  };

  const handleAddRecipient = async () => {
    if (!newRecipient.name || !newRecipient.phone) return toast.error('Name and phone required');
    try {
      const r = await fetch(`${API}/api/whatsapp/recipients`, {
        method: 'POST', headers: getHeaders(), body: JSON.stringify(newRecipient)
      });
      if (r.ok) { 
        toast.success('Recipient added'); 
        fetchRecipients(); 
        setNewRecipient({ name: '', phone: '', alerts: ['morning', 'evening', 'weekly', 'registration'] }); 
      }
    } catch {
      toast.error('Failed to add recipient');
    }
  };

  const handleDeleteRecipient = async (phone) => {
    try {
      const r = await fetch(`${API}/api/whatsapp/recipients/${encodeURIComponent(phone)}`, { method: 'DELETE', headers: getHeaders() });
      if (r.ok) { toast.success('Removed recipient'); fetchRecipients(); }
    } catch {
      toast.error('Failed to delete recipient');
    }
  };

  const connectedColor = status?.status === 'connected' ? 'text-green-400' : status?.status === 'qr_ready' ? 'text-yellow-400' : 'text-red-400';
  const StatusIcon = status?.status === 'connected' ? Wifi : WifiOff;
  const ALERT_TYPES = ['morning', 'evening', 'weekly', 'registration', 'corporate'];

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">WhatsApp Control Center</h1>
              <p className="text-sm text-zinc-400">Multi-device Baileys Gateway & AI Inquiry Responder</p>
            </div>
          </div>
          <button onClick={fetchStatus} className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-all">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Status Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-4 flex items-center gap-3">
            <StatusIcon className={`w-6 h-6 ${connectedColor}`} />
            <div>
              <p className="text-xs text-zinc-500">Connection State</p>
              <p className={`font-semibold capitalize ${connectedColor}`}>{status?.status || 'Unknown'}</p>
            </div>
          </div>
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-4 flex items-center gap-3">
            {status?.ai_enabled ? <Bot className="w-6 h-6 text-blue-400" /> : <BotOff className="w-6 h-6 text-zinc-500" />}
            <div>
              <p className="text-xs text-zinc-500">AI Auto-Responder</p>
              <p className={`font-semibold ${status?.ai_enabled ? 'text-blue-400' : 'text-zinc-500'}`}>
                {status?.ai_enabled ? 'Active (EN/SN/ND)' : 'Disabled'}
                {status?.paused_until && new Date() < new Date(status.paused_until) && ' [Paused]'}
              </p>
            </div>
          </div>
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-4 flex items-center gap-3">
            <MessageCircle className="w-6 h-6 text-violet-400" />
            <div>
              <p className="text-xs text-zinc-500">Recent Transcripts</p>
              <p className="font-semibold text-violet-400">{status?.message_count || 0}</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-white/5 pb-2">
          {['connection', 'ai-settings', 'send', 'recipients', 'transcripts'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}>
              {tab === 'ai-settings' ? 'AI Settings' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Connection Tab */}
        {activeTab === 'connection' && (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 space-y-4">
              <h3 className="font-semibold text-white">Pair WhatsApp Device</h3>
              <p className="text-xs text-zinc-400">
                Connect your official institute number or WhatsApp Business phone without per-message Cloud API fees.
              </p>
              <div className="flex gap-2">
                {['qr', 'pairing'].map(m => (
                  <button key={m} onClick={() => setConnectMethod(m)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${connectMethod === m ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'text-zinc-400 hover:bg-white/5'}`}>
                    {m === 'qr' ? <><QrCode className="w-4 h-4 inline mr-1" />Scan QR Code</> : <><Phone className="w-4 h-4 inline mr-1" />Pairing Code</>}
                  </button>
                ))}
              </div>
              {connectMethod === 'pairing' && (
                <input value={phoneInput} onChange={e => setPhoneInput(e.target.value)}
                  placeholder="Enter phone with country code (e.g. 263771234567)"
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-500" />
              )}
              <button onClick={handleConnect} disabled={loading}
                className="w-full py-2.5 rounded-lg bg-green-500 hover:bg-green-400 text-white font-semibold text-sm transition-all flex items-center justify-center gap-2">
                {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Power className="w-4 h-4" />}
                {status?.status === 'connected' ? 'Re-initialize Session' : 'Generate Code / Link'}
              </button>
              {status?.status === 'connected' && (
                <button onClick={handleDisconnect}
                  className="w-full py-2 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 text-sm font-medium transition-all">
                  Logout & Clear Saved Auth
                </button>
              )}
            </div>

            <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 flex flex-col items-center justify-center min-h-[240px]">
              {status?.status === 'qr_ready' && status?.qr ? (
                <>
                  <p className="text-sm text-zinc-400 mb-3">Scan this code using WhatsApp Linked Devices:</p>
                  <img src={status.qr} alt="QR Code" className="w-48 h-48 rounded-lg bg-white p-2" />
                </>
              ) : status?.status === 'qr_ready' && status?.pairing_code ? (
                <>
                  <p className="text-sm text-zinc-400 mb-2">Enter this 8-digit code in WhatsApp → Linked Devices:</p>
                  <div className="text-3xl font-mono font-bold text-green-400 tracking-[0.3em] bg-green-500/10 px-6 py-3 rounded-xl border border-green-500/20">
                    {status.pairing_code}
                  </div>
                </>
              ) : status?.status === 'connected' ? (
                <div className="text-center">
                  <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-2" />
                  <p className="text-green-400 font-semibold text-lg">WhatsApp Connected</p>
                  <p className="text-xs text-zinc-500 mt-1">Multi-device active • AI Responder Online</p>
                </div>
              ) : (
                <div className="text-center text-zinc-500">
                  <WifiOff className="w-10 h-10 mx-auto mb-2 opacity-40" />
                  <p className="text-sm">Device offline. Click "Generate Code / Link" to begin.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI Settings Tab */}
        {activeTab === 'ai-settings' && (
          <div className="space-y-4">
            <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 space-y-4">
              <h3 className="font-semibold text-white">AI Admissions & Inquiry Responder</h3>
              <p className="text-sm text-zinc-400">
                Cognify's WhatsApp AI Agent identifies 7 core inquiry intents and responds natively in 
                <strong className="text-white"> English, Shona, and Ndebele</strong> with human jitter delay (1.5s - 3s).
              </p>
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/5">
                <div>
                  <p className="text-sm font-medium text-white">24/7 Automated Answering</p>
                  <p className="text-xs text-zinc-500">Covers programs, course fees, reference checking, and admissions</p>
                </div>
                <button onClick={handleToggleAI}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${status?.ai_enabled ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-white/5 text-zinc-400 hover:text-white'}`}>
                  {status?.ai_enabled ? 'Enabled ✓' : 'Disabled'}
                </button>
              </div>
              <div>
                <p className="text-sm font-medium text-white mb-2">Emergency Pause AI Auto-Reply</p>
                <div className="flex gap-2">
                  {[1, 4, 24].map(h => (
                    <button key={h} onClick={() => handlePause(h)}
                      className="flex-1 py-2 rounded-lg border border-white/10 text-zinc-400 hover:text-white hover:bg-white/5 text-sm transition-all flex items-center justify-center gap-1">
                      <PauseCircle className="w-4 h-4" />Pause {h}h
                    </button>
                  ))}
                </div>
              </div>
              {status?.paused_until && new Date() < new Date(status.paused_until) && (
                <div className="flex items-center gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                  <AlertCircle className="w-4 h-4 text-yellow-400" />
                  <p className="text-sm text-yellow-300">
                    AI replies paused until {new Date(status.paused_until).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Send Tab */}
        {activeTab === 'send' && (
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 space-y-4">
            <h3 className="font-semibold text-white">Manual Outbound WhatsApp Message</h3>
            <input value={sendTo} onChange={e => setSendTo(e.target.value)}
              placeholder="Destination phone (e.g. 0771234567 or 263771234567)"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-zinc-500" />
            <textarea value={sendMsg} onChange={e => setSendMsg(e.target.value)}
              rows={4} placeholder="Type announcement or message..."
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-zinc-500 resize-none" />
            <button onClick={handleSend} disabled={sending}
              className="w-full py-2.5 rounded-lg bg-green-500 hover:bg-green-400 text-white font-semibold text-sm transition-all flex items-center justify-center gap-2">
              {sending ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Send Outbound Message
            </button>
          </div>
        )}

        {/* Recipients Tab */}
        {activeTab === 'recipients' && (
          <div className="space-y-4">
            <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 space-y-4">
              <h3 className="font-semibold text-white">Add Executive Briefing Recipient</h3>
              <div className="grid md:grid-cols-2 gap-3">
                <input value={newRecipient.name} onChange={e => setNewRecipient(p => ({ ...p, name: e.target.value }))}
                  placeholder="Officer / Executive Name" className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-500" />
                <input value={newRecipient.phone} onChange={e => setNewRecipient(p => ({ ...p, phone: e.target.value }))}
                  placeholder="WhatsApp Number (e.g. 263771234567)" className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-500" />
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-2">Alert Subscriptions:</p>
                <div className="flex flex-wrap gap-2">
                  {ALERT_TYPES.map(a => (
                    <button key={a} onClick={() => setNewRecipient(p => ({
                      ...p, alerts: p.alerts.includes(a) ? p.alerts.filter(x => x !== a) : [...p.alerts, a]
                    }))}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${newRecipient.alerts.includes(a) ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-white/5 text-zinc-500 border border-white/5'}`}>
                      {a}
                    </button>
                  ))}
                </div>
              </div>
              <button onClick={handleAddRecipient}
                className="py-2.5 px-4 rounded-lg bg-green-500 hover:bg-green-400 text-white font-semibold text-sm flex items-center gap-2 transition-all">
                <Plus className="w-4 h-4" />Save Recipient
              </button>
            </div>
            <div className="space-y-2">
              {recipients.map((r, i) => (
                <div key={i} className="flex items-center justify-between bg-[#0d0d0f] border border-white/5 rounded-xl p-4">
                  <div className="flex items-center gap-3">
                    <Users className="w-5 h-5 text-zinc-500" />
                    <div>
                      <p className="text-sm font-medium text-white">{r.name}</p>
                      <p className="text-xs text-zinc-500">{r.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1 flex-wrap">
                      {(r.alerts || []).map(a => (
                        <span key={a} className="px-2 py-0.5 bg-green-500/10 text-green-400 rounded-full text-xs">{a}</span>
                      ))}
                    </div>
                    <button onClick={() => handleDeleteRecipient(r.phone)} className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
              {recipients.length === 0 && (
                <div className="text-center py-8 text-zinc-500 text-sm">No executive alert recipients configured yet.</div>
              )}
            </div>
          </div>
        )}

        {/* Transcripts Tab */}
        {activeTab === 'transcripts' && (
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-white">Live Inbound & Outbound Transcripts</h3>
              <button onClick={fetchMessages} className="text-xs text-zinc-400 hover:text-white flex items-center gap-1">
                <RefreshCw className="w-3 h-3" />Refresh
              </button>
            </div>
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {messages.map((m, i) => (
                <div key={i} className={`p-3 rounded-lg border text-sm ${m.direction === 'inbound' ? 'bg-white/5 border-white/5' : 'bg-green-500/10 border-green-500/20'}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-semibold ${m.direction === 'inbound' ? 'text-zinc-400' : 'text-green-400'}`}>
                      {m.direction === 'inbound' ? 'Inbound from ' + m.from : 'Outbound to ' + m.to}
                    </span>
                    <span className="text-xs text-zinc-500">{new Date(m.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-zinc-200">{m.text}</p>
                </div>
              ))}
              {messages.length === 0 && (
                <div className="text-center py-8 text-zinc-500 text-sm">No messages logged yet.</div>
              )}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
