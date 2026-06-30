import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import {
  CreditCard, DollarSign, Settings as SettingsIcon, Wallet, Receipt, RefreshCw,
  PackageOpen, ListChecks, BarChart3, Tag, Globe, Shield, Mail, Webhook, Activity,
  CheckCircle2, XCircle, Loader2, Eye, Plus, Trash2, AlertCircle, Menu, Users as UsersIcon,
  ExternalLink, Clock,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;
const TOKEN = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

const MENU = [
  { key: 'dashboard',     label: 'Dashboard',         icon: BarChart3 },
  { key: 'providers',     label: 'Providers',         icon: CreditCard },
  { key: 'products',      label: 'Products',          icon: PackageOpen },
  { key: 'subscriptions', label: 'Subscriptions',     icon: ListChecks },
  { key: 'transactions',  label: 'Transactions',      icon: DollarSign },
  { key: 'invoices',      label: 'Invoices',          icon: Receipt },
  { key: 'receipts',      label: 'Receipts',          icon: Receipt },
  { key: 'refunds',       label: 'Refunds',           icon: RefreshCw },
  { key: 'payment-logs',  label: 'Payment Logs',      icon: Activity },
  { key: 'webhook-logs',  label: 'Webhook Logs',      icon: Webhook },
  { key: 'audit-logs',    label: 'Audit Logs',        icon: Shield },
  { key: 'revenue',       label: 'Revenue Analytics', icon: BarChart3 },
  { key: 'pricing-plans', label: 'Pricing Plans',     icon: Tag },
  { key: 'coupons',       label: 'Coupons',           icon: Tag },
  { key: 'taxes',         label: 'Taxes',             icon: Tag },
  { key: 'currencies',    label: 'Currencies',        icon: Globe },
  { key: 'settings',      label: 'Settings',          icon: SettingsIcon },
  { key: 'api-config',    label: 'API Configuration', icon: SettingsIcon },
  { key: 'notifications', label: 'Notification Settings', icon: Mail },
  { key: 'email-templates', label: 'Email Templates', icon: Mail },
  { key: 'activity',      label: 'User Activity',     icon: UsersIcon },
  { key: 'security',      label: 'Security',          icon: Shield },
];

export default function PaymentManagementPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [active, setActive] = useState('dashboard');

  useEffect(() => {
    const r = () => setIsMobile(window.innerWidth < 1024);
    r(); window.addEventListener('resize', r);
    return () => window.removeEventListener('resize', r);
  }, []);

  return (
    <div className="min-h-screen bg-[#09090B] text-zinc-100">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} isMobile={isMobile} />
      <main className={`min-h-screen ${isMobile ? '' : 'ml-64'}`}>
        <header className="border-b border-white/5 sticky top-0 z-20 bg-[#09090B]/95 backdrop-blur">
          <div className="px-6 py-4 flex items-center gap-3">
            {isMobile && (
              <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-white/5">
                <Menu className="w-5 h-5" />
              </button>
            )}
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
              <Wallet className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-semibold">Payment Management</h1>
              <p className="text-xs text-zinc-500">Provider-independent payment platform</p>
            </div>
          </div>
        </header>

        <div className="max-w-[1600px] mx-auto px-4 py-6 grid grid-cols-1 xl:grid-cols-12 gap-6">
          {/* LEFT NAV */}
          <aside className="xl:col-span-3 2xl:col-span-2">
            <div className="glass-card p-2 sticky top-24">
              <nav className="space-y-0.5">
                {MENU.map((m) => {
                  const Icon = m.icon;
                  const isActive = active === m.key;
                  return (
                    <button
                      key={m.key}
                      onClick={() => setActive(m.key)}
                      data-testid={`pay-menu-${m.key}`}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors ${
                        isActive ? 'bg-violet-500/20 text-violet-200 border border-violet-500/30'
                                 : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'
                      }`}
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span className="truncate">{m.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          </aside>

          {/* MAIN CONTENT */}
          <section className="xl:col-span-9 2xl:col-span-10">
            {active === 'dashboard' && <DashboardPanel />}
            {active === 'providers' && <ProvidersPanel />}
            {active === 'products' && <ProductsPanel />}
            {active === 'subscriptions' && <SimpleListPanel endpoint="subscriptions" label="Subscriptions" empty="No active subscriptions yet." />}
            {active === 'transactions' && <SimpleListPanel endpoint="transactions" label="Transactions" empty="No transactions yet." showAmount />}
            {active === 'invoices' && <SimpleListPanel endpoint="invoices" label="Invoices" empty="No invoices yet." showAmount />}
            {active === 'receipts' && <SimpleListPanel endpoint="receipts" label="Receipts" empty="No receipts yet." />}
            {active === 'refunds' && <SimpleListPanel endpoint="refunds" label="Refunds" empty="No refunds processed." />}
            {active === 'payment-logs' && <LogsPanel endpoint="payment-logs" label="Payment Logs" />}
            {active === 'webhook-logs' && <LogsPanel endpoint="webhook-logs" label="Webhook Events" />}
            {active === 'audit-logs' && <LogsPanel endpoint="audit-logs" label="Audit Logs" />}
            {active === 'revenue' && <RevenuePanel />}
            {active === 'pricing-plans' && <CRUDPanel endpoint="pricing-plans" label="Pricing Plans" fields={['name','price','currency','interval','description']} />}
            {active === 'coupons' && <CRUDPanel endpoint="coupons" label="Coupons" fields={['code','discount_percent','currency','expires_at','description']} />}
            {active === 'taxes' && <CRUDPanel endpoint="taxes" label="Taxes" fields={['name','rate','country','description']} />}
            {active === 'currencies' && <CRUDPanel endpoint="currencies" label="Currencies" fields={['code','name','symbol','rate_to_usd']} />}
            {active === 'settings' && <SettingsPanel />}
            {active === 'api-config' && <ApiConfigPanel />}
            {active === 'notifications' && <NotificationSettingsPanel />}
            {active === 'email-templates' && <CRUDPanel endpoint="email-templates" label="Email Templates" fields={['name','subject','body']} largeFields={['body']} />}
            {active === 'activity' && <ActivityPanel />}
            {active === 'security' && <SecurityPanel />}
          </section>
        </div>
      </main>
    </div>
  );
}

/* ============== DASHBOARD ============== */
function DashboardPanel() {
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/api/super-admin/payments/dashboard`, { headers: TOKEN() });
      setD(data);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to load dashboard'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>;
  if (!d) return null;
  const cards = [
    { label: 'Today',     v: d.revenue.today,   color: 'from-emerald-500 to-teal-500' },
    { label: 'Week',      v: d.revenue.week,    color: 'from-blue-500 to-cyan-500' },
    { label: 'Month',     v: d.revenue.month,   color: 'from-violet-500 to-fuchsia-500' },
    { label: 'Year',      v: d.revenue.year,    color: 'from-amber-500 to-orange-500' },
  ];
  const tx = d.transactions || {};
  const ctrs = [
    ['Total', tx.total, 'text-zinc-300'],
    ['Successful', tx.successful, 'text-emerald-400'],
    ['Pending', tx.pending, 'text-amber-400'],
    ['Failed', tx.failed, 'text-rose-400'],
    ['Cancelled', tx.cancelled, 'text-zinc-500'],
    ['Refunded', tx.refunded, 'text-blue-400'],
  ];
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Payment Overview</h2>
        <Button variant="outline" className="border-white/10" onClick={load} data-testid="pay-refresh">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c) => (
          <div key={c.label} className="glass-card p-5">
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${c.color} flex items-center justify-center mb-3`}>
              <DollarSign className="w-5 h-5 text-white" />
            </div>
            <p className="text-3xl font-bold">${(c.v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
            <p className="text-sm text-zinc-400 mt-1">{c.label} Revenue</p>
          </div>
        ))}
      </div>
      <div className="glass-card p-5">
        <h3 className="font-semibold mb-3">Transactions</h3>
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-3">
          {ctrs.map(([label, val, color]) => (
            <div key={label} className="rounded-lg bg-zinc-900/60 border border-white/5 p-3">
              <p className={`text-2xl font-bold ${color}`}>{val || 0}</p>
              <p className="text-xs text-zinc-500">{label}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card p-5">
          <h3 className="font-semibold mb-3">Subscriptions</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/5">
              <p className="text-2xl font-bold text-emerald-400">{d.subscriptions?.active || 0}</p>
              <p className="text-xs text-zinc-500">Active</p>
            </div>
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/5">
              <p className="text-2xl font-bold text-zinc-500">{d.subscriptions?.expired || 0}</p>
              <p className="text-xs text-zinc-500">Expired</p>
            </div>
          </div>
        </div>
        <div className="glass-card p-5">
          <h3 className="font-semibold mb-3">Avg Transaction</h3>
          <p className="text-3xl font-bold text-violet-300">${(d.revenue?.avg_transaction || 0).toFixed(2)}</p>
          <p className="text-xs text-zinc-500 mt-1">across today&apos;s successful payments</p>
        </div>
      </div>
      <div className="glass-card p-5">
        <h3 className="font-semibold mb-3">Recent Transactions</h3>
        {(d.recent_transactions || []).length === 0
          ? <p className="text-sm text-zinc-500">No transactions yet.</p>
          : <TxTable rows={d.recent_transactions} />}
      </div>
      <div className="glass-card p-5">
        <h3 className="font-semibold mb-3">Recent Errors</h3>
        {(d.recent_errors || []).length === 0
          ? <p className="text-sm text-zinc-500">No errors logged.</p>
          : <ul className="space-y-1 text-sm font-mono text-zinc-400">
              {d.recent_errors.map((e, i) => (
                <li key={i} className="border-b border-white/5 py-1">
                  <span className="text-rose-400">[{e.level}]</span> {e.provider}/{e.event}: {e.message}
                </li>
              ))}
            </ul>}
      </div>
    </div>
  );
}

function TxTable({ rows }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-zinc-500">
          <tr className="text-left">
            <th className="py-2 px-2 font-medium">Reference</th>
            <th className="py-2 px-2 font-medium">Amount</th>
            <th className="py-2 px-2 font-medium">Provider</th>
            <th className="py-2 px-2 font-medium">Status</th>
            <th className="py-2 px-2 font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-t border-white/5">
              <td className="py-2 px-2 font-mono text-xs">{r.reference || r.id?.slice(0,8)}</td>
              <td className="py-2 px-2">{r.currency} {r.amount}</td>
              <td className="py-2 px-2 capitalize">{r.provider}</td>
              <td className="py-2 px-2"><StatusBadge s={r.status} /></td>
              <td className="py-2 px-2 text-xs text-zinc-500">{(r.created_at || '').slice(0,16).replace('T', ' ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ s }) {
  const map = {
    paid: 'bg-emerald-500/20 text-emerald-300', succeeded: 'bg-emerald-500/20 text-emerald-300',
    completed: 'bg-emerald-500/20 text-emerald-300',
    pending: 'bg-amber-500/20 text-amber-300', initiated: 'bg-amber-500/20 text-amber-300',
    failed: 'bg-rose-500/20 text-rose-300', cancelled: 'bg-zinc-500/20 text-zinc-300',
    refunded: 'bg-blue-500/20 text-blue-300',
    active: 'bg-emerald-500/20 text-emerald-300', expired: 'bg-zinc-500/20 text-zinc-300',
    paused: 'bg-amber-500/20 text-amber-300',
  };
  return <Badge className={`capitalize ${map[s] || 'bg-zinc-700 text-zinc-300'}`}>{s}</Badge>;
}

/* ============== PROVIDERS ============== */
function ProvidersPanel() {
  const [providers, setProviders] = useState([]);
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState({});
  const load = useCallback(async () => {
    const { data } = await axios.get(`${API}/api/super-admin/payments/providers`, { headers: TOKEN() });
    setProviders(data.providers || []);
  }, []);
  useEffect(() => { load(); }, [load]);

  const toggle = async (slug, enabled) => {
    setBusy((b) => ({ ...b, [slug]: true }));
    try {
      await axios.post(`${API}/api/super-admin/payments/providers/${slug}/${enabled ? 'enable' : 'disable'}`, {}, { headers: TOKEN() });
      toast.success(`${slug} ${enabled ? 'enabled' : 'disabled'}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setBusy((b) => { const n = { ...b }; delete n[slug]; return n; }); }
  };
  const testConn = async (slug) => {
    setBusy((b) => ({ ...b, [slug + '-test']: true }));
    try {
      const { data } = await axios.post(`${API}/api/super-admin/payments/providers/${slug}/test`, {}, { headers: TOKEN() });
      toast[data.ok ? 'success' : 'error'](data.message || (data.ok ? 'OK' : 'Failed'));
      load();
    } catch (e) { toast.error('Test failed'); }
    finally { setBusy((b) => { const n = { ...b }; delete n[slug + '-test']; return n; }); }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Payment Providers</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {providers.map((p) => (
          <div key={p.slug} className="glass-card p-5" data-testid={`provider-card-${p.slug}`}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-lg flex items-center gap-2">
                  {p.display_name}
                  {p.is_primary && <Badge className="bg-violet-500/20 text-violet-300 text-xs">Primary</Badge>}
                </h3>
                <p className="text-xs text-zinc-500">{p.environment} · {p.api_version}</p>
              </div>
              <Switch checked={!!p.enabled} onCheckedChange={(v) => toggle(p.slug, v)}
                disabled={busy[p.slug]} data-testid={`provider-toggle-${p.slug}`} />
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-zinc-500 mb-3">
              <div>Status:{' '}
                {p.health_status === 'healthy' ? <span className="text-emerald-400">healthy</span>
                 : p.health_status === 'error' ? <span className="text-rose-400">error</span>
                 : <span className="text-zinc-400">untested</span>}
              </div>
              <div>Webhook: <span className="text-zinc-400">{p.webhook_status}</span></div>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" className="border-white/10" onClick={() => setEditing(p)}
                data-testid={`provider-configure-${p.slug}`}>
                <SettingsIcon className="w-3 h-3 mr-1" /> Configure
              </Button>
              <Button size="sm" variant="outline" className="border-emerald-500/30 text-emerald-300"
                disabled={busy[p.slug + '-test']} onClick={() => testConn(p.slug)}
                data-testid={`provider-test-${p.slug}`}>
                {busy[p.slug + '-test'] ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <CheckCircle2 className="w-3 h-3 mr-1" />}
                Test
              </Button>
            </div>
          </div>
        ))}
      </div>
      {editing && <ConfigureProviderModal provider={editing} onClose={() => setEditing(null)} onSaved={load} />}
    </div>
  );
}

function ConfigureProviderModal({ provider, onClose, onSaved }) {
  const isPaynow = provider.slug === 'paynow';
  const [form, setForm] = useState(() => ({
    environment: provider.environment || 'sandbox',
    integration_id: provider.integration_id || '',
    integration_key: '', // blank = leave existing
    result_url: provider.result_url || '',
    return_url: provider.return_url || '',
    merchant_name: provider.merchant_name || '',
    merchant_email: provider.merchant_email || '',
    default_currency: provider.default_currency || 'USD',
    webhook_secret: '',
    api_key: '', secret_key: '', encryption_key: '',
    client_id: provider.client_id || '', client_secret: '',
  }));
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      const patch = { ...form };
      // Strip empty secrets so we preserve existing values
      ['integration_key','webhook_secret','api_key','secret_key','encryption_key','client_secret','publishable_key']
        .forEach((k) => { if (!patch[k]) delete patch[k]; });
      await axios.put(`${API}/api/super-admin/payments/providers/${provider.slug}`, patch, { headers: TOKEN() });
      toast.success('Provider configuration saved');
      onSaved(); onClose();
    } catch (e) { toast.error(e.response?.data?.detail || 'Save failed'); }
    finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-zinc-950 border border-white/10 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 border-b border-white/5 flex items-center justify-between sticky top-0 bg-zinc-950">
          <h3 className="font-semibold text-lg">Configure {provider.display_name}</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg"><XCircle className="w-5 h-5" /></button>
        </div>
        <div className="p-5 space-y-3">
          {isPaynow ? (
            <>
              <Field label="Integration ID" value={form.integration_id} onChange={(v) => setForm({...form, integration_id: v})} testid="cfg-integration-id" />
              <Field label="Integration Key (encrypted at rest — leave blank to keep existing)" type="password"
                value={form.integration_key} onChange={(v) => setForm({...form, integration_key: v})} testid="cfg-integration-key" />
              <div className="text-xs text-zinc-500">
                Current secret: <span className="font-mono">{provider.integration_key_preview || '— not set —'}</span>
              </div>
              <Field label="Result URL" value={form.result_url} onChange={(v) => setForm({...form, result_url: v})} testid="cfg-result-url" />
              <Field label="Return URL" value={form.return_url} onChange={(v) => setForm({...form, return_url: v})} testid="cfg-return-url" />
              <Field label="Merchant Name" value={form.merchant_name} onChange={(v) => setForm({...form, merchant_name: v})} />
              <Field label="Merchant Email" value={form.merchant_email} onChange={(v) => setForm({...form, merchant_email: v})} />
              <Field label="Default Currency" value={form.default_currency} onChange={(v) => setForm({...form, default_currency: v})} />
              <Field label="Webhook Secret (encrypted; blank = keep existing)" type="password"
                value={form.webhook_secret} onChange={(v) => setForm({...form, webhook_secret: v})} />
            </>
          ) : (
            <>
              <Field label="API Key (encrypted; blank = keep existing)" type="password"
                value={form.api_key} onChange={(v) => setForm({...form, api_key: v})} />
              <Field label="Secret Key (encrypted; blank = keep existing)" type="password"
                value={form.secret_key} onChange={(v) => setForm({...form, secret_key: v})} />
              <Field label="Webhook Secret" type="password"
                value={form.webhook_secret} onChange={(v) => setForm({...form, webhook_secret: v})} />
            </>
          )}
          <div>
            <label className="text-xs text-zinc-400 mb-1 block">Environment</label>
            <select value={form.environment} onChange={(e) => setForm({...form, environment: e.target.value})}
              className="w-full bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-sm">
              <option value="sandbox">Sandbox</option>
              <option value="production">Production</option>
            </select>
          </div>
        </div>
        <div className="p-5 border-t border-white/5 flex gap-2 justify-end sticky bottom-0 bg-zinc-950">
          <Button variant="outline" className="border-white/10" onClick={onClose}>Cancel</Button>
          <Button onClick={save} disabled={saving} className="bg-violet-500 hover:bg-violet-600" data-testid="cfg-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Save Configuration
          </Button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', testid }) {
  return (
    <div>
      <label className="text-xs text-zinc-400 mb-1 block">{label}</label>
      <Input value={value} type={type} onChange={(e) => onChange(e.target.value)}
        className="bg-zinc-900 border-white/10" data-testid={testid} />
    </div>
  );
}

