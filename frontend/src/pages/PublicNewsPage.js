/* Public /news — Cognify News page. Renders published articles for the
   current active INTERNAL destination. Reachable at:
     https://cognify.aiinstituteafrica.com/news
   and on the preview at /news. */
import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Loader2, ExternalLink, ArrowRight, Newspaper } from 'lucide-react';
import { Badge } from '../components/ui/badge';

const API = process.env.REACT_APP_BACKEND_URL;

const ICON = { research: '🔬', product: '🚀', policy: '📜',
               funding: '💰', africa: '🌍', applied: '⚙️' };

export default function PublicNewsPage() {
  const [data, setData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API}/api/public/news`)
      .then(({ data }) => setData(data))
      .catch(() => setData({ articles: [] }));
  }, []);

  if (!data) return <div className="min-h-screen flex items-center justify-center bg-zinc-950">
    <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
  </div>;

  const { articles = [], active_destination, iso_week } = data;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Newspaper className="w-7 h-7 text-violet-400" />
              <h1 className="text-4xl sm:text-5xl font-semibold">Cognify News</h1>
            </div>
            <p className="text-zinc-400 text-sm">
              Real-time AI research, product launches and policy news — curated by our Live Research Engine.
            </p>
          </div>
          {active_destination && (
            <Badge className="bg-violet-500/20 text-violet-300 text-xs">
              Publishing to · {active_destination.name} · Week {iso_week}
            </Badge>
          )}
        </div>

        {articles.length === 0 ? (
          <div className="glass-card p-10 text-center text-zinc-400" data-testid="news-empty">
            <Newspaper className="w-10 h-10 mx-auto mb-3 opacity-50" />
            <p>No articles published to Cognify yet. Come back after the next digest cycle.</p>
          </div>
        ) : (
          <ul className="space-y-4">
            {articles.map((a) => (
              <li key={a.id} data-testid={`news-item-${a.id}`}
                  className="p-5 rounded-xl border border-white/10 bg-zinc-900/60 hover:border-violet-500/40 transition">
                <div className="flex items-center gap-2 text-xs text-zinc-500 mb-2">
                  <span>{ICON[a.category] || '🧠'}</span>
                  <span className="font-medium">{a.source}</span>
                  <span>·</span>
                  <span>{a.publication_date || a.published_at?.slice(0, 10)}</span>
                  <Badge className="bg-zinc-800 text-zinc-300 uppercase text-[10px]">{a.category}</Badge>
                </div>
                <h2 className="text-xl font-semibold text-white leading-tight mb-2">
                  <Link to={`/news/${a.slug || a.id}`} className="hover:text-violet-300">{a.title}</Link>
                </h2>
                <p className="text-sm text-zinc-400 leading-relaxed">{a.summary}</p>
                {a.impact && (
                  <p className="text-sm text-violet-300 mt-2">
                    <span className="font-semibold">Why it matters:</span> {a.impact}
                  </p>
                )}
                <div className="mt-4 flex items-center gap-4 text-sm">
                  <Link to={`/news/${a.slug || a.id}`} className="text-violet-400 hover:text-violet-300 flex items-center gap-1" data-testid={`news-read-${a.id}`}>
                    Read on Cognify <ArrowRight className="w-3 h-3" />
                  </Link>
                  {a.source_url && (
                    <a href={a.source_url} target="_blank" rel="noreferrer"
                       className="text-zinc-500 hover:text-zinc-300 flex items-center gap-1">
                      Source <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
