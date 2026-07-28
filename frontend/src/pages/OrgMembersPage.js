/* Org Admin → Members Management
   Left tabs: Pending · Members · Join Link Settings */
import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Loader2, Users, UserCheck, UserX, Copy, Check, Link2,
  Settings as SettingsIcon, RefreshCw, ShieldCheck, ShieldOff, QrCode
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';

const API = process.env.REACT_APP_BACKEND_URL;
const TOK = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

const TABS = [
  { key: 'pending',  label: 'Pending Members', icon: Users },
  { key: 'members',  label: 'All Members',      icon: UserCheck },
  { key: 'settings', label: 'Join Link Settings', icon: SettingsIcon },
];

export default function OrgMembersPage() {
  const [tab, setTab] = useState('pending');
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-6xl mx-auto p-6">
        <h1 className="text-3xl font-semibold mb-1">Organization Members</h1>
        <p className="text-sm text-zinc-400 mb-6">Review new signups, manage members, and configure your public join link.</p>
        <div className="flex gap-2 mb-6 border-b border-white/5">
          {TABS.map((t) => (
            <button key={t.key}
                    data-testid={`org-mem-tab-${t.key}`}
                    onClick={() => setTab(t.key)}
                    className={`px-4 py-2 text-sm flex items-center gap-2 border-b-2 -mb-px transition ${
                      tab === t.key
                        ? 'border-violet-500 text-white'
                        : 'border-transparent text-zinc-400 hover:text-zinc-200'
                    }`}>
              <t.icon className="w-4 h-4" /> {t.label}
            </button>
          ))}
        </div>
        {tab === 'pending' && <PendingPanel />}
        {tab === 'members' && <MembersPanel />}
        {tab === 'settings' && <SettingsPanel />}
      </div>
    </div>
  );
}

