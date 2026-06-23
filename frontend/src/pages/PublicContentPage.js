import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  Sparkles, Search, FileText, Headphones, Video, Eye, Lock,
  Calendar, BookOpen, ArrowRight, LogIn
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PublicContentPage() {
  const navigate = useNavigate();
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => { load(); }, [selectedCategory]);

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedCategory !== 'all') params.category = selectedCategory;
      if (searchQuery) params.q = searchQuery;
      const { data } = await axios.get(`${API}/api/public/content`, { params });
      setDocs(data.documents || []);
    } catch (e) {
      toast.error('Failed to load public content');
    } finally {
      setLoading(false);
    }
  };

  const requireLoginForMedia = (kind) => {
    toast.info(`Sign in to access the ${kind} version`, { duration: 3000 });
    navigate('/login', { state: { redirectTo: window.location.pathname } });
  };

  const categories = [
    { id: 'all', label: 'All' },
    { id: 'summit', label: 'Summit Presentations' },
    { id: 'public', label: 'Public Resources' },
    { id: 'keynote', label: 'Keynotes' },
    { id: 'workshop', label: 'Workshops' },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-zinc-100">
      {/* Top nav */}
      <nav className="border-b border-white/5 backdrop-blur-xl bg-zinc-950/80 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg">Cognify</span>
          </Link>
          <div className="flex items-center gap-3">
            <Button variant="outline" className="border-white/10" onClick={() => navigate('/login')} data-testid="public-login-btn">
              <LogIn className="w-4 h-4 mr-2" />
              Sign in
            </Button>
            <Button className="bg-violet-500 hover:bg-violet-600" onClick={() => navigate('/register')}>
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 py-16 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto">
          <Badge className="bg-violet-500/20 text-violet-300 mb-4">Public Knowledge Hub</Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4 leading-tight">
            Summit talks & public<br />resources for everyone
          </h1>
          <p className="text-zinc-400 text-lg">
            Browse and read summit presentations, keynotes, and public resources — completely free.
            Want to listen to the audio version or watch the talk? Just sign in.
          </p>
        </div>

        {/* Search + filter */}
        <div className="mt-10 max-w-4xl mx-auto space-y-4">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && load()}
              placeholder="Search summit presentations, keynotes…"
              className="pl-12 h-12 bg-zinc-900 border-white/10"
              data-testid="public-search-input"
            />
          </div>
          <div className="flex flex-wrap gap-2 justify-center">
            {categories.map((c) => (
              <Button
                key={c.id}
                size="sm"
                variant={selectedCategory === c.id ? 'default' : 'outline'}
                onClick={() => setSelectedCategory(c.id)}
                className={selectedCategory === c.id ? 'bg-violet-500 hover:bg-violet-600' : 'border-white/10'}
                data-testid={`public-cat-${c.id}`}
              >
                {c.label}
              </Button>
            ))}
          </div>
        </div>
      </section>

      {/* Content grid */}
      <section className="px-6 pb-24 max-w-7xl mx-auto">
        {loading ? (
          <div className="text-center py-20 text-zinc-500">Loading…</div>
        ) : docs.length === 0 ? (
          <div className="text-center py-20 glass-card max-w-2xl mx-auto">
            <BookOpen className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
            <p className="text-zinc-400">No public content yet. Check back soon.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {docs.map((d) => (
              <div
                key={d.id}
                className="group glass-card p-6 hover:border-violet-500/30 transition-all"
                data-testid={`public-card-${d.id}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <Badge className="bg-violet-500/20 text-violet-300">{d.category || 'public'}</Badge>
                  <FileText className="w-5 h-5 text-violet-400" />
                </div>
                <h3 className="font-semibold text-lg mb-2 group-hover:text-violet-300 transition-colors">{d.title}</h3>
                {d.description && <p className="text-sm text-zinc-400 line-clamp-3 mb-3">{d.description}</p>}
                <div className="text-xs text-zinc-500 flex items-center gap-2 mb-4">
                  <Calendar className="w-3 h-3" />
                  {d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}
                  <span>·</span>
                  {d.filename}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    onClick={() => navigate(`/public/${d.id}`)}
                    className="bg-violet-500 hover:bg-violet-600"
                    data-testid={`public-view-${d.id}`}
                  >
                    <Eye className="w-4 h-4 mr-1" /> Read
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => d.has_audio ? navigate(`/login?next=/public/${d.id}?play=audio`) : requireLoginForMedia('audio')}
                    className="border-white/10"
                    disabled={!d.has_audio}
                    data-testid={`public-audio-${d.id}`}
                    title={d.has_audio ? 'Sign in to listen' : 'No audio yet'}
                  >
                    {d.has_audio ? <Lock className="w-3 h-3 mr-1" /> : null}
                    <Headphones className="w-4 h-4 mr-1" /> Audio
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => d.has_video ? navigate(`/login?next=/public/${d.id}?play=video`) : requireLoginForMedia('video')}
                    className="border-white/10"
                    disabled={!d.has_video}
                    data-testid={`public-video-${d.id}`}
                    title={d.has_video ? 'Sign in to watch' : 'No video yet'}
                  >
                    {d.has_video ? <Lock className="w-3 h-3 mr-1" /> : null}
                    <Video className="w-4 h-4 mr-1" /> Video
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* CTA */}
      <section className="border-t border-white/5 px-6 py-16 bg-gradient-to-br from-violet-500/5 to-blue-500/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Want the full experience?</h2>
          <p className="text-zinc-400 mb-6">
            Sign in or create an account to unlock audio narrations, video versions, and your own personalized learning journey.
          </p>
          <Button size="lg" className="bg-violet-500 hover:bg-violet-600" onClick={() => navigate('/register')}>
            Create your free account <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </section>
    </div>
  );
}
