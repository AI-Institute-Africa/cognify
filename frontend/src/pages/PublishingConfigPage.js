/* Super Admin → Publishing Configuration */
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Loader2, Newspaper, ExternalLink, RefreshCw, Plus, Trash2, PlayCircle,
  ShieldCheck, ShieldOff, Send, ChevronRight
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
  { key: 'overview',    label: 'Overview' },
  { key: 'destinations', label: 'Destinations' },
  { key: 'history',     label: 'Publishing History' },
];

export default function PublishingConfigPage() {
  const [tab, setTab] = useState('overview');
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold flex items-center gap-3">
            <Newspaper className="w-7 h-7 text-violet-400" /> Publishing Configuration
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Weekly-rotating publication to Cognify News and AI Institute Africa. The active destination flips
            automatically every ISO week — administrators can override, disable rotation, or add new destinations.
          </p>
        </div>
        <div className="flex gap-2 mb-6 border-b border-white/5">
          {TABS.map((t) => (
            <button key={t.key}
                    data-testid={`pub-tab-${t.key}`}
                    onClick={() => setTab(t.key)}
                    className={`px-4 py-2 text-sm border-b-2 -mb-px transition ${
                      tab === t.key ? 'border-violet-500 text-white' : 'border-transparent text-zinc-400 hover:text-zinc-200'
                    }`}>{t.label}</button>
          ))}
        </div>
        {tab === 'overview' && <OverviewPanel />}
        {tab === 'destinations' && <DestinationsPanel />}
        {tab === 'history' && <HistoryPanel />}
      </div>
    </div>
  );
}