function PendingPanel() {
  const [items, setItems] = useState(null);
  const [busy, setBusy] = useState(null);

  const load = () => {
    axios.get(`${API}/api/org-admin/pending-members`, { headers: TOK() })
      .then(({ data }) => setItems(data.pending || []))
      .catch(() => toast.error('Failed to load pending members'));
  };
  useEffect(load, []);

  const act = async (id, action, reason) => {
    setBusy(`${id}:${action}`);
    try {
      const url = `${API}/api/org-admin/pending-members/${id}/${action}`;
      await axios.post(url, action === 'reject' ? { reason: reason || '' } : {}, { headers: TOK() });
      toast.success(action === 'approve' ? 'Member approved' : 'Application rejected');
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Action failed');
    } finally {
      setBusy(null);
    }
  };

  if (items === null) return <div className="py-10 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-violet-400" /></div>;
  if (!items.length) {
    return <div className="glass-card p-10 text-center text-zinc-400" data-testid="pending-empty">
      <Users className="w-10 h-10 mx-auto mb-3 opacity-50" />
      <p>No pending applications right now.</p>
    </div>;
  }
  return (
    <div className="space-y-3">
      {items.map((p) => (
        <Card key={p.id} className="bg-zinc-900/60 border-white/10" data-testid={`pending-row-${p.id}`}>
          <CardContent className="p-4 flex items-center justify-between gap-4 flex-wrap">
            <div className="flex-1 min-w-[240px]">
              <div className="font-medium text-white">{p.full_name}</div>
              <div className="text-sm text-zinc-400">{p.email}{p.phone ? ` · ${p.phone}` : ''}</div>
              <div className="text-xs text-zinc-500 mt-1">
                Applied {p.created_at?.replace('T', ' ').slice(0, 16)}
                {p.joined_via === 'public_link' && (
                  <Badge className="ml-2 bg-violet-500/20 text-violet-300">via /{p.joined_slug}</Badge>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm"
                      disabled={busy === `${p.id}:reject`}
                      data-testid={`pending-reject-${p.id}`}
                      onClick={() => {
                        const reason = window.prompt('Reason for rejection (optional)') || '';
                        act(p.id, 'reject', reason);
                      }}>
                {busy === `${p.id}:reject` ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserX className="w-4 h-4 mr-1" />} Reject
              </Button>
              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-500"
                      disabled={busy === `${p.id}:approve`}
                      data-testid={`pending-approve-${p.id}`}
                      onClick={() => act(p.id, 'approve')}>
                {busy === `${p.id}:approve` ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserCheck className="w-4 h-4 mr-1" />} Approve
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function MembersPanel() {
  const [items, setItems] = useState(null);
  useEffect(() => {
    axios.get(`${API}/api/org-admin/members`, { headers: TOK() })
      .then(({ data }) => setItems(data.members || []))
      .catch(() => toast.error('Failed to load members'));
  }, []);
  if (items === null) return <div className="py-10 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-violet-400" /></div>;
  if (!items.length) {
    return <div className="glass-card p-10 text-center text-zinc-400">
      <UserCheck className="w-10 h-10 mx-auto mb-3 opacity-50" />
      <p>No members yet.</p>
    </div>;
  }
  return (
    <div className="glass-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-zinc-900/60 text-zinc-400">
          <tr>
            <th className="text-left p-3">Name</th>
            <th className="text-left p-3">Email</th>
            <th className="text-left p-3">Role</th>
            <th className="text-left p-3">Joined via</th>
            <th className="text-left p-3">Joined</th>
            <th className="text-left p-3">Last seen</th>
          </tr>
        </thead>
        <tbody>
          {items.map((m) => (
            <tr key={m.id} className="border-t border-white/5" data-testid={`member-row-${m.id}`}>
              <td className="p-3 text-white">{m.full_name}</td>
              <td className="p-3">{m.email}</td>
              <td className="p-3 capitalize">{m.role}</td>
              <td className="p-3 text-zinc-400">{m.joined_via || 'direct'}</td>
              <td className="p-3 text-zinc-500">{m.created_at?.slice(0, 10)}</td>
              <td className="p-3 text-zinc-500">{m.last_seen_at ? m.last_seen_at.replace('T', ' ').slice(0, 16) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SettingsPanel() {
  const [s, setS] = useState(null);
  const [copied, setCopied] = useState(false);
  const [domainInput, setDomainInput] = useState('');

  const load = () => {
    axios.get(`${API}/api/org-admin/join-settings`, { headers: TOK() })
      .then(({ data }) => setS(data))
      .catch(() => toast.error('Failed to load settings'));
  };
  useEffect(load, []);

  const save = async (patch) => {
    const next = { ...s, ...patch };
    setS(next);
    try {
      const { data } = await axios.put(`${API}/api/org-admin/join-settings`, {
        enabled: next.enabled,
        require_approval: next.require_approval,
        allowed_domains: next.allowed_domains,
      }, { headers: TOK() });
      setS(data);
      toast.success('Saved');
    } catch (e) {
      toast.error('Save failed');
      load();
    }
  };

  const joinUrl = useMemo(() => {
    if (!s?.join_slug) return '';
    return `${window.location.origin}/join/${s.join_slug}`;
  }, [s]);

  const copy = () => {
    navigator.clipboard.writeText(joinUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
    toast.success('Link copied');
  };

  const qrUrl = joinUrl ? `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(joinUrl)}` : '';

  if (!s) return <div className="py-10 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-violet-400" /></div>;

  return (
    <div className="space-y-6">
      {/* Link block */}
      <Card className="bg-zinc-900/60 border-white/10">
        <CardContent className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h3 className="text-lg font-semibold text-white flex items-center gap-2"><Link2 className="w-5 h-5 text-violet-400" /> Your Public Join Link</h3>
              <p className="text-sm text-zinc-400 mt-1">Share this URL. Anyone visiting can sign up and become a member of your organization.</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-zinc-400">Enabled</span>
              <Switch data-testid="join-enable-toggle"
                      checked={!!s.enabled} onCheckedChange={(v) => save({ enabled: v })} />
              {s.enabled
                ? <Badge className="bg-emerald-500/20 text-emerald-300"><ShieldCheck className="w-3 h-3 mr-1" /> Live</Badge>
                : <Badge className="bg-zinc-800 text-zinc-400"><ShieldOff className="w-3 h-3 mr-1" /> Disabled</Badge>}
            </div>
          </div>

          <div className="flex gap-2 items-center bg-zinc-950 border border-white/10 rounded-lg p-3">
            <code className="flex-1 text-sm text-violet-300 truncate" data-testid="join-url">{joinUrl}</code>
            <Button size="sm" variant="outline" data-testid="join-copy-btn" onClick={copy}>
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </Button>
          </div>

          <div className="grid sm:grid-cols-[auto,1fr] gap-6 pt-2">
            <div className="flex flex-col items-center gap-2">
              <img src={qrUrl} alt="Join QR" className="rounded-lg bg-white p-2" data-testid="join-qr" />
              <span className="text-xs text-zinc-500 flex items-center gap-1"><QrCode className="w-3 h-3" /> Scan to open</span>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-zinc-950/70 rounded-lg border border-white/5">
                <div>
                  <div className="text-sm text-white">Require admin approval</div>
                  <div className="text-xs text-zinc-500">If off, new signups are auto-activated.</div>
                </div>
                <Switch data-testid="join-approval-toggle"
                        checked={!!s.require_approval}
                        onCheckedChange={(v) => save({ require_approval: v })} />
              </div>
              <div className="p-3 bg-zinc-950/70 rounded-lg border border-white/5 space-y-2">
                <div className="text-sm text-white">Restrict to email domains</div>
                <div className="text-xs text-zinc-500">Leave empty to allow everyone. Enter one domain per entry.</div>
                <div className="flex gap-2">
                  <Input value={domainInput}
                         data-testid="join-domain-input"
                         onChange={(e) => setDomainInput(e.target.value)}
                         placeholder="example.com"
                         className="bg-zinc-950 border-white/10 flex-1" />
                  <Button size="sm" data-testid="join-domain-add"
                          onClick={() => {
                            const d = domainInput.trim().toLowerCase().replace(/^@/, '');
                            if (!d) return;
                            if (s.allowed_domains.includes(d)) return toast.error('Already added');
                            save({ allowed_domains: [...s.allowed_domains, d] });
                            setDomainInput('');
                          }}>Add</Button>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  {s.allowed_domains.map((d) => (
                    <Badge key={d} className="bg-violet-500/20 text-violet-300 cursor-pointer"
                           data-testid={`join-domain-chip-${d}`}
                           onClick={() => save({ allowed_domains: s.allowed_domains.filter(x => x !== d) })}>
                      {d} ✕
                    </Badge>
                  ))}
                  {s.allowed_domains.length === 0 && <span className="text-xs text-zinc-500">All domains allowed.</span>}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
