/* Public /news/:slug — article detail. */
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Loader2, ExternalLink, ChevronLeft } from 'lucide-react';
import { Badge } from '../components/ui/badge';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PublicNewsArticlePage() {
  const { slug } = useParams();
  const [article, setArticle] = useState(null);
  const [notFound, setNotFound] = useState(false);
  useEffect(() => {
    axios.get(`${API}/api/public/news/${slug}`)
      .then(({ data }) => setArticle(data))
      .catch(() => setNotFound(true));
  }, [slug]);
  if (notFound) {
    return <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-300">
      <div className="text-center">
        <h1 className="text-2xl mb-3">Article not found</h1>
        <Link to="/news" className="text-violet-400">← Back to news</Link>
      </div>
    </div>;
  }
  if (!article) return <div className="min-h-screen flex items-center justify-center bg-zinc-950">
    <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
  </div>;
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-3xl mx-auto px-4 py-10">
        <Link to="/news" className="text-sm text-violet-400 hover:text-violet-300 flex items-center gap-1 mb-6">
          <ChevronLeft className="w-4 h-4" /> Back to news
        </Link>
        <div className="text-xs text-zinc-500 mb-3">
          {article.source} · {article.publication_date || article.published_at?.slice(0, 10)}
          <Badge className="ml-2 bg-zinc-800 uppercase text-[10px]">{article.category}</Badge>
        </div>
        <h1 className="text-3xl sm:text-4xl font-semibold text-white leading-tight mb-4" data-testid="article-title">{article.title}</h1>
        <p className="text-lg text-zinc-300 leading-relaxed mb-6">{article.summary}</p>
        {article.impact && (
          <div className="mb-8 p-4 rounded-lg border border-violet-500/30 bg-violet-500/10">
            <div className="text-xs uppercase font-semibold text-violet-300 mb-1">Why it matters</div>
            <p className="text-violet-200">{article.impact}</p>
          </div>
        )}
        {article.source_url && (
          <a href={article.source_url} target="_blank" rel="noreferrer"
             className="inline-flex items-center gap-2 text-sm text-violet-400 hover:text-violet-300"
             data-testid="article-source-link">
            Read the original story <ExternalLink className="w-4 h-4" />
          </a>
        )}
        <p className="text-xs text-zinc-500 mt-8">
          Published to <span className="text-zinc-400">{article.destination_name}</span> ·
          Week {article.published_week}, {article.published_year}
        </p>
      </div>
    </div>
  );
}
