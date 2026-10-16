/* Public Org Join Page — /join/:slug
   Anyone (no auth) can view the org landing and sign up. */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Loader2, CheckCircle2, Shield, Copy, QrCode, BookOpen, Users, Globe } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';

const API = process.env.REACT_APP_BACKEND_URL;

export default function OrgJoinPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [landing, setLanding] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [form, setForm] = useState({ email: '', password: '', full_name: '', phone: '' });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    axios.get(`${API}/api/public/org/${slug}`)
      .then(({ data }) => setLanding(data))
      .catch((err) => {
        setNotFound(true);
        toast.error(err.response?.data?.detail || 'Organization not found');
      })
      .finally(() => setLoading(false));
  }, [slug]);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password || !form.full_name) {
      toast.error('Please fill in all required fields');
      return;
    }
    if (form.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await axios.post(`${API}/api/public/org/${slug}/signup`, form);
      setResult(data);
      if (data.status === 'active' && data.access_token) {
        localStorage.setItem('cognify_token', data.access_token);
        localStorage.setItem('cognify_user', JSON.stringify(data.user));
        toast.success('Welcome — signed in!');
        setTimeout(() => navigate('/dashboard'), 1500);
      } else {
        toast.success(data.message || 'Application submitted');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Signup failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-zinc-950">
      <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
    </div>;
  }
  if (notFound) {
    return <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-300 p-6">
      <div className="max-w-md text-center space-y-4">
        <h1 className="text-2xl font-semibold">Organization not found</h1>
        <p className="text-zinc-400">The join link <code className="text-violet-300">/join/{slug}</code> is invalid or has been disabled.</p>
        <Link to="/"><Button variant="outline" data-testid="join-back-home">Back to home</Button></Link>
      </div>
    </div>;
  }

  const { org, public_courses = [], member_count, require_approval } = landing;

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-950 to-violet-950/30">
      <div className="max-w-6xl mx-auto px-4 py-10">
        {/* Hero */}
        <div className="flex items-start gap-6 mb-10">
          {org.logo_url ? (
            <img src={org.logo_url} alt={org.name} className="w-24 h-24 rounded-2xl object-cover border border-white/10" />
          ) : (
            <div className="w-24 h-24 rounded-2xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center">
              <Users className="w-10 h-10 text-violet-300" />
            </div>
          )}
          <div className="flex-1">
            <h1 className="text-4xl sm:text-5xl font-semibold text-white leading-tight" data-testid="join-org-name">{org.name}</h1>
            <div className="mt-3 flex flex-wrap gap-2 text-sm">
              {org.country && <Badge className="bg-zinc-800 text-zinc-300"><Globe className="w-3 h-3 mr-1"/>{org.country}</Badge>}
              {org.org_type && <Badge className="bg-violet-500/20 text-violet-300 capitalize">{org.org_type}</Badge>}
              <Badge className="bg-emerald-500/20 text-emerald-300"><Users className="w-3 h-3 mr-1"/>{member_count} members</Badge>
              <Badge className="bg-blue-500/20 text-blue-300"><BookOpen className="w-3 h-3 mr-1"/>{public_courses.length} public courses</Badge>
            </div>
            {org.description && <p className="mt-4 text-zinc-300 max-w-3xl leading-relaxed">{org.description}</p>}
          </div>
        </div>

        <div className="grid lg:grid-cols-5 gap-8">
          {/* Signup form */}
          <div className="lg:col-span-2">
            <Card className="bg-zinc-900/60 border-white/10 backdrop-blur">
              <CardContent className="p-6">
                {result?.status === 'pending' ? (
                  <div className="text-center space-y-3 py-4">
                    <CheckCircle2 className="w-14 h-14 mx-auto text-emerald-400" />
                    <h2 className="text-xl font-semibold text-white">Application received</h2>
                    <p className="text-zinc-400">{result.message}</p>
                    <Link to="/login"><Button variant="outline" className="mt-4" data-testid="join-goto-login">Go to login</Button></Link>
                  </div>
                ) : (
                  <>
                    <h2 className="text-xl font-semibold text-white mb-1">Join {org.name}</h2>
                    <p className="text-sm text-zinc-400 mb-6">
                      {require_approval
                        ? 'Sign up below — an organization admin will review your application.'
                        : 'Sign up below and start learning immediately.'}
                    </p>
                    <form onSubmit={submit} className="space-y-4">
                      <div>
                        <Label className="text-zinc-300">Full name *</Label>
                        <Input required data-testid="join-full-name"
                               value={form.full_name}
                               onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                               placeholder="Jane Doe"
                               className="bg-zinc-950 border-white/10 mt-1" />
                      </div>
                      <div>
                        <Label className="text-zinc-300">Email *</Label>
                        <Input required type="email" data-testid="join-email"
                               value={form.email}
                               onChange={(e) => setForm({ ...form, email: e.target.value })}
                               placeholder="you@example.com"
                               className="bg-zinc-950 border-white/10 mt-1" />
                      </div>
                      <div>
                        <Label className="text-zinc-300">Password *</Label>
                        <Input required type="password" data-testid="join-password"
                               value={form.password}
                               onChange={(e) => setForm({ ...form, password: e.target.value })}
                               placeholder="8+ characters"
                               className="bg-zinc-950 border-white/10 mt-1" />
                      </div>
                      <div>
                        <Label className="text-zinc-300">Phone (optional)</Label>
                        <Input data-testid="join-phone"
                               value={form.phone}
                               onChange={(e) => setForm({ ...form, phone: e.target.value })}
                               placeholder="+263 …"
                               className="bg-zinc-950 border-white/10 mt-1" />
                      </div>
                      <Button type="submit" disabled={submitting}
                              data-testid="join-submit"
                              className="w-full bg-violet-600 hover:bg-violet-500">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> :
                          require_approval ? 'Apply to join' : 'Create account'}
                      </Button>
                      <div className="text-center text-xs text-zinc-500">
                        Already a member? <Link to="/login" className="text-violet-400 hover:text-violet-300">Log in</Link>
                      </div>
                    </form>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Public courses */}
          <div className="lg:col-span-3">
            <h3 className="text-lg font-semibold text-white mb-4">Public Courses</h3>
            {public_courses.length === 0 ? (
              <div className="glass-card p-8 text-center text-zinc-400">
                <Shield className="w-10 h-10 mx-auto mb-3 opacity-60" />
                <p>No public courses yet. Sign up to see everything this organization offers.</p>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {public_courses.map((c) => (
                  <Card key={c.id} data-testid={`join-course-${c.id}`}
                        className="bg-zinc-900/60 border-white/10 hover:border-violet-500/40 transition">
                    <CardContent className="p-4">
                      {c.cover_image && (
                        <img src={c.cover_image} alt={c.title}
                             className="w-full h-32 object-cover rounded mb-3" />
                      )}
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="font-semibold text-white line-clamp-2 flex-1">{c.title}</h4>
                        {c.is_free ? <Badge className="bg-emerald-500/20 text-emerald-300 shrink-0">Free</Badge>
                          : (c.price ? <Badge className="bg-amber-500/20 text-amber-300 shrink-0">{c.currency || '$'}{c.price}</Badge> : null)}
                      </div>
                      {c.description && <p className="text-xs text-zinc-400 mt-2 line-clamp-3">{c.description}</p>}
                      <div className="mt-3 flex flex-wrap gap-1 text-xs text-zinc-500">
                        {c.subject && <span>{c.subject}</span>}
                        {c.grade_level && <span>· {c.grade_level}</span>}
                        {c.duration_hours && <span>· {c.duration_hours}h</span>}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
