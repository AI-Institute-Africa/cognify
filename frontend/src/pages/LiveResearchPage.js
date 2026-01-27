import React, { useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { searchResearch } from '../services/api';
import { 
  Search, 
  Globe, 
  FileText, 
  ExternalLink,
  TrendingUp,
  Newspaper,
  BookOpen,
  Briefcase,
  Loader2,
  Sparkles,
  Filter,
  Clock,
  Link2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

const categories = [
  { value: 'all', label: 'All Sources', icon: Globe },
  { value: 'research', label: 'Research Papers', icon: FileText },
  { value: 'news', label: 'Industry News', icon: Newspaper },
  { value: 'tools', label: 'Tools & Software', icon: Briefcase },
  { value: 'tutorials', label: 'Tutorials', icon: BookOpen },
];

export default function LiveResearchPage() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [directLinks, setDirectLinks] = useState([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setLoading(true);
    setSearched(true);

    try {
      const response = await searchResearch(query);
      setResults(response.ai_results || []);
      setDirectLinks(response.direct_search_links || []);
      toast.success(`Found results for "${query}"`);
    } catch (error) {
      console.error('Search failed:', error);
      toast.error('Search failed. Please try again.');
      // Still show direct links
      const encoded = encodeURIComponent(query);
      setDirectLinks([
        { title: `Search "${query}" on Google Scholar`, url: `https://scholar.google.com/scholar?q=${encoded}`, source: 'Google Scholar' },
        { title: `Search "${query}" on arXiv`, url: `https://arxiv.org/search/?query=${encoded}&searchtype=all`, source: 'arXiv' },
        { title: `Search "${query}" on ResearchGate`, url: `https://www.researchgate.net/search/publication?q=${encoded}`, source: 'ResearchGate' },
        { title: `Search "${query}" on PubMed`, url: `https://pubmed.ncbi.nlm.nih.gov/?term=${encoded}`, source: 'PubMed' },
        { title: `Search "${query}" on Semantic Scholar`, url: `https://www.semanticscholar.org/search?q=${encoded}`, source: 'Semantic Scholar' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getCategoryColor = (cat) => {
    switch (cat) {
      case 'research': return 'text-violet-400 bg-violet-500/20';
      case 'news': return 'text-blue-400 bg-blue-500/20';
      case 'tools': return 'text-emerald-400 bg-emerald-500/20';
      case 'tutorials': return 'text-amber-400 bg-amber-500/20';
      default: return 'text-zinc-400 bg-zinc-500/20';
    }
  };

  return (
    <DashboardLayout>
      <Header 
        title="Live Research Engine"
        subtitle="Real-time research papers, news & industry signals"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 border-blue-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-blue-500/20">
                <TrendingUp className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Stay Updated with Industry Signals</h3>
                <p className="text-zinc-400 text-sm">
                  Connect your learning concepts to real-world research, industry news, and the latest tools. 
                  Our engine aggregates content from academic databases, news sources, and tech platforms.
                </p>
              </div>
            </div>
          </div>

          {/* Search Section */}
          <div className="glass-card p-6 mb-8">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search Input */}
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Search for topics, concepts, or technologies..."
                  data-testid="research-search-input"
                  className="pl-12 h-12 bg-zinc-900/50 border-white/10"
                />
              </div>

              {/* Category Filter */}
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="w-full md:w-[200px] h-12 bg-zinc-900/50 border-white/10">
                  <Filter className="w-4 h-4 mr-2 text-zinc-500" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10">
                  {categories.map(cat => (
                    <SelectItem key={cat.value} value={cat.value}>
                      <span className="flex items-center gap-2">
                        <cat.icon className="w-4 h-4" />
                        {cat.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Search Button */}
              <Button
                onClick={handleSearch}
                disabled={loading}
                data-testid="research-search-btn"
                className="h-12 px-8 bg-blue-500 hover:bg-blue-600"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>

            {/* Quick Search Suggestions */}
            {!searched && (
              <div className="mt-4">
                <p className="text-xs text-zinc-500 mb-2">Popular searches:</p>
                <div className="flex flex-wrap gap-2">
                  {['Machine Learning', 'Adaptive Learning', 'Knowledge Graphs', 'EdTech Trends'].map(term => (
                    <button
                      key={term}
                      onClick={() => { setQuery(term); handleSearch(); }}
                      className="px-3 py-1.5 rounded-full bg-zinc-800 text-sm text-zinc-400 hover:bg-zinc-700 hover:text-white transition-colors"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Results Section */}
          {searched && (
            <div className="space-y-4">
              {/* Results Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">
                  {loading ? 'Searching...' : `${results.length} Results`}
                </h2>
                {results.length > 0 && (
                  <Badge variant="outline" className="border-zinc-700">
                    Sorted by relevance
                  </Badge>
                )}
              </div>

              {/* Loading State */}
              {loading && (
                <div className="glass-card p-12 text-center">
                  <Loader2 className="w-12 h-12 text-blue-400 mx-auto mb-4 animate-spin" />
                  <p className="text-zinc-400">Searching across research databases, news, and tools...</p>
                </div>
              )}

              {/* Results List */}
              {!loading && results.length > 0 && (
                <div className="space-y-4">
                  {results.map((result, index) => {
                    const CategoryIcon = getCategoryIcon(result.category);
                    
                    return (
                      <div
                        key={result.id}
                        className={`glass-card p-6 hover:border-white/20 transition-all animate-fadeIn stagger-${index + 1}`}
                        data-testid={`research-result-${result.id}`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            {/* Category & Source */}
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={getCategoryColor(result.category)}>
                                <CategoryIcon className="w-3 h-3 mr-1" />
                                {result.category}
                              </Badge>
                              <span className="text-sm text-zinc-500">{result.source}</span>
                              <span className="text-xs text-zinc-600 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {result.date}
                              </span>
                            </div>

                            {/* Title */}
                            <h3 className="text-lg font-semibold mb-2 hover:text-blue-400 transition-colors">
                              <a href={result.url} target="_blank" rel="noopener noreferrer">
                                {result.title}
                              </a>
                            </h3>

                            {/* Snippet */}
                            <p className="text-sm text-zinc-400 line-clamp-2">{result.snippet}</p>
                          </div>

                          {/* Relevance Score & Actions */}
                          <div className="flex flex-col items-end gap-3">
                            <div className="text-right">
                              <p className="text-xs text-zinc-500">Relevance</p>
                              <p className="text-lg font-bold text-blue-400">{result.relevance}%</p>
                            </div>
                            <a
                              href={result.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors"
                            >
                              <ExternalLink className="w-4 h-4 text-zinc-400" />
                            </a>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* No Results */}
              {!loading && results.length === 0 && (
                <div className="glass-card p-12 text-center">
                  <Search className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No AI-generated results</h3>
                  <p className="text-zinc-500 mb-4">
                    Try the direct search links below to find publications
                  </p>
                </div>
              )}

              {/* Direct Search Links */}
              {!loading && directLinks.length > 0 && (
                <div className="glass-card p-6 mt-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Link2 className="w-5 h-5 text-emerald-400" />
                    Direct Search Links (Real Publications)
                  </h3>
                  <p className="text-sm text-zinc-500 mb-4">
                    Click these links to search directly on academic databases:
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {directLinks.map((link, idx) => (
                      <a
                        key={idx}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 p-4 rounded-xl bg-zinc-800/50 hover:bg-zinc-700/50 border border-white/5 hover:border-emerald-500/30 transition-all"
                        data-testid={`direct-link-${idx}`}
                      >
                        <div className="p-2 rounded-lg bg-emerald-500/20">
                          <ExternalLink className="w-4 h-4 text-emerald-400" />
                        </div>
                        <div>
                          <p className="font-medium text-sm">{link.source}</p>
                          <p className="text-xs text-zinc-500">Search &quot;{query}&quot;</p>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Initial State */}
          {!searched && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {categories.slice(1).map(cat => (
                <button
                  key={cat.value}
                  onClick={() => { setCategory(cat.value); setQuery(cat.label); }}
                  className="glass-card p-6 text-left hover:border-white/20 transition-all group"
                >
                  <div className={`w-12 h-12 rounded-xl ${getCategoryColor(cat.value)} flex items-center justify-center mb-4`}>
                    <cat.icon className="w-6 h-6" />
                  </div>
                  <h3 className="font-semibold mb-2 group-hover:text-blue-400 transition-colors">
                    {cat.label}
                  </h3>
                  <p className="text-sm text-zinc-500">
                    {cat.value === 'research' && 'Academic papers, journals, and studies'}
                    {cat.value === 'news' && 'Latest industry news and trends'}
                    {cat.value === 'tools' && 'Software, platforms, and developer tools'}
                    {cat.value === 'tutorials' && 'Guides, how-tos, and learning resources'}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
