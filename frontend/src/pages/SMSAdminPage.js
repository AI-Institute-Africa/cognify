import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import {
  MessageSquare, Send, Radio, CheckCircle, AlertCircle,
  RefreshCw, Clock, Users, Shield, Loader, FileText, Activity
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export default function SMSAdminPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Single SMS state
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  // Broadcast state
  const [broadcastPhones, setBroadcastPhones] = useState('');
  const [broadcastMessage, setBroadcastMessage] = useState('');
  const [broadcasting, setBroadcasting] = useState(false);

  // Logs & Templates
  const [logs, setLogs] = useState([]);
  const [templates, setTemplates] = useState([]);

  const token = localStorage.getItem('cognify_token') || localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  };

  const fetchStatus = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/sms/status`, { headers });
      if (r.ok) {
        setStatus(await r.json());
      }
    } catch (e) {
      console.error('Failed to fetch SMS status:', e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const fetchLogs = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/sms/logs?limit=50`, { headers });
      if (r.ok) {
        const d = await r.json();
        setLogs(d.logs || []);
      }
    } catch (e) {
      console.error('Failed to fetch SMS logs:', e);
    }
  }, [token]);

  const fetchTemplates = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/sms/templates`, { headers });
      if (r.ok) {
        const d = await r.json();
        setTemplates(d.templates || []);
      }
    } catch (e) {
      console.error('Failed to fetch SMS templates:', e);
    }
  }, [token]);

  useEffect(() => {
    fetchStatus();
    fetchLogs();
    fetchTemplates();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchLogs, fetchTemplates]);

  const handleSendSingle = async (e) => {
    e.preventDefault();
    if (!phone.trim() || !message.trim()) {
      toast.error('Recipient phone and message content are required');
      return;
    }
    setSending(true);
    try {
      const r = await fetch(`${API}/api/sms/send`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ to: phone.trim(), message: message.trim() })
      });
      const data = await r.json();
      if (r.ok) {
        toast.success(data.message || 'SMS sent successfully!');
        setMessage('');
        fetchStatus();
        fetchLogs();
      } else {
        toast.error(data.detail || 'Failed to dispatch SMS');
      }
    } catch (e) {
      toast.error('Network error while dispatching SMS');
    } finally {
      setSending(false);
    }
  };

  const handleBroadcast = async (e) => {
    e.preventDefault();
    const rawPhones = broadcastPhones
      .split(/[\n,;]+/)
      .map(p => p.trim())
      .filter(p => p.length >= 8);

    if (rawPhones.length === 0) {
      toast.error('Please enter at least one valid recipient phone number');
      return;
    }
    if (!broadcastMessage.trim()) {
      toast.error('Broadcast message cannot be empty');
      return;
    }

    setBroadcasting(true);
    try {
      const r = await fetch(`${API}/api/sms/broadcast`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          recipients: rawPhones,
          message: broadcastMessage.trim()
        })
      });
      const data = await r.json();
      if (r.ok) {
        toast.success(`Dispatched ${data.sent} of ${data.total} SMS successfully`);
        setBroadcastMessage('');
        fetchStatus();
        fetchLogs();
      } else {
        toast.error(data.detail || 'Failed to execute broadcast');
      }
    } catch (e) {
      toast.error('Network error dispatching broadcast');
    } finally {
      setBroadcasting(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <Radio className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">SMS Control Engine</h1>
              <p className="text-sm text-zinc-400">
                Manage live SMS gateway, dispatch single & bulk alerts, and audit OTP deliveries
              </p>
            </div>
          </div>
          <button
            onClick={() => { fetchStatus(); fetchLogs(); }}
            className="p-2.5 rounded-xl border border-white/10 text-zinc-400 hover:text-white hover:bg-white/5 transition-all flex items-center gap-2 text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Status Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Gateway Status</p>
              <p className="font-semibold text-green-400 capitalize">
                {status?.status === 'connected' ? 'Connected (SMSPoP)' : 'Unconfigured'}
              </p>
            </div>
          </div>

          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Shield className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Sender ID</p>
              <p className="font-semibold text-white">
                {status?.sender_id || 'SMSPoP'}
              </p>
            </div>
          </div>

          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Activity className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Dispatched (DB)</p>
              <p className="font-semibold text-purple-400">
                {status?.stats?.total_dispatched || 0} Delivered
              </p>
            </div>
          </div>

          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-yellow-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Recent Campaigns</p>
              <p className="font-semibold text-yellow-400">
                {status?.recent_campaigns?.length || 0} Logged
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-white/5 pb-2">
          {[
            { id: 'overview', label: 'Gateway Overview' },
            { id: 'send', label: 'Send SMS' },
            { id: 'broadcast', label: 'Bulk Broadcast' },
            { id: 'logs', label: 'Delivery Logs' },
            { id: 'templates', label: 'Templates' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 space-y-4">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Radio className="w-4 h-4 text-blue-400" />
                Gateway Configuration
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-zinc-500">Active Provider</span>
                  <span className="text-white font-medium">SMSPoP Zimbabwe</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-zinc-500">Base URL</span>
                  <span className="font-mono text-zinc-300 text-xs">{status?.base_url}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-zinc-500">Registered Sender ID</span>
                  <span className="font-mono text-white font-semibold">{status?.sender_id}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/5">
                  <span className="text-zinc-500">API Key</span>
                  <span className="font-mono text-green-400 text-xs">{status?.api_key_masked}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-zinc-500">Default Country Code</span>
                  <span className="text-zinc-300">+263 (Zimbabwe)</span>
                </div>
              </div>

              <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-300">
                💡 All mobile numbers entered in Zimbabwe format (e.g. 078..., 077..., 071...) are automatically converted to standard MSISDN (263...) before dispatch.
              </div>
            </div>

            <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 space-y-4">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-yellow-400" />
                Recent SMSPoP Campaigns
              </h3>
              <div className="space-y-2 max-h-[340px] overflow-y-auto">
                {status?.recent_campaigns && status.recent_campaigns.length > 0 ? (
                  status.recent_campaigns.map((c, i) => (
                    <div key={i} className="p-3 rounded-lg bg-white/3 border border-white/5 text-xs flex justify-between items-center">
                      <div>
                        <p className="font-medium text-white">{c.name || 'Notification'}</p>
                        <p className="text-zinc-500 text-[11px] mt-0.5">
                          ID: {c.id} • Contacts: {c.total_contacts} • Sent: {c.sent}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 font-semibold text-[10px] uppercase">
                          {c.status}
                        </span>
                        <p className="text-zinc-600 text-[10px] mt-1">{c.created_at ? new Date(c.created_at).toLocaleTimeString() : ''}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-zinc-500 text-xs text-center py-6">No recent campaigns retrieved</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: SEND SINGLE SMS */}
        {activeTab === 'send' && (
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 max-w-xl mx-auto space-y-4">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Send className="w-4 h-4 text-green-400" />
              Dispatch Single SMS
            </h3>
            <form onSubmit={handleSendSingle} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Recipient Phone</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="e.g. 0786434988 or +263786434988"
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-medium text-zinc-400">Message Content</label>
                  <span className="text-[11px] text-zinc-500">{message.length}/160 chars ({Math.ceil(message.length / 160) || 1} SMS)</span>
                </div>
                <textarea
                  rows={4}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your SMS message here..."
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={sending}
                className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all flex items-center justify-center gap-2"
              >
                {sending ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Send SMS Now
              </button>
            </form>
          </div>
        )}

        {/* TAB 3: BROADCAST */}
        {activeTab === 'broadcast' && (
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 max-w-2xl mx-auto space-y-4">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" />
              Bulk SMS Broadcast
            </h3>
            <p className="text-xs text-zinc-400">
              Enter multiple phone numbers separated by commas or new lines. Each contact receives the message individually with registered Sender ID.
            </p>

            <form onSubmit={handleBroadcast} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Recipients List</label>
                <textarea
                  rows={4}
                  value={broadcastPhones}
                  onChange={(e) => setBroadcastPhones(e.target.value)}
                  placeholder="0786434988, 0771234567, +263712345678"
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-medium text-zinc-400">Broadcast Message</label>
                  <span className="text-[11px] text-zinc-500">{broadcastMessage.length}/160 chars</span>
                </div>
                <textarea
                  rows={3}
                  value={broadcastMessage}
                  onChange={(e) => setBroadcastMessage(e.target.value)}
                  placeholder="Important notification to all learners..."
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={broadcasting}
                className="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-sm transition-all flex items-center justify-center gap-2"
              >
                {broadcasting ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Dispatch Broadcast
              </button>
            </form>
          </div>
        )}

        {/* TAB 4: DELIVERY LOGS */}
        {activeTab === 'logs' && (
          <div className="bg-[#0d0d0f] border border-white/5 rounded-xl p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                SMS Notification Delivery Logs
              </h3>
              <button
                onClick={fetchLogs}
                className="text-xs text-zinc-400 hover:text-white flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" /> Refresh
              </button>
            </div>

            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {logs.length > 0 ? (
                logs.map((log, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg border bg-white/3 border-white/5 text-sm flex flex-col md:flex-row md:items-center justify-between gap-2"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-white text-xs font-semibold">{log.recipient}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-500/10 text-blue-400">
                          {log.event}
                        </span>
                        {log.provider_reference && (
                          <span className="text-[10px] text-zinc-500 font-mono">
                            Ref: {log.provider_reference}
                          </span>
                        )}
                      </div>
                      <p className="text-zinc-300 text-xs">{log.message}</p>
                    </div>

                    <div className="text-right flex md:flex-col items-center md:items-end justify-between">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                          log.status === 'delivered'
                            ? 'bg-green-500/10 text-green-400'
                            : 'bg-red-500/10 text-red-400'
                        }`}
                      >
                        {log.status}
                      </span>
                      <span className="text-[10px] text-zinc-500 mt-1">
                        {log.sent_at ? new Date(log.sent_at).toLocaleString() : ''}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-10 text-zinc-500 text-sm">
                  No SMS delivery logs recorded yet.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 5: TEMPLATES */}
        {activeTab === 'templates' && (
          <div className="grid md:grid-cols-2 gap-4">
            {templates.map((tpl, i) => (
              <div key={i} className="bg-[#0d0d0f] border border-white/5 rounded-xl p-5 space-y-2">
                <div className="flex justify-between items-center">
                  <h4 className="font-semibold text-white text-sm">{tpl.label}</h4>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-blue-500/10 text-blue-400">
                    {tpl.event}
                  </span>
                </div>
                <div className="p-3 bg-white/3 border border-white/5 rounded-lg text-xs font-mono text-zinc-300">
                  {tpl.template}
                </div>
                <button
                  onClick={() => {
                    setMessage(tpl.template);
                    setActiveTab('send');
                  }}
                  className="text-xs text-blue-400 hover:text-blue-300 pt-1"
                >
                  Use Template in Sender →
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