/* ============== PRODUCTS ============== */
function ProductsPanel() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const load = async () => {
    const { data } = await axios.get(`${API}/api/super-admin/payments/products`, { headers: TOKEN() });
    setItems(data.products || []);
  };
  useEffect(() => { load(); }, []);
  const del = async (id) => {
    if (!window.confirm('Delete this product?')) return;
    await axios.delete(`${API}/api/super-admin/payments/products/${id}`, { headers: TOKEN() });
    toast.success('Deleted'); load();
  };
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Payment Products</h2>
        <Button onClick={() => setOpen(true)} className="bg-violet-500 hover:bg-violet-600" data-testid="pay-add-product">
          <Plus className="w-4 h-4 mr-2" /> New Product
        </Button>
      </div>
      {items.length === 0 ? (
        <div className="glass-card p-12 text-center text-zinc-500">No products yet. Create your first one.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {items.map((p) => (
            <div key={p.id} className="glass-card p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{p.title}</h3>
                  <p className="text-xs text-zinc-500">{p.category} · {p.billing_type}{p.billing_interval ? ` · ${p.billing_interval}` : ''}</p>
                </div>
                <Badge className="bg-emerald-500/20 text-emerald-300">{p.currency} {p.price}</Badge>
              </div>
              <p className="text-sm text-zinc-400 mt-2 line-clamp-2">{p.description || '—'}</p>
              <div className="flex justify-end mt-3">
                <Button size="sm" variant="outline" className="border-rose-500/30 text-rose-300" onClick={() => del(p.id)}>
                  <Trash2 className="w-3 h-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
      {open && <ProductModal onClose={() => setOpen(false)} onSaved={() => { setOpen(false); load(); }} />}
    </div>
  );
}

function ProductModal({ onClose, onSaved }) {
  const [f, setF] = useState({
    title: '', description: '', category: 'general',
    price: 0, currency: 'USD', tax_rate: 0, discount: 0,
    billing_type: 'one_time', billing_interval: '', visibility: 'public', status: 'active',
  });
  const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/api/super-admin/payments/products`, f, { headers: TOKEN() });
      toast.success('Product created'); onSaved();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setSaving(false); }
  };
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-zinc-950 border border-white/10 rounded-2xl max-w-2xl w-full p-5 space-y-3" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-semibold text-lg">New Product</h3>
        <Field label="Title" value={f.title} onChange={(v) => setF({...f, title: v})} testid="prod-title" />
        <Field label="Description" value={f.description} onChange={(v) => setF({...f, description: v})} />
        <div className="grid grid-cols-3 gap-3">
          <Field label="Price" type="number" value={f.price} onChange={(v) => setF({...f, price: parseFloat(v) || 0})} testid="prod-price" />
          <Field label="Currency" value={f.currency} onChange={(v) => setF({...f, currency: v})} />
          <Field label="Category" value={f.category} onChange={(v) => setF({...f, category: v})} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-zinc-400 mb-1 block">Billing</label>
            <select value={f.billing_type} onChange={(e) => setF({...f, billing_type: e.target.value})}
              className="w-full bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-sm">
              <option value="one_time">One-time</option>
              <option value="subscription">Subscription</option>
            </select>
          </div>
          {f.billing_type === 'subscription' && (
            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Interval</label>
              <select value={f.billing_interval} onChange={(e) => setF({...f, billing_interval: e.target.value})}
                className="w-full bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-sm">
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="biannual">Biannual</option>
                <option value="annual">Annual</option>
                <option value="lifetime">Lifetime</option>
              </select>
            </div>
          )}
        </div>
        <div className="flex gap-2 justify-end pt-2">
          <Button variant="outline" className="border-white/10" onClick={onClose}>Cancel</Button>
          <Button onClick={save} disabled={saving} className="bg-violet-500 hover:bg-violet-600" data-testid="prod-save">
            {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null} Save
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ============== GENERIC LIST PANELS ============== */
function SimpleListPanel({ endpoint, label, empty, showAmount }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    (async () => {
      try {
        const { data } = await axios.get(`${API}/api/super-admin/payments/${endpoint}`, { headers: TOKEN() });
        setItems(data.items || []);
      } catch (e) { toast.error(`Failed to load ${label}`); }
      finally { setLoading(false); }
    })();
  }, [endpoint, label]);
  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>;
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">{label}</h2>
      {items.length === 0 ? (
        <div className="glass-card p-12 text-center text-zinc-500">{empty}</div>
      ) : (
        <div className="glass-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900/60 text-zinc-400">
              <tr>
                <th className="text-left p-3">ID</th>
                {showAmount && <th className="text-left p-3">Amount</th>}
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id} className="border-t border-white/5">
                  <td className="p-3 font-mono text-xs">{r.reference || r.id?.slice(0, 12)}</td>
                  {showAmount && <td className="p-3">{r.currency} {r.amount}</td>}
                  <td className="p-3"><StatusBadge s={r.status} /></td>
                  <td className="p-3 text-xs text-zinc-500">{(r.created_at || '').slice(0,16).replace('T', ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function LogsPanel({ endpoint, label }) {
  const [items, setItems] = useState([]);
  useEffect(() => {
    axios.get(`${API}/api/super-admin/payments/${endpoint}`, { headers: TOKEN() })
      .then(({ data }) => setItems(data.items || []));
  }, [endpoint]);
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">{label}</h2>
      {items.length === 0 ? (
        <div className="glass-card p-12 text-center text-zinc-500">No log entries.</div>
      ) : (
        <div className="glass-card overflow-y-auto max-h-[70vh] divide-y divide-white/5">
          {items.map((r, i) => (
            <div key={i} className="p-3 text-sm">
              <div className="flex items-center gap-2 mb-1">
                <Badge className={`text-xs ${r.level === 'error' ? 'bg-rose-500/20 text-rose-300' : 'bg-zinc-700 text-zinc-300'}`}>{r.level || 'info'}</Badge>
                <span className="text-xs text-zinc-500">{(r.created_at || '').slice(0,19).replace('T', ' ')}</span>
                {r.action && <span className="text-violet-400 text-xs">{r.action}</span>}
                {r.provider && <span className="text-blue-400 text-xs">{r.provider}</span>}
              </div>
              <p className="text-zinc-300 font-mono text-xs">{r.message || r.event || r.action || JSON.stringify(r.metadata || r.payload || {}).slice(0, 200)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ============== REVENUE ANALYTICS ============== */
function RevenuePanel() {
  const [series, setSeries] = useState([]);
  useEffect(() => {
    axios.get(`${API}/api/super-admin/payments/revenue/timeseries?days=30`, { headers: TOKEN() })
      .then(({ data }) => setSeries(data.series || []));
  }, []);
  const max = useMemo(() => Math.max(1, ...series.map((s) => s.revenue || 0)), [series]);
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Revenue Analytics</h2>
      <div className="glass-card p-5">
        <h3 className="font-semibold mb-4">Revenue per day — last 30 days</h3>
        {series.length === 0 ? (
          <p className="text-sm text-zinc-500 py-12 text-center">No data yet.</p>
        ) : (
          <div className="flex items-end gap-1 h-48">
            {series.map((s, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
                <div className="w-full bg-gradient-to-t from-violet-500 to-emerald-400 rounded-t hover:from-violet-400 hover:to-emerald-300 transition-colors"
                     style={{ height: `${(s.revenue / max) * 100}%`, minHeight: '2px' }}
                     title={`${s.date}: $${s.revenue}`} />
                <span className="text-[9px] text-zinc-500 -rotate-45 origin-left">{s.date?.slice(5)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ============== GENERIC CRUD PANEL ============== */
function CRUDPanel({ endpoint, label, fields, largeFields = [] }) {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(() => Object.fromEntries(fields.map((f) => [f, ''])));
  const [open, setOpen] = useState(false);
  const load = async () => {
    const { data } = await axios.get(`${API}/api/super-admin/payments/${endpoint}`, { headers: TOKEN() });
    setItems(data.items || []);
  };
  useEffect(() => { load(); }, [endpoint]);
  const save = async () => {
    try {
      await axios.post(`${API}/api/super-admin/payments/${endpoint}`, form, { headers: TOKEN() });
      toast.success('Saved'); setOpen(false); setForm(Object.fromEntries(fields.map((f) => [f, ''])));
      load();
    } catch (e) { toast.error('Save failed'); }
  };
  const del = async (id) => {
    if (!window.confirm('Delete?')) return;
    await axios.delete(`${API}/api/super-admin/payments/${endpoint}/${id}`, { headers: TOKEN() });
    load();
  };
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">{label}</h2>
        <Button className="bg-violet-500 hover:bg-violet-600" onClick={() => setOpen(true)}>
          <Plus className="w-4 h-4 mr-2" /> New
        </Button>
      </div>
      {items.length === 0 ? (
        <div className="glass-card p-12 text-center text-zinc-500">No entries yet.</div>
      ) : (
        <div className="glass-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900/60 text-zinc-400">
              <tr>{fields.map((f) => <th key={f} className="text-left p-3 capitalize">{f.replace(/_/g, ' ')}</th>)}<th className="p-3"></th></tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id} className="border-t border-white/5">
                  {fields.map((f) => <td key={f} className="p-3 text-zinc-300">{String(r[f] ?? '—').slice(0, 80)}</td>)}
                  <td className="p-3 text-right">
                    <Button size="sm" variant="outline" className="border-rose-500/30 text-rose-300" onClick={() => del(r.id)}>
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50" onClick={() => setOpen(false)}>
          <div className="bg-zinc-950 border border-white/10 rounded-2xl max-w-lg w-full p-5 space-y-3" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-lg">New {label.slice(0, -1)}</h3>
            {fields.map((f) => (
              largeFields.includes(f) ? (
                <div key={f}>
                  <label className="text-xs text-zinc-400 mb-1 block capitalize">{f.replace(/_/g, ' ')}</label>
                  <Textarea value={form[f] || ''} onChange={(e) => setForm({ ...form, [f]: e.target.value })}
                    className="bg-zinc-900 border-white/10" rows={6} />
                </div>
              ) : (
                <Field key={f} label={f.replace(/_/g, ' ')} value={form[f] || ''}
                  onChange={(v) => setForm({ ...form, [f]: v })} />
              )
            ))}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" className="border-white/10" onClick={() => setOpen(false)}>Cancel</Button>
              <Button onClick={save} className="bg-violet-500 hover:bg-violet-600">Save</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ============== SETTINGS ============== */
function SettingsPanel() {
  const [s, setS] = useState(null);
  useEffect(() => {
    axios.get(`${API}/api/super-admin/payments/settings`, { headers: TOKEN() }).then(({ data }) => setS(data));
  }, []);
  const save = async (patch) => {
    const { data } = await axios.put(`${API}/api/super-admin/payments/settings`, patch, { headers: TOKEN() });
    setS(data); toast.success('Settings saved');
  };
  if (!s) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>;
  const togs = [
    ['fail_open', 'Grant access when payments unavailable (fail-open)'],
    ['auto_generate_invoice', 'Auto-generate invoice on successful payment'],
    ['auto_generate_receipt', 'Auto-generate receipt'],
    ['auto_activate_subscription', 'Auto-activate subscriptions'],
    ['auto_unlock_content', 'Auto-unlock paid content'],
    ['auto_send_email', 'Auto-send email notifications'],
    ['auto_verify_payment', 'Auto-verify payments via webhook'],
    ['email_notifications', 'Email notifications'],
    ['sms_notifications', 'SMS notifications'],
    ['admin_notifications', 'Admin notifications'],
  ];
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Payment Settings</h2>
      <div className="glass-card p-5 space-y-3">
        <Field label="Default Currency" value={s.default_currency} onChange={(v) => save({ default_currency: v })} />
        <Field label="Invoice Prefix" value={s.invoice_prefix} onChange={(v) => save({ invoice_prefix: v })} />
        <Field label="Receipt Prefix" value={s.receipt_prefix} onChange={(v) => save({ receipt_prefix: v })} />
        <Field label="Reference Prefix" value={s.reference_prefix} onChange={(v) => save({ reference_prefix: v })} />
        <div>
          <label className="text-xs text-zinc-400 mb-1 block">Service unavailable message (shown when no provider is configured)</label>
          <Textarea value={s.service_unavailable_message || ''}
            onChange={(e) => setS({ ...s, service_unavailable_message: e.target.value })}
            onBlur={() => save({ service_unavailable_message: s.service_unavailable_message })}
            className="bg-zinc-900 border-white/10" rows={3} />
        </div>
      </div>
      <div className="glass-card p-5 space-y-3">
        <h3 className="font-semibold">Automation</h3>
        {togs.map(([k, label]) => (
          <div key={k} className="flex items-center justify-between p-2 rounded-lg bg-zinc-900/40 border border-white/5">
            <span className="text-sm">{label}</span>
            <Switch checked={!!s[k]} onCheckedChange={(v) => save({ [k]: v })} data-testid={`setting-${k}`} />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ============== USER ACTIVITY ============== */
function ActivityPanel() {
  const [online, setOnline] = useState([]);
  const [external, setExternal] = useState({ anonymous_visitors: [], external_referred_users: [] });
  const [usage, setUsage] = useState([]);
  const load = useCallback(async () => {
    try {
      const [a, b, c] = await Promise.all([
        axios.get(`${API}/api/super-admin/activity/online`, { headers: TOKEN() }),
        axios.get(`${API}/api/super-admin/activity/external`, { headers: TOKEN() }),
        axios.get(`${API}/api/super-admin/activity/usage`, { headers: TOKEN() }),
      ]);
      setOnline(a.data.users || []);
      setExternal(b.data || { anonymous_visitors: [], external_referred_users: [] });
      setUsage(c.data.users || []);
    } catch (e) { toast.error('Failed to load activity'); }
  }, []);
  useEffect(() => { load(); const t = setInterval(load, 30000); return () => clearInterval(t); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">User Activity</h2>
        <Button variant="outline" className="border-white/10" onClick={load}>
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-card p-5">
          <p className="text-3xl font-bold text-emerald-400">{online.length}</p>
          <p className="text-xs text-zinc-500 mt-1">Online now (last 5 min)</p>
        </div>
        <div className="glass-card p-5">
          <p className="text-3xl font-bold text-blue-400">{external.anonymous_visitors.length}</p>
          <p className="text-xs text-zinc-500 mt-1">Anonymous visitors (24h)</p>
        </div>
        <div className="glass-card p-5">
          <p className="text-3xl font-bold text-violet-400">{external.external_referred_users.length}</p>
          <p className="text-xs text-zinc-500 mt-1">External-referred users (24h)</p>
        </div>
      </div>

      <div className="glass-card overflow-x-auto">
        <h3 className="p-4 font-semibold border-b border-white/5">Currently online</h3>
        {online.length === 0 ? (
          <p className="p-6 text-sm text-zinc-500 text-center">Nobody online right now.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-zinc-900/60 text-zinc-400">
              <tr><th className="text-left p-3">User</th><th className="text-left p-3">Role</th><th className="text-left p-3">Last seen</th><th className="text-left p-3">Time online</th></tr>
            </thead>
            <tbody>
              {online.map((u) => (
                <tr key={u.id} className="border-t border-white/5">
                  <td className="p-3"><p className="font-medium">{u.full_name || '—'}</p><p className="text-xs text-zinc-500">{u.email}</p></td>
                  <td className="p-3 capitalize">{(u.role || '').replace('_', ' ')}</td>
                  <td className="p-3 text-xs text-zinc-500"><Clock className="w-3 h-3 inline mr-1" />{(u.last_seen_at || '').slice(11,19)}</td>
                  <td className="p-3 text-xs">{((u.total_active_seconds || 0) / 3600).toFixed(2)} h total</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="glass-card overflow-x-auto">
        <h3 className="p-4 font-semibold border-b border-white/5">Hours spent on the platform</h3>
        <table className="w-full text-sm">
          <thead className="bg-zinc-900/60 text-zinc-400">
            <tr><th className="text-left p-3">User</th><th className="text-left p-3">Role</th><th className="text-left p-3">Total hours</th><th className="text-left p-3">Last seen</th></tr>
          </thead>
          <tbody>
            {usage.slice(0, 50).map((u) => (
              <tr key={u.id} className="border-t border-white/5">
                <td className="p-3"><p className="font-medium">{u.full_name || '—'}</p><p className="text-xs text-zinc-500">{u.email}</p></td>
                <td className="p-3 capitalize">{(u.role || '').replace('_', ' ')}</td>
                <td className="p-3 font-mono text-violet-300">{u.total_hours} h</td>
                <td className="p-3 text-xs text-zinc-500">{(u.last_seen_at || '—').slice(0,16).replace('T',' ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card overflow-x-auto">
          <h3 className="p-4 font-semibold border-b border-white/5">Anonymous visitors (24h)</h3>
          {external.anonymous_visitors.length === 0 ? (
            <p className="p-6 text-sm text-zinc-500 text-center">No anonymous visits yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-zinc-900/60 text-zinc-400">
                <tr><th className="text-left p-3">IP</th><th className="text-left p-3">Path</th><th className="text-left p-3">Hits</th><th className="text-left p-3">Last</th></tr>
              </thead>
              <tbody>
                {external.anonymous_visitors.slice(0, 30).map((v, i) => (
                  <tr key={i} className="border-t border-white/5">
                    <td className="p-3 font-mono text-xs">{v._id?.ip || v.ip}</td>
                    <td className="p-3 text-xs">{v._id?.path || v.path}</td>
                    <td className="p-3"><Badge className="bg-blue-500/20 text-blue-300">{v.hits}</Badge></td>
                    <td className="p-3 text-xs text-zinc-500">{(v.last || '').slice(11,19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div className="glass-card overflow-x-auto">
          <h3 className="p-4 font-semibold border-b border-white/5">External-referred users</h3>
          {external.external_referred_users.length === 0 ? (
            <p className="p-6 text-sm text-zinc-500 text-center">No external-referred users yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-zinc-900/60 text-zinc-400">
                <tr><th className="text-left p-3">User</th><th className="text-left p-3">Referrer</th></tr>
              </thead>
              <tbody>
                {external.external_referred_users.map((u, i) => (
                  <tr key={i} className="border-t border-white/5">
                    <td className="p-3"><p className="font-medium">{u.full_name || u.email}</p></td>
                    <td className="p-3 text-xs text-violet-300 truncate max-w-[200px]">
                      <ExternalLink className="w-3 h-3 inline mr-1" />{u.last_referrer}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

/* ============== SECURITY ============== */
function SecurityPanel() {
  const items = [
    'Encrypted API keys (Fernet at rest)',
    'Webhook signature verification (HMAC-SHA256)',
    'Role-based permissions (super_admin only)',
    'Bearer JWT authentication on every endpoint',
    'Audit logging for every provider/settings change',
    'HTTPS-only enforced by Kubernetes ingress',
    'No live credentials in source — env vars only',
    'Soft-delete with deleted_at timestamps',
    'Fail-open mode toggle (controlled by Settings)',
  ];
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Payment Security</h2>
      <div className="glass-card p-5 space-y-2">
        {items.map((it) => (
          <div key={it} className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="text-zinc-300">{it}</span>
          </div>
        ))}
      </div>
      <div className="glass-card p-5 border-amber-500/30">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-200">Pre-go-live checklist</h3>
            <ul className="text-sm text-zinc-300 mt-2 space-y-1 list-disc list-inside">
              <li>Add Paynow Integration ID and Integration Key</li>
              <li>Set Result URL and Return URL to production paths</li>
              <li>Click &quot;Test Connection&quot; — must return healthy</li>
              <li>Switch environment to <strong>production</strong></li>
              <li>Toggle the Paynow provider <strong>enabled</strong></li>
              <li>Turn off &quot;fail-open&quot; in Settings once payments are live</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============== API CONFIGURATION ============== */
function ApiConfigPanel() {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    axios.get(`${API}/api/super-admin/payments/providers`, { headers: TOKEN() })
      .then(({ data }) => setProviders(data.providers || []))
      .catch(() => toast.error('Failed to load API config'))
      .finally(() => setLoading(false));
  }, []);
  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>;
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">API Configuration</h2>
      <p className="text-sm text-zinc-400">Encrypted API credentials and webhook endpoints. Use Providers page to edit secrets — this view is read-only summary.</p>
      <div className="glass-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900/60 text-zinc-400">
            <tr>
              <th className="text-left p-3">Provider</th>
              <th className="text-left p-3">Environment</th>
              <th className="text-left p-3">Webhook URL</th>
              <th className="text-left p-3">Webhook Secret</th>
              <th className="text-left p-3">API Key</th>
              <th className="text-left p-3">Health</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.slug} className="border-t border-white/5" data-testid={`apicfg-row-${p.slug}`}>
                <td className="p-3 font-medium">{p.display_name}</td>
                <td className="p-3 capitalize">{p.environment}</td>
                <td className="p-3 font-mono text-xs text-violet-300">
                  {`${window.location.origin}/api/payments/webhook/${p.slug}`}
                </td>
                <td className="p-3 font-mono text-xs">{p.webhook_secret_preview || '— not set —'}</td>
                <td className="p-3 font-mono text-xs">{p.integration_key_preview || p.api_key_preview || p.secret_key_preview || '— not set —'}</td>
                <td className="p-3">
                  {p.health_status === 'healthy'
                    ? <Badge className="bg-emerald-500/20 text-emerald-300">healthy</Badge>
                    : p.health_status === 'error'
                      ? <Badge className="bg-rose-500/20 text-rose-300">error</Badge>
                      : <Badge className="bg-zinc-700 text-zinc-300">untested</Badge>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ============== NOTIFICATION SETTINGS ============== */
function NotificationSettingsPanel() {
  const [s, setS] = useState(null);
  useEffect(() => {
    axios.get(`${API}/api/super-admin/payments/settings`, { headers: TOKEN() })
      .then(({ data }) => setS(data))
      .catch(() => toast.error('Failed to load notification settings'));
  }, []);
  const save = async (patch) => {
    const { data } = await axios.put(`${API}/api/super-admin/payments/settings`, patch, { headers: TOKEN() });
    setS(data);
    toast.success('Notification setting saved');
  };
  if (!s) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>;
  const toggles = [
    ['email_notifications', 'Send customer emails (payment initiated / successful / failed)'],
    ['sms_notifications', 'Send SMS notifications (where supported)'],
    ['admin_notifications', 'Notify administrators on key events'],
    ['auto_send_email', 'Auto-send invoice & receipt emails'],
  ];
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Notification Settings</h2>
      <div className="glass-card p-5 space-y-3">
        {toggles.map(([k, label]) => (
          <div key={k} className="flex items-center justify-between p-2 rounded-lg bg-zinc-900/40 border border-white/5">
            <span className="text-sm">{label}</span>
            <Switch checked={!!s[k]} onCheckedChange={(v) => save({ [k]: v })} data-testid={`notif-${k}`} />
          </div>
        ))}
      </div>
      <div className="glass-card p-5 space-y-2">
        <h3 className="font-semibold">Email channel</h3>
        <p className="text-sm text-zinc-400">
          Transactional emails are sent via the platform-wide Resend HTTP integration.
          Manage templates in <span className="text-violet-300">Email Templates</span>.
        </p>
      </div>
    </div>
  );
}

