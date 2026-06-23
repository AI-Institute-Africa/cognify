import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import {
  Users, Building2, BarChart3, FileUp, Search, Loader2, Shield,
  UserCheck, UserX, Power, RefreshCw, Upload, Trash2, Headphones, Video,
  Globe, Menu, Eye,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;
const TOKEN_HEADER = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

export default function SuperAdminDashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 1024);
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return (
    <div className="min-h-screen bg-[#09090B] text-zinc-100">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} isMobile={isMobile} />
      <main className={`min-h-screen ${isMobile ? '' : 'ml-64'}`}>
        <header className="border-b border-white/5 sticky top-0 z-20 bg-[#09090B]/90 backdrop-blur">
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isMobile && (
                <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-white/5" data-testid="open-sidebar-btn">
                  <Menu className="w-5 h-5" />
                </button>
              )}
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-rose-500 flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold">Super Admin Console</h1>
                <p className="text-xs text-zinc-500">System-wide controls · bypass org isolation</p>
              </div>
            </div>
            <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30">Top-level access</Badge>
          </div>
        </header>

        <div className="px-6 py-8 max-w-7xl mx-auto">
          <Tabs defaultValue="analytics" className="w-full">
            <TabsList className="bg-zinc-900 border border-white/10 mb-6">
              <TabsTrigger value="analytics" data-testid="sa-tab-analytics">
                <BarChart3 className="w-4 h-4 mr-2" /> Analytics
              </TabsTrigger>
              <TabsTrigger value="users" data-testid="sa-tab-users">
                <Users className="w-4 h-4 mr-2" /> Users
              </TabsTrigger>
              <TabsTrigger value="orgs" data-testid="sa-tab-orgs">
                <Building2 className="w-4 h-4 mr-2" /> Organizations
              </TabsTrigger>
              <TabsTrigger value="public" data-testid="sa-tab-public">
                <Globe className="w-4 h-4 mr-2" /> Public Content
              </TabsTrigger>
            </TabsList>

            <TabsContent value="analytics"><AnalyticsTab /></TabsContent>
            <TabsContent value="users"><UsersTab /></TabsContent>
            <TabsContent value="orgs"><OrgsTab /></TabsContent>
            <TabsContent value="public"><PublicContentTab /></TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}

