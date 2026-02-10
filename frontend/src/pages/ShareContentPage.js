import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Share2,
  Link,
  Download,
  Users,
  Copy,
  ExternalLink,
  Brain,
  FileText,
  Trophy,
  GraduationCap,
  Mic,
  HelpCircle,
  CheckCircle,
  Loader2,
  Clock,
  Eye,
  Lock
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const CONTENT_TYPES = [
  { id: 'ai_response', label: 'AI Mentor Responses', icon: Brain, color: 'violet' },
  { id: 'assignment', label: 'Assignments', icon: FileText, color: 'blue' },
  { id: 'grade', label: 'Grades', icon: GraduationCap, color: 'emerald' },
  { id: 'achievement', label: 'Achievements', icon: Trophy, color: 'amber' },
  { id: 'learn_by_teaching', label: 'Learn-by-Teaching Content', icon: Mic, color: 'pink' },
  { id: 'question_analysis', label: 'Question Analysis', icon: HelpCircle, color: 'cyan' },
];

export default function ShareContentPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [shares, setShares] = useState([]);
  const [contentType, setContentType] = useState('all');
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [selectedContent, setSelectedContent] = useState(null);
  const [sharing, setSharing] = useState(false);
  const [shareOptions, setShareOptions] = useState({
    type: 'link',
    permission: 'view',
    expiry: '30',
    recipients: []
  });

  // Shareable content from various sources
  const [shareableContent, setShareableContent] = useState([]);

  useEffect(() => {
    loadShares();
    loadShareableContent();
  }, []);

  const loadShares = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/user/shares`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setShares(data.shares || []);
      }
    } catch (error) {
      console.error('Failed to load shares:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadShareableContent = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/user/shareable-content`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setShareableContent(data.content || []);
      }
    } catch (error) {
      console.error('Failed to load content:', error);
    }
  };

  const handleShare = async () => {
    if (!selectedContent) return;

    setSharing(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/share/content`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content_type: selectedContent.type,
          content_id: selectedContent.id,
          share_type: shareOptions.type,
          permission: shareOptions.permission,
          expiry_days: parseInt(shareOptions.expiry),
          recipient_ids: shareOptions.recipients
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        if (shareOptions.type === 'link') {
          const shareUrl = `${window.location.origin}/shared/${data.share_code}`;
          await navigator.clipboard.writeText(shareUrl);
          toast.success('Share link copied to clipboard!');
        } else {
          toast.success('Content shared successfully!');
        }
        
        setShowShareDialog(false);
        loadShares();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to share');
      }
    } catch (error) {
      toast.error('Failed to share content');
    } finally {
      setSharing(false);
    }
  };

  const copyShareLink = (shareCode) => {
    const shareUrl = `${window.location.origin}/shared/${shareCode}`;
    navigator.clipboard.writeText(shareUrl);
    toast.success('Link copied!');
  };

  const downloadContent = async (share) => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/share/${share.share_code}/download`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${share.content_type}-${share.share_code}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Downloaded!');
      }
    } catch (error) {
      toast.error('Failed to download');
    }
  };

  const filteredContent = contentType === 'all' 
    ? shareableContent 
    : shareableContent.filter(c => c.type === contentType);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="w-12 h-12 animate-spin text-violet-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Share & Collaborate"
        subtitle="Share your learning achievements and content with others"
      />
      
      <div className="p-4 sm:p-6 lg:p-8">
        {/* Content Types */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          {CONTENT_TYPES.map(type => {
            const Icon = type.icon;
            const count = shareableContent.filter(c => c.type === type.id).length;
            return (
              <button
                key={type.id}
                onClick={() => setContentType(contentType === type.id ? 'all' : type.id)}
                className={`p-4 rounded-xl border transition-all text-center ${
                  contentType === type.id
                    ? `border-${type.color}-500/50 bg-${type.color}-500/10`
                    : 'border-white/10 hover:border-white/20'
                }`}
                data-testid={`filter-${type.id}`}
              >
                <Icon className={`w-6 h-6 mx-auto mb-2 text-${type.color}-400`} />
                <p className="text-sm font-medium">{type.label}</p>
                <Badge className={`mt-2 bg-${type.color}-500/20 text-${type.color}-400`}>
                  {count}
                </Badge>
              </button>
            );
          })}
        </div>

        {/* Shareable Content */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-4">Your Content</h2>
          {filteredContent.length === 0 ? (
            <div className="text-center py-12 glass-card">
              <Share2 className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-500">No shareable content found</p>
              <p className="text-xs text-zinc-600 mt-1">
                Complete courses, get grades, or create content to share
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredContent.map((content, index) => {
                const typeInfo = CONTENT_TYPES.find(t => t.id === content.type);
                const Icon = typeInfo?.icon || Share2;
                return (
                  <div
                    key={content.id}
                    className={`glass-card p-4 animate-fadeIn stagger-${(index % 5) + 1}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg bg-${typeInfo?.color || 'zinc'}-500/20`}>
                        <Icon className={`w-5 h-5 text-${typeInfo?.color || 'zinc'}-400`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium truncate">{content.title}</h3>
                        <p className="text-xs text-zinc-500 mt-1">{content.description}</p>
                        <p className="text-xs text-zinc-600 mt-2">
                          {new Date(content.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => {
                        setSelectedContent(content);
                        setShowShareDialog(true);
                      }}
                      size="sm"
                      className="w-full mt-3 bg-violet-500/10 text-violet-400 hover:bg-violet-500 hover:text-white"
                    >
                      <Share2 className="w-4 h-4 mr-2" />
                      Share
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Active Shares */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Your Shared Links</h2>
          {shares.length === 0 ? (
            <div className="text-center py-12 glass-card">
              <Link className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-500">No active shares</p>
            </div>
          ) : (
            <div className="space-y-3">
              {shares.map((share) => {
                const typeInfo = CONTENT_TYPES.find(t => t.id === share.content_type);
                const Icon = typeInfo?.icon || Share2;
                const isExpired = share.expires_at && new Date(share.expires_at) < new Date();
                return (
                  <div
                    key={share.id}
                    className={`glass-card p-4 flex items-center justify-between ${isExpired ? 'opacity-50' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg bg-${typeInfo?.color || 'zinc'}-500/20`}>
                        <Icon className={`w-5 h-5 text-${typeInfo?.color || 'zinc'}-400`} />
                      </div>
                      <div>
                        <p className="font-medium">{share.title || share.content_type}</p>
                        <div className="flex items-center gap-3 text-xs text-zinc-500 mt-1">
                          <span className="flex items-center gap-1">
                            <Eye className="w-3 h-3" />
                            {share.access_count || 0} views
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {isExpired ? 'Expired' : `Expires ${new Date(share.expires_at).toLocaleDateString()}`}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        onClick={() => copyShareLink(share.share_code)}
                        size="sm"
                        variant="outline"
                        className="border-white/10"
                        disabled={isExpired}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button
                        onClick={() => downloadContent(share)}
                        size="sm"
                        variant="outline"
                        className="border-white/10"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Share Dialog */}
      <Dialog open={showShareDialog} onOpenChange={setShowShareDialog}>
        <DialogContent className="bg-zinc-900 border-white/10">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Share2 className="w-5 h-5 text-violet-400" />
              Share Content
            </DialogTitle>
            <DialogDescription className="text-zinc-500">
              Choose how you want to share "{selectedContent?.title}"
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <label className="text-sm text-zinc-400">Share Method</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => setShareOptions(prev => ({ ...prev, type: 'link' }))}
                  className={`p-3 rounded-lg border text-center transition-all ${
                    shareOptions.type === 'link'
                      ? 'border-violet-500 bg-violet-500/10'
                      : 'border-white/10 hover:border-white/20'
                  }`}
                >
                  <Link className="w-5 h-5 mx-auto mb-1" />
                  <p className="text-xs">Link</p>
                </button>
                <button
                  onClick={() => setShareOptions(prev => ({ ...prev, type: 'internal' }))}
                  className={`p-3 rounded-lg border text-center transition-all ${
                    shareOptions.type === 'internal'
                      ? 'border-violet-500 bg-violet-500/10'
                      : 'border-white/10 hover:border-white/20'
                  }`}
                >
                  <Users className="w-5 h-5 mx-auto mb-1" />
                  <p className="text-xs">Internal</p>
                </button>
                <button
                  onClick={() => setShareOptions(prev => ({ ...prev, type: 'download' }))}
                  className={`p-3 rounded-lg border text-center transition-all ${
                    shareOptions.type === 'download'
                      ? 'border-violet-500 bg-violet-500/10'
                      : 'border-white/10 hover:border-white/20'
                  }`}
                >
                  <Download className="w-5 h-5 mx-auto mb-1" />
                  <p className="text-xs">Download</p>
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm text-zinc-400">Permission</label>
              <Select
                value={shareOptions.permission}
                onValueChange={(value) => setShareOptions(prev => ({ ...prev, permission: value }))}
              >
                <SelectTrigger className="bg-zinc-800/50 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10">
                  <SelectItem value="view">View Only</SelectItem>
                  <SelectItem value="comment">Can Comment</SelectItem>
                  <SelectItem value="copy">Can Copy</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm text-zinc-400">Link Expiry</label>
              <Select
                value={shareOptions.expiry}
                onValueChange={(value) => setShareOptions(prev => ({ ...prev, expiry: value }))}
              >
                <SelectTrigger className="bg-zinc-800/50 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10">
                  <SelectItem value="7">7 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                  <SelectItem value="90">90 days</SelectItem>
                  <SelectItem value="365">1 year</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleShare}
              disabled={sharing}
              className="w-full bg-violet-500 hover:bg-violet-600"
            >
              {sharing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating Share...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  {shareOptions.type === 'link' ? 'Copy Share Link' : 'Share'}
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