function OverviewPanel() {
  const [stats, setStats] = useState(null);
  const [dests, setDests] = useState([]);
  const [busy, setBusy] = useState(false);
  const load = () => {
    axios.get(`${API}/api/super-admin/publishing/stats`, { headers: TOK() })
      .then(({ data }) => setStats(data))
      .catch(() => toast.error('Failed to load stats'));
    axios.get(`${API}/api/super-admin/publishing/destinations`, { headers: TOK() })
      .then(({ data }) => setDests(data.destinations || []));
  };
  useEffect(() => { load(); }, []);

  const toggleRotation = async (enabled) => {
    await axios.put(`${API}/api/super-admin/publishing/settings`,
      { rotation_enabled: enabled }, { headers: TOK() });
    toast.success(enabled ? 'Weekly rotation enabled' : 'Weekly rotation disabled');
    load();
  };
  const setOverride = async (destId) => {
    await axios.put(`${API}/api/super-admin/publishing/settings`,
      { manual_override_destination_id: destId }, { headers: TOK() });
    toast.success(destId ? 'Override applied for this week' : 'Override cleared');
    load();
  };
  const runTest = async () => {
    setBusy(true);
    try {
      const { data } = await axios.post(`${API}/api/super-admin/publishing/test`, {}, { headers: TOK() });
      toast.success(`Test article published to ${data.active_destination?.name}`);
      load();
    } catch (e) {
      toast.error('Test publish failed');
    } finally {
      setBusy(false);
    }
  };

  if (!stats) return <div className="py-10 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-violet-400" /></div>;

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-2 gap-4">
        <Card className="bg-zinc-900/60 border-violet-500/30">
          <CardContent className="p-5">
            <div className="text-xs text-zinc-500 uppercase mb-1">Current Active Website</div>
            <div className="text-2xl font-semibold text-white" data-testid="pub-active-name">
              {stats.active_destination?.name || '—'}
            </div>
            <a href={stats.active_destination?.site_url} target="_blank" rel="noreferrer"
               className="text-sm text-violet-400 hover:text-violet-300 flex items-center gap-1 mt-2"
               data-testid="pub-active-url">
              {stats.active_destination?.site_url} <ExternalLink className="w-3 h-3" />
            </a>
            <Badge className="mt-3 bg-emerald-500/20 text-emerald-300">Week {stats.iso_week}, {stats.iso_year}</Badge>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/60 border-white/10">
          <CardContent className="p-5">
            <div className="text-xs text-zinc-500 uppercase mb-1">Next Scheduled Website</div>
            <div className="text-2xl font-semibold text-zinc-300" data-testid="pub-next-name">
              {stats.next_destination?.name || '—'}
            </div>
            <div className="text-sm text-zinc-500 mt-2">{stats.next_destination?.site_url}</div>
            <Badge className="mt-3 bg-zinc-800 text-zinc-300">Week {stats.iso_week + 1}</Badge>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-zinc-900/60 border-white/10">
        <CardContent className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold text-white">Weekly Rotation</div>
              <div className="text-xs text-zinc-500">Automatically switches destination each ISO week.</div>
            </div>
            <Switch data-testid="pub-rotation-toggle" checked={!!stats.rotation_enabled}
                    onCheckedChange={toggleRotation} />
          </div>
          <div className="border-t border-white/5 pt-4">
            <div className="text-sm text-zinc-300 mb-2">Manual Override (this week only)</div>
            <div className="flex flex-wrap gap-2">
              {dests.map((d) => (
                <button key={d.id}
                        data-testid={`pub-override-${d.id}`}
                        onClick={() => setOverride(d.id)}
                        className={`px-3 py-1.5 rounded-lg text-sm border ${
                          stats.manual_override?.destination_id === d.id
                            ? 'border-violet-500 bg-violet-500/10 text-violet-200'
                            : 'border-white/10 text-zinc-300 hover:border-violet-500/40'
                        }`}>
                  {d.name}
                </button>
              ))}
              {stats.manual_override?.destination_id && (
                <Button size="sm" variant="ghost" data-testid="pub-override-clear"
                        onClick={() => setOverride(null)}>Clear override</Button>
              )}
            </div>
          </div>
          <div className="border-t border-white/5 pt-4 flex flex-wrap gap-3">
            <Button disabled={busy} onClick={runTest} data-testid="pub-test-btn"
                    className="bg-violet-600 hover:bg-violet-500">
              {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <PlayCircle className="w-4 h-4 mr-2" />}
              Publish Test Article
            </Button>
            <Button variant="outline" data-testid="pub-view-news"
                    onClick={() => window.open('/news', '_blank')}>
              View /news page <ExternalLink className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function DestinationsPanel() {
  const [items, setItems] = useState(null);
  const [form, setForm] = useState({ name: '', site_url: '', scope: 'external', webhook_url: '', webhook_secret: '', enabled: true });
  const [busy, setBusy] = useState(false);
  const load = () => { axios.get(`${API}/api/super-admin/publishing/destinations`, { headers: TOK() })
    .then(({ data }) => setItems(data.destinations || [])); };
  useEffect(() => { load(); }, []);

  const patch = async (id, body) => {
    await axios.put(`${API}/api/super-admin/publishing/destinations/${id}`, body, { headers: TOK() });
    toast.success('Saved');
    load();
  };
  const remove = async (id) => {
    if (!window.confirm('Remove this destination?')) return;
    await axios.delete(`${API}/api/super-admin/publishing/destinations/${id}`, { headers: TOK() });
    toast.success('Removed');
    load();
  };
  const add = async () => {
    if (!form.name || !form.site_url) return toast.error('Name & site URL required');
    setBusy(true);
    try {
      await axios.post(`${API}/api/super-admin/publishing/destinations`, form, { headers: TOK() });
      toast.success('Destination added');
      setForm({ name: '', site_url: '', scope: 'external', webhook_url: '', webhook_secret: '', enabled: true });
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to add');
    } finally { setBusy(false); }
  };

  if (items === null) return <div className="py-10 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-violet-400" /></div>;

  return (
    <div className="space-y-4">
      {items.map((d) => (
        <Card key={d.id} className="bg-zinc-900/60 border-white/10" data-testid={`pub-dest-${d.id}`}>
          <CardContent className="p-4 flex items-center justify-between gap-4 flex-wrap">
            <div className="flex-1 min-w-[280px]">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-white">{d.name}</span>
                <Badge className={d.scope === 'internal' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-blue-500/20 text-blue-300'}>{d.scope}</Badge>
                <Badge className="bg-zinc-800 text-zinc-400">order {d.order}</Badge>
              </div>
              <div className="text-sm text-violet-300 mt-1">{d.site_url}</div>
              {d.webhook_url && <div className="text-xs text-zinc-500 mt-1">Webhook: {d.webhook_url}</div>}
            </div>
            <div className="flex items-center gap-3">
              <Switch checked={!!d.enabled}
                      data-testid={`pub-dest-toggle-${d.id}`}
                      onCheckedChange={(v) => patch(d.id, { enabled: v })} />
              <Button size="sm" variant="outline"
                      data-testid={`pub-dest-edit-${d.id}`}
                      onClick={() => {
                        const w = window.prompt('Webhook URL (leave empty to clear):', d.webhook_url || '');
                        if (w === null) return;
                        const s = window.prompt('Webhook secret (leave empty to clear):', d.webhook_secret || '');
                        if (s === null) return;
                        patch(d.id, { webhook_url: w || null, webhook_secret: s || null });
                      }}>Edit webhook</Button>
              <Button size="sm" variant="ghost" onClick={() => remove(d.id)} data-testid={`pub-dest-del-${d.id}`}>
                <Trash2 className="w-4 h-4 text-rose-400" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}

      <Card className="bg-zinc-900/60 border-white/10">
        <CardContent className="p-5">
          <div className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Plus className="w-5 h-5" /> Add New Destination
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            <div>
              <Label>Name</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                     data-testid="pub-new-name" className="bg-zinc-950 border-white/10 mt-1" />
            </div>
            <div>
              <Label>Site URL</Label>
              <Input value={form.site_url} onChange={(e) => setForm({ ...form, site_url: e.target.value })}
                     data-testid="pub-new-url" className="bg-zinc-950 border-white/10 mt-1"
                     placeholder="https://example.com/news" />
            </div>
            <div>
              <Label>Scope</Label>
              <select value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })}
                      data-testid="pub-new-scope"
                      className="w-full bg-zinc-950 border border-white/10 rounded-md h-10 px-3 mt-1 text-sm text-white">
                <option value="internal">internal (rendered by Cognify)</option>
                <option value="external">external (webhook POST)</option>
              </select>
            </div>
            <div>
              <Label>Webhook URL (optional, external only)</Label>
              <Input value={form.webhook_url} onChange={(e) => setForm({ ...form, webhook_url: e.target.value })}
                     data-testid="pub-new-webhook" className="bg-zinc-950 border-white/10 mt-1"
                     placeholder="https://target.example.com/api/receive" />
            </div>
          </div>
          <Button className="mt-4 bg-violet-600 hover:bg-violet-500"
                  disabled={busy} onClick={add} data-testid="pub-new-add">
            {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
            Add Destination
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function HistoryPanel() {
  const [items, setItems] = useState(null);
  useEffect(() => {
    axios.get(`${API}/api/super-admin/publishing/history?limit=200`, { headers: TOK() })
      .then(({ data }) => setItems(data.articles || []))
      .catch(() => setItems([]));
  }, []);
  if (items === null) return <div className="py-10 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-violet-400" /></div>;
  if (!items.length) return <div className="glass-card p-10 text-center text-zinc-400">
    <p>Nothing published yet. Run the digest or click "Publish Test Article" on Overview.</p>
  </div>;
  return (
    <div className="glass-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-zinc-900/60 text-zinc-400">
          <tr>
            <th className="text-left p-3">Title</th>
            <th className="text-left p-3">Destination</th>
            <th className="text-left p-3">Week</th>
            <th className="text-left p-3">Published at</th>
            <th className="text-left p-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr key={a.id} className="border-t border-white/5" data-testid={`pub-hist-${a.id}`}>
              <td className="p-3 text-white truncate max-w-md">{a.title}</td>
              <td className="p-3">{a.destination_name}</td>
              <td className="p-3">{a.published_week}, {a.published_year}</td>
              <td className="p-3 text-zinc-500">{a.published_at?.replace('T', ' ').slice(0, 16)}</td>
              <td className="p-3">
                {a.publish_status === 'published' && <Badge className="bg-emerald-500/20 text-emerald-300">published</Badge>}
                {a.publish_status === 'webhook_failed' && <Badge className="bg-rose-500/20 text-rose-300">webhook failed</Badge>}
                {!['published', 'webhook_failed'].includes(a.publish_status) && <Badge>{a.publish_status}</Badge>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