/* ---------------- Analytics ---------------- */
function AnalyticsTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/api/super-admin/analytics`, { headers: TOKEN_HEADER() });
      setData(data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load analytics');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>;
  if (!data) return null;

  const s = data.summary || {};
  const cards = [
    { label: 'Total Users', value: s.total_users, sub: `${s.active_users} active`, icon: Users, color: 'from-blue-500 to-cyan-500' },
    { label: 'Organizations', value: s.total_organizations, sub: `${s.active_organizations} active`, icon: Building2, color: 'from-violet-500 to-fuchsia-500' },
    { label: 'Courses', value: s.total_courses, sub: 'standard + custom', icon: FileUp, color: 'from-emerald-500 to-teal-500' },
    { label: 'Premade Docs', value: s.total_premade_docs, sub: 'library size', icon: FileUp, color: 'from-amber-500 to-orange-500' },
    { label: 'Public Content', value: s.total_public_content, sub: 'summit + public', icon: Globe, color: 'from-rose-500 to-pink-500' },
    { label: 'Quiz Attempts', value: s.total_quiz_attempts, sub: `${s.total_assignments} assignments`, icon: BarChart3, color: 'from-indigo-500 to-purple-500' },
  ];

  return (
    <div className="space-y-8" data-testid="sa-analytics-panel">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">System overview</h2>
          <p className="text-sm text-zinc-500">{s.new_signups_last_7d || 0} new signups in the last 7 days</p>
        </div>
        <Button variant="outline" className="border-white/10" onClick={load} data-testid="sa-refresh-analytics">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <div key={c.label} className="glass-card p-5 hover:border-white/20 transition-colors">
              <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${c.color} flex items-center justify-center`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <p className="text-xs text-zinc-500">{c.sub}</p>
              </div>
              <p className="text-3xl font-bold">{c.value ?? 0}</p>
              <p className="text-sm text-zinc-400 mt-1">{c.label}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="font-semibold mb-4">Users by role</h3>
          <div className="space-y-2">
            {Object.entries(data.users_by_role || {}).map(([role, count]) => (
              <div key={role} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-white/5">
                <span className="capitalize text-sm">{role.replace('_', ' ')}</span>
                <Badge className="bg-violet-500/20 text-violet-300">{count}</Badge>
              </div>
            ))}
          </div>
        </div>
        <div className="glass-card p-6">
          <h3 className="font-semibold mb-4">Top organizations by users</h3>
          {(data.top_organizations || []).length === 0 ? (
            <p className="text-sm text-zinc-500">No organizations yet.</p>
          ) : (
            <div className="space-y-2">
              {data.top_organizations.map((o, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-white/5">
                  <span className="text-sm">{o.name}</span>
                  <Badge className="bg-blue-500/20 text-blue-300">{o.users} users</Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Users ---------------- */
function UsersTab() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [role, setRole] = useState('');
  const [activeFilter, setActiveFilter] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (q) params.q = q;
      if (role) params.role = role;
      if (activeFilter !== '') params.is_active = activeFilter === 'active';
      const { data } = await axios.get(`${API}/api/super-admin/users`, { params, headers: TOKEN_HEADER() });
      setUsers(data.users || []);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load users');
    } finally { setLoading(false); }
  }, [q, role, activeFilter]);

  useEffect(() => { load(); }, [load]);

  const toggleActive = async (u) => {
    const isActive = u.is_active !== false;
    const action = isActive ? 'deactivate' : 'reactivate';
    try {
      await axios.post(`${API}/api/super-admin/users/${u.id}/${action}`, {}, { headers: TOKEN_HEADER() });
      toast.success(`User ${action}d`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || `Failed to ${action} user`); }
  };

  return (
    <div className="space-y-4" data-testid="sa-users-panel">
      <div className="flex flex-wrap gap-2 items-center">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && load()}
            placeholder="Search email or name…" className="pl-9 bg-zinc-900 border-white/10"
            data-testid="sa-user-search" />
        </div>
        <select value={role} onChange={(e) => setRole(e.target.value)}
          className="bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-sm" data-testid="sa-role-filter">
          <option value="">All roles</option>
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
          <option value="admin">Admin</option>
          <option value="org_admin">Org Admin</option>
          <option value="parent">Parent</option>
          <option value="super_admin">Super Admin</option>
        </select>
        <select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)}
          className="bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-sm" data-testid="sa-active-filter">
          <option value="">All</option>
          <option value="active">Active</option>
          <option value="inactive">Deactivated</option>
        </select>
        <Button onClick={load} variant="outline" className="border-white/10" data-testid="sa-apply-filters">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>
        ) : users.length === 0 ? (
          <div className="text-center py-12 text-zinc-500">No users found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900/60 text-zinc-400">
                <tr>
                  <th className="text-left p-3 font-medium">User</th>
                  <th className="text-left p-3 font-medium">Role</th>
                  <th className="text-left p-3 font-medium">Org</th>
                  <th className="text-left p-3 font-medium">Status</th>
                  <th className="text-right p-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const active = u.is_active !== false;
                  return (
                    <tr key={u.id} className="border-t border-white/5 hover:bg-white/[0.02]" data-testid={`sa-user-row-${u.id}`}>
                      <td className="p-3">
                        <p className="font-medium">{u.full_name || '—'}</p>
                        <p className="text-xs text-zinc-500">{u.email}</p>
                      </td>
                      <td className="p-3"><Badge className="bg-zinc-800 text-zinc-200 capitalize">{(u.role || '').replace('_', ' ')}</Badge></td>
                      <td className="p-3 text-xs text-zinc-400">{u.organization_id ? u.organization_id.slice(0, 8) + '…' : '—'}</td>
                      <td className="p-3">
                        {active ? (
                          <Badge className="bg-emerald-500/20 text-emerald-300"><UserCheck className="w-3 h-3 mr-1" />Active</Badge>
                        ) : (
                          <Badge className="bg-rose-500/20 text-rose-300"><UserX className="w-3 h-3 mr-1" />Deactivated</Badge>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        <Button size="sm" variant="outline" className="border-white/10"
                          onClick={() => toggleActive(u)} data-testid={`sa-toggle-user-${u.id}`}>
                          <Power className="w-3 h-3 mr-1" /> {active ? 'Deactivate' : 'Reactivate'}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------------- Organizations ---------------- */
function OrgsTab() {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/api/super-admin/organizations`, { headers: TOKEN_HEADER() });
      setOrgs(data.organizations || []);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to load orgs'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleOrg = async (org) => {
    const isActive = org.is_active !== false;
    const action = isActive ? 'deactivate' : 'reactivate';
    if (isActive && !window.confirm(`Deactivate ${org.name}? All its users will also be deactivated.`)) return;
    try {
      await axios.post(`${API}/api/super-admin/organizations/${org.id}/${action}`, {}, { headers: TOKEN_HEADER() });
      toast.success(`Organization ${action}d`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || `Failed to ${action} org`); }
  };

  return (
    <div className="space-y-4" data-testid="sa-orgs-panel">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Organizations</h2>
        <Button onClick={load} variant="outline" className="border-white/10" data-testid="sa-refresh-orgs">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>
      ) : orgs.length === 0 ? (
        <div className="text-center py-12 text-zinc-500 glass-card">No organizations registered yet.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {orgs.map((org) => {
            const active = org.is_active !== false;
            return (
              <div key={org.id} className="glass-card p-5" data-testid={`sa-org-card-${org.id}`}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-lg">{org.name}</h3>
                    <p className="text-xs text-zinc-500">/{org.slug || org.id?.slice(0, 8)}</p>
                  </div>
                  {active ? <Badge className="bg-emerald-500/20 text-emerald-300">Active</Badge>
                    : <Badge className="bg-rose-500/20 text-rose-300">Deactivated</Badge>}
                </div>
                <div className="grid grid-cols-3 gap-2 mb-4 text-center">
                  <div className="p-2 rounded-lg bg-zinc-900 border border-white/5">
                    <p className="text-xl font-bold">{org.users_count || 0}</p>
                    <p className="text-xs text-zinc-500">Users</p>
                  </div>
                  <div className="p-2 rounded-lg bg-zinc-900 border border-white/5">
                    <p className="text-xl font-bold">{org.active_users || 0}</p>
                    <p className="text-xs text-zinc-500">Active</p>
                  </div>
                  <div className="p-2 rounded-lg bg-zinc-900 border border-white/5">
                    <p className="text-xl font-bold">{org.courses_count || 0}</p>
                    <p className="text-xs text-zinc-500">Courses</p>
                  </div>
                </div>
                <Button size="sm" variant="outline" className="w-full border-white/10"
                  onClick={() => toggleOrg(org)} data-testid={`sa-toggle-org-${org.id}`}>
                  <Power className="w-3 h-3 mr-2" /> {active ? 'Deactivate' : 'Reactivate'}
                </Button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ---------------- Public Content ---------------- */
function PublicContentTab() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [working, setWorking] = useState({}); // {docId: 'audio'|'video'|'delete'}
  const mediaInputRefs = useRef({}); // {docId-kind: HTMLInputElement}

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/api/public/content`);
      setDocs(data.documents || []);
    } catch (e) { toast.error('Failed to load public content'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onDelete = async (id) => {
    if (!window.confirm('Soft-delete this public content?')) return;
    setWorking((w) => ({ ...w, [id]: 'delete' }));
    try {
      await axios.delete(`${API}/api/super-admin/public-content/${id}`, { headers: TOKEN_HEADER() });
      toast.success('Removed');
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to delete'); }
    finally { setWorking((w) => { const n = { ...w }; delete n[id]; return n; }); }
  };

  const generate = async (id, kind) => {
    setWorking((w) => ({ ...w, [id]: kind }));
    try {
      const { data } = await axios.post(`${API}/api/super-admin/public-content/${id}/generate-${kind}`, {}, { headers: TOKEN_HEADER() });
      toast.success(`${kind === 'audio' ? 'Audio' : 'Video'} generation started`);
      const jobId = data.job_id;
      const poll = async () => {
        try {
          const { data: j } = await axios.get(`${API}/api/super-admin/public-content/job/${jobId}`, { headers: TOKEN_HEADER() });
          if (j.status === 'completed') {
            toast.success(`${kind} ready!`);
            setWorking((w) => { const n = { ...w }; delete n[id]; return n; });
            load();
          } else if (j.status === 'failed') {
            toast.error(j.error || `${kind} generation failed`);
            setWorking((w) => { const n = { ...w }; delete n[id]; return n; });
          } else {
            setTimeout(poll, 4000);
          }
        } catch (_) {
          setWorking((w) => { const n = { ...w }; delete n[id]; return n; });
        }
      };
      setTimeout(poll, 4000);
    } catch (e) {
      toast.error(e.response?.data?.detail || `Failed to start ${kind} generation`);
      setWorking((w) => { const n = { ...w }; delete n[id]; return n; });
    }
  };

  const uploadMedia = async (id, kind, file) => {
    if (!file) return;
    setWorking((w) => ({ ...w, [id]: `upload-${kind}` }));
    try {
      const fd = new FormData();
      fd.append('file', file);
      await axios.post(`${API}/api/super-admin/public-content/${id}/upload-${kind}`, fd, {
        headers: { ...TOKEN_HEADER(), 'Content-Type': 'multipart/form-data' },
      });
      toast.success(`${kind === 'audio' ? 'Audio' : 'Video'} attached`);
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || `Failed to attach ${kind}`);
    } finally {
      setWorking((w) => { const n = { ...w }; delete n[id]; return n; });
    }
  };

  return (
    <div className="space-y-4" data-testid="sa-public-panel">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Public content library</h2>
          <p className="text-xs text-zinc-500">Manage summit presentations and resources shown on the /public page</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
            <DialogTrigger asChild>
              <Button className="bg-violet-500 hover:bg-violet-600" data-testid="sa-upload-open">
                <Upload className="w-4 h-4 mr-2" /> Upload
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-950 border-white/10 text-zinc-100 max-w-lg">
              <DialogHeader><DialogTitle>Upload public content</DialogTitle></DialogHeader>
              <UploadForm onDone={() => { setUploadOpen(false); load(); }} />
            </DialogContent>
          </Dialog>
          <Button variant="outline" className="border-white/10" onClick={load} data-testid="sa-refresh-public">
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>
      ) : docs.length === 0 ? (
        <div className="text-center py-12 glass-card text-zinc-500">No public content yet. Upload your first summit presentation.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {docs.map((d) => {
            const busy = working[d.id];
            return (
              <div key={d.id} className="glass-card p-5" data-testid={`sa-public-card-${d.id}`}>
                <div className="flex items-start justify-between mb-2">
                  <Badge className="bg-violet-500/20 text-violet-300">{d.category}</Badge>
                  <div className="flex gap-1">
                    {d.has_audio && <Badge className="bg-emerald-500/20 text-emerald-300"><Headphones className="w-3 h-3 mr-1" />Audio</Badge>}
                    {d.has_video && <Badge className="bg-blue-500/20 text-blue-300"><Video className="w-3 h-3 mr-1" />Video</Badge>}
                  </div>
                </div>
                <h3 className="font-semibold mb-1">{d.title}</h3>
                {d.description && <p className="text-xs text-zinc-400 line-clamp-2 mb-3">{d.description}</p>}
                <p className="text-xs text-zinc-500 mb-4">{d.filename} · {Math.round((d.file_size || 0) / 1024)} KB</p>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" variant="outline" className="border-white/10"
                    onClick={() => window.open(`/public/${d.id}`, '_blank')} data-testid={`sa-view-${d.id}`}>
                    <Eye className="w-3 h-3 mr-1" /> View
                  </Button>
                  <Button size="sm" variant="outline" className="border-white/10"
                    disabled={!!busy} onClick={() => generate(d.id, 'audio')} data-testid={`sa-gen-audio-${d.id}`}
                    title="AI-generate audio narration">
                    {busy === 'audio' ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Headphones className="w-3 h-3 mr-1" />}
                    AI Audio
                  </Button>
                  <Button size="sm" variant="outline" className="border-white/10"
                    disabled={!!busy} onClick={() => generate(d.id, 'video')} data-testid={`sa-gen-video-${d.id}`}
                    title="AI-generate explainer video">
                    {busy === 'video' ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Video className="w-3 h-3 mr-1" />}
                    AI Video
                  </Button>
                  <Button size="sm" variant="outline" className="border-emerald-500/30 text-emerald-300"
                    disabled={!!busy}
                    onClick={() => mediaInputRefs.current[`${d.id}-audio`]?.click()}
                    data-testid={`sa-upload-audio-${d.id}`}
                    title="Upload pre-recorded audio file">
                    {busy === 'upload-audio' ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Upload className="w-3 h-3 mr-1" />}
                    Audio file
                  </Button>
                  <input
                    type="file" accept=".mp3,.wav,.m4a,.aac,.ogg" hidden
                    ref={(el) => { mediaInputRefs.current[`${d.id}-audio`] = el; }}
                    onChange={(e) => { uploadMedia(d.id, 'audio', e.target.files?.[0]); e.target.value = ''; }}
                  />
                  <Button size="sm" variant="outline" className="border-blue-500/30 text-blue-300"
                    disabled={!!busy}
                    onClick={() => mediaInputRefs.current[`${d.id}-video`]?.click()}
                    data-testid={`sa-upload-video-${d.id}`}
                    title="Upload pre-recorded video file">
                    {busy === 'upload-video' ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Upload className="w-3 h-3 mr-1" />}
                    Video file
                  </Button>
                  <input
                    type="file" accept=".mp4,.mov,.webm,.mkv" hidden
                    ref={(el) => { mediaInputRefs.current[`${d.id}-video`] = el; }}
                    onChange={(e) => { uploadMedia(d.id, 'video', e.target.files?.[0]); e.target.value = ''; }}
                  />
                  <Button size="sm" variant="outline" className="border-rose-500/20 text-rose-300"
                    disabled={!!busy} onClick={() => onDelete(d.id)} data-testid={`sa-delete-${d.id}`}>
                    {busy === 'delete' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function UploadForm({ onDone }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('summit');
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const fileRef = useRef(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!file || !title) { toast.error('Title and file are required'); return; }
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('title', title);
      fd.append('description', description || '');
      fd.append('category', category);
      fd.append('is_summit', category === 'summit' ? 'true' : 'false');
      await axios.post(`${API}/api/super-admin/public-content/upload`, fd, {
        headers: { ...TOKEN_HEADER(), 'Content-Type': 'multipart/form-data' },
      });
      toast.success('Uploaded');
      onDone();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally { setSubmitting(false); }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <div>
        <label className="text-xs text-zinc-400 mb-1 block">Title</label>
        <Input value={title} onChange={(e) => setTitle(e.target.value)} className="bg-zinc-900 border-white/10"
          required data-testid="sa-upload-title" />
      </div>
      <div>
        <label className="text-xs text-zinc-400 mb-1 block">Description</label>
        <Textarea value={description} onChange={(e) => setDescription(e.target.value)}
          className="bg-zinc-900 border-white/10" rows={3} data-testid="sa-upload-desc" />
      </div>
      <div>
        <label className="text-xs text-zinc-400 mb-1 block">Category</label>
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="w-full bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-sm" data-testid="sa-upload-category">
          <option value="summit">Summit Presentation</option>
          <option value="public">Public Resource</option>
          <option value="keynote">Keynote</option>
          <option value="workshop">Workshop</option>
        </select>
      </div>
      <div>
        <label className="text-xs text-zinc-400 mb-1 block">File (PDF/DOCX/PPT/PPTX/MP4/MP3 — up to 200 MB)</label>
        <input
          ref={fileRef}
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="w-full text-sm text-zinc-300 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-violet-500 file:text-white"
          accept=".pdf,.docx,.doc,.ppt,.pptx,.mp4,.mp3,.wav,.m4a,.png,.jpg,.jpeg"
          required
          data-testid="sa-upload-file"
        />
      </div>
      <DialogFooter>
        <Button type="submit" disabled={submitting} className="bg-violet-500 hover:bg-violet-600" data-testid="sa-upload-submit">
          {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
          Upload
        </Button>
      </DialogFooter>
    </form>
  );
}
