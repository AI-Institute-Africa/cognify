import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import {
  Share2,
  Link as LinkIcon,
  Copy,
  Download,
  Users,
  Globe,
  Lock,
  FileText,
  Award,
  BookOpen,
  Brain,
  CheckCircle,
  Clock,
  Trash2,
  ExternalLink,
  Eye,
  Settings,
  Mail,
  RefreshCw,
  Plus
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// Content types that can be shared
const SHAREABLE_TYPES = [
  { id: 'assignment', name: 'Assignments', icon: FileText, color: 'blue' },
  { id: 'grade', name: 'Grades & Reports', icon: Award, color: 'emerald' },
  { id: 'course_progress', name: 'Course Progress', icon: BookOpen, color: 'violet' },
  { id: 'ai_output', name: 'AI Mentor Outputs', icon: Brain, color: 'amber' },
  { id: 'certificate', name: 'Certificates', icon: Award, color: 'pink' },
  { id: 'achievement', name: 'Achievements', icon: CheckCircle, color: 'cyan' },
];

export default function ShareContentPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [sharedItems, setSharedItems] = useState([]);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [selectedType, setSelectedType] = useState(null);
  const [shareableContent, setShareableContent] = useState([]);
  const [selectedContent, setSelectedContent] = useState(null);
  const [creating, setCreating] = useState(false);

  const [shareSettings, setShareSettings] = useState({
    visibility: 'public', // 'public', 'link_only', 'specific_users'
    expires_in_days: 30,
    allow_download: true,
    recipients: ''
  });

  useEffect(() => {
    loadSharedItems();
  }, []);

  const loadSharedItems = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/share/my-shared`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSharedItems(data || []);
      }
    } catch (error) {
      console.error('Failed to load shared items:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadShareableContent = async (type) => {
    setSelectedType(type);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/share/available/${type}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setShareableContent(data || []);
      }
    } catch (error) {
      console.error('Failed to load content:', error);
      setShareableContent([]);
    }
  };

  const handleShare = async () => {
    if (!selectedContent) {
      toast.error('Please select content to share');
      return;
    }

    setCreating(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/share/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content_type: selectedType,
          content_id: selectedContent.id,
          content_title: selectedContent.title || selectedContent.name,
          visibility: shareSettings.visibility,
          expires_in_days: shareSettings.expires_in_days,
          allow_download: shareSettings.allow_download,
          recipient_emails: shareSettings.recipients.split(',').map(e => e.trim()).filter(Boolean)
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('Content shared successfully!');
        
        // Copy link to clipboard
        if (data.share_url) {
          navigator.clipboard.writeText(data.share_url);
          toast.info('Share link copied to clipboard!');
        }

        setShowShareDialog(false);
        setSelectedContent(null);
        setSelectedType(null);
        setShareSettings({
          visibility: 'public',
          expires_in_days: 30,
          allow_download: true,
          recipients: ''
        });
        loadSharedItems();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to share content');
      }
    } catch (error) {
      toast.error('Failed to share content');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (shareId) => {
    if (!confirm('Are you sure you want to remove this share?')) return;

    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/share/${shareId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Share removed');
        loadSharedItems();
      }
    } catch (error) {
      toast.error('Failed to remove share');
    }
  };

  const copyShareLink = (url) => {
    navigator.clipboard.writeText(url);
    toast.success('Link copied to clipboard!');
  };

  const getTypeInfo = (typeId) => {
    return SHAREABLE_TYPES.find(t => t.id === typeId);
  };

  return (
    <DashboardLayout>
      <Header 
        title="Share Content"
        subtitle="Share your achievements, grades, and learning progress"
      />

      <div className="p-8">
        {/* Content Type Selection */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">What would you like to share?</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {SHAREABLE_TYPES.map((type) => {
              const Icon = type.icon;
              return (
                <button
                  key={type.id}
                  onClick={() => {
                    loadShareableContent(type.id);
                    setShowShareDialog(true);
                  }}
                  className={`p-4 rounded-xl border border-white/10 hover:border-${type.color}-500/30 transition-all text-center group`}
                  data-testid={`share-type-${type.id}`}
                >
                  <div className={`w-12 h-12 rounded-xl bg-${type.color}-500/20 flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform`}>
                    <Icon className={`w-6 h-6 text-${type.color}-400`} />
                  </div>
                  <span className="text-sm font-medium">{type.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Shared Items */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Your Shared Content</h3>
            <Badge className="bg-violet-500/20 text-violet-400">
              {sharedItems.length} items shared
            </Badge>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
            </div>
          ) : sharedItems.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <Share2 className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">No Shared Content Yet</h3>
              <p className="text-zinc-500 mb-6 max-w-md mx-auto">
                Share your assignments, grades, certificates, and achievements with others.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sharedItems.map((item) => {
                const typeInfo = getTypeInfo(item.content_type);
                const Icon = typeInfo?.icon || FileText;
                const isExpired = item.expires_at && new Date(item.expires_at) < new Date();

                return (
                  <div 
                    key={item.id}
                    className={`glass-card p-4 ${isExpired ? 'opacity-50' : ''}`}
                    data-testid={`shared-item-${item.id}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className={`p-2 rounded-lg bg-${typeInfo?.color || 'zinc'}-500/20`}>
                        <Icon className={`w-5 h-5 text-${typeInfo?.color || 'zinc'}-400`} />
                      </div>
                      <div className="flex items-center gap-2">
                        {item.visibility === 'public' ? (
                          <Badge className="bg-emerald-500/20 text-emerald-400 text-xs">
                            <Globe className="w-3 h-3 mr-1" />
                            Public
                          </Badge>
                        ) : item.visibility === 'link_only' ? (
                          <Badge className="bg-amber-500/20 text-amber-400 text-xs">
                            <LinkIcon className="w-3 h-3 mr-1" />
                            Link Only
                          </Badge>
                        ) : (
                          <Badge className="bg-blue-500/20 text-blue-400 text-xs">
                            <Lock className="w-3 h-3 mr-1" />
                            Private
                          </Badge>
                        )}
                      </div>
                    </div>

                    <h4 className="font-medium mb-1 truncate">{item.content_title || 'Shared Content'}</h4>
                    <p className="text-sm text-zinc-500 mb-3">
                      {typeInfo?.name || item.content_type}
                    </p>

                    <div className="flex items-center justify-between text-xs text-zinc-500 mb-3">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {item.view_count || 0} views
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {isExpired ? 'Expired' : item.expires_at ? `Expires ${new Date(item.expires_at).toLocaleDateString()}` : 'Never expires'}
                      </span>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyShareLink(item.share_url)}
                        className="flex-1 border-white/10"
                      >
                        <Copy className="w-3 h-3 mr-1" />
                        Copy Link
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(item.share_url, '_blank')}
                        className="border-white/10"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(item.id)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-3 h-3" />
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
        <DialogContent className="bg-zinc-900 border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Share2 className="w-5 h-5 text-violet-400" />
              Share {getTypeInfo(selectedType)?.name || 'Content'}
            </DialogTitle>
            <DialogDescription className="text-zinc-500">
              Select content to share and configure sharing settings.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Content Selection */}
            <div className="space-y-3">
              <Label>Select Content to Share</Label>
              <div className="grid grid-cols-1 gap-2 max-h-[200px] overflow-y-auto">
                {shareableContent.length === 0 ? (
                  <p className="text-zinc-500 text-center py-4">
                    No {getTypeInfo(selectedType)?.name?.toLowerCase() || 'content'} available to share
                  </p>
                ) : (
                  shareableContent.map((content) => (
                    <button
                      key={content.id}
                      onClick={() => setSelectedContent(content)}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        selectedContent?.id === content.id
                          ? 'border-violet-500 bg-violet-500/10'
                          : 'border-white/10 hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center">
                          {React.createElement(getTypeInfo(selectedType)?.icon || FileText, {
                            className: 'w-4 h-4 text-zinc-400'
                          })}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm truncate">{content.title || content.name}</h4>
                          {content.date && (
                            <p className="text-xs text-zinc-500">{new Date(content.date).toLocaleDateString()}</p>
                          )}
                        </div>
                        {selectedContent?.id === content.id && (
                          <CheckCircle className="w-5 h-5 text-violet-400" />
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>

            {/* Share Settings */}
            <div className="space-y-4 pt-4 border-t border-white/10">
              <h4 className="font-medium flex items-center gap-2">
                <Settings className="w-4 h-4 text-zinc-400" />
                Sharing Settings
              </h4>

              <div>
                <Label>Visibility</Label>
                <Select 
                  value={shareSettings.visibility}
                  onValueChange={(v) => setShareSettings(prev => ({...prev, visibility: v}))}
                >
                  <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-white/10">
                    <SelectItem value="public">
                      <span className="flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        Public - Anyone can view
                      </span>
                    </SelectItem>
                    <SelectItem value="link_only">
                      <span className="flex items-center gap-2">
                        <LinkIcon className="w-4 h-4" />
                        Link Only - Anyone with link
                      </span>
                    </SelectItem>
                    <SelectItem value="specific_users">
                      <span className="flex items-center gap-2">
                        <Lock className="w-4 h-4" />
                        Specific Users - Email required
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {shareSettings.visibility === 'specific_users' && (
                <div>
                  <Label>Recipient Emails (comma separated)</Label>
                  <Input
                    placeholder="email1@example.com, email2@example.com"
                    value={shareSettings.recipients}
                    onChange={(e) => setShareSettings(prev => ({...prev, recipients: e.target.value}))}
                    className="mt-1 bg-zinc-800 border-white/10"
                  />
                </div>
              )}

              <div>
                <Label>Expires In</Label>
                <Select 
                  value={shareSettings.expires_in_days.toString()}
                  onValueChange={(v) => setShareSettings(prev => ({...prev, expires_in_days: parseInt(v)}))}
                >
                  <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-white/10">
                    <SelectItem value="7">7 days</SelectItem>
                    <SelectItem value="30">30 days</SelectItem>
                    <SelectItem value="90">90 days</SelectItem>
                    <SelectItem value="365">1 year</SelectItem>
                    <SelectItem value="0">Never</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
                <div className="flex items-center gap-3">
                  <Download className="w-5 h-5 text-zinc-400" />
                  <div>
                    <span className="font-medium">Allow Download</span>
                    <p className="text-xs text-zinc-500">Let viewers download this content</p>
                  </div>
                </div>
                <Switch 
                  checked={shareSettings.allow_download}
                  onCheckedChange={(v) => setShareSettings(prev => ({...prev, allow_download: v}))}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowShareDialog(false)}
              className="border-white/10"
            >
              Cancel
            </Button>
            <Button
              onClick={handleShare}
              disabled={creating || !selectedContent}
              className="bg-violet-500 hover:bg-violet-600"
              data-testid="share-content-btn"
            >
              {creating ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Share2 className="w-4 h-4 mr-2" />
                  Share Content
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
