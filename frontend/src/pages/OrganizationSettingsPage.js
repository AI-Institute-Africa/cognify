import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { 
  Building2, Globe, Phone, MapPin, 
  Facebook, Twitter, Linkedin, Instagram,
  Upload, Database, FileText, Loader2, 
  Save, Link, Settings, Shield, Trash2
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function OrganizationSettingsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [organization, setOrganization] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [dbStatus, setDbStatus] = useState(null);
  
  // Form states
  const [profile, setProfile] = useState({
    name: '',
    description: '',
    website: '',
    phone: '',
    address: '',
    logo_url: '',
    facebook: '',
    twitter: '',
    linkedin: '',
    instagram: ''
  });
  
  const [newDoc, setNewDoc] = useState({ file: null, title: '', description: '', docType: 'reference' });
  const [uploadingDoc, setUploadingDoc] = useState(false);
  
  const [dbConfig, setDbConfig] = useState({
    db_type: 'mongodb',
    connection_string: '',
    db_name: '',
    collection_name: ''
  });
  const [connectingDb, setConnectingDb] = useState(false);

  useEffect(() => {
    loadOrganization();
    loadDocuments();
    loadDbStatus();
  }, []);

  const loadOrganization = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/org/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setOrganization(data);
        setProfile({
          name: data.name || '',
          description: data.description || '',
          website: data.website || '',
          phone: data.phone || '',
          address: data.address || '',
          logo_url: data.logo_url || '',
          facebook: data.social_media?.facebook || '',
          twitter: data.social_media?.twitter || '',
          linkedin: data.social_media?.linkedin || '',
          instagram: data.social_media?.instagram || ''
        });
      }
    } catch (error) {
      console.error('Failed to load organization:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/org/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data || []);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const loadDbStatus = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/org/database/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDbStatus(data);
      }
    } catch (error) {
      console.error('Failed to load DB status:', error);
    }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/org/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: profile.name,
          description: profile.description,
          website: profile.website,
          phone: profile.phone,
          address: profile.address,
          logo_url: profile.logo_url,
          social_media: {
            facebook: profile.facebook,
            twitter: profile.twitter,
            linkedin: profile.linkedin,
            instagram: profile.instagram
          }
        })
      });
      
      if (response.ok) {
        toast.success('Organization profile saved!');
      } else {
        toast.error('Failed to save profile');
      }
    } catch (error) {
      console.error('Save error:', error);
      toast.error('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const handleUploadDocument = async () => {
    if (!newDoc.file || !newDoc.title) {
      toast.error('Please select a file and provide a title');
      return;
    }
    
    setUploadingDoc(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const formData = new FormData();
      formData.append('file', newDoc.file);
      formData.append('title', newDoc.title);
      formData.append('description', newDoc.description);
      formData.append('doc_type', newDoc.docType);
      
      const response = await fetch(`${API}/api/org/documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (response.ok) {
        toast.success('Document uploaded!');
        setNewDoc({ file: null, title: '', description: '', docType: 'reference' });
        loadDocuments();
      } else {
        toast.error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Upload failed');
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleConnectDatabase = async () => {
    if (!dbConfig.connection_string) {
      toast.error('Please provide a connection string');
      return;
    }
    
    setConnectingDb(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/org/database/connect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dbConfig)
      });
      
      const data = await response.json();
      if (data.status === 'connected') {
        toast.success('Database connected successfully!');
        loadDbStatus();
      } else {
        toast.error(data.message || 'Connection failed');
      }
    } catch (error) {
      console.error('DB connection error:', error);
      toast.error('Connection failed');
    } finally {
      setConnectingDb(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Organization Settings"
        subtitle="Manage your organization profile, documents, and integrations"
      />

      <div className="p-6">
        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="bg-zinc-800/50">
            <TabsTrigger value="profile" className="data-[state=active]:bg-blue-500/20">
              <Building2 className="w-4 h-4 mr-2" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="social" className="data-[state=active]:bg-blue-500/20">
              <Globe className="w-4 h-4 mr-2" />
              Social Media
            </TabsTrigger>
            <TabsTrigger value="documents" className="data-[state=active]:bg-blue-500/20">
              <FileText className="w-4 h-4 mr-2" />
              Documents
            </TabsTrigger>
            <TabsTrigger value="database" className="data-[state=active]:bg-blue-500/20">
              <Database className="w-4 h-4 mr-2" />
              Database
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <div className="glass-card p-6 space-y-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Building2 className="w-5 h-5 text-blue-400" />
                Organization Profile
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label>Organization Name</Label>
                  <Input
                    value={profile.name}
                    onChange={(e) => setProfile({...profile, name: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="Your Organization Name"
                  />
                </div>
                
                <div>
                  <Label>Website</Label>
                  <Input
                    value={profile.website}
                    onChange={(e) => setProfile({...profile, website: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="https://www.example.com"
                  />
                </div>
                
                <div>
                  <Label>Phone</Label>
                  <Input
                    value={profile.phone}
                    onChange={(e) => setProfile({...profile, phone: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="+263 XXX XXXX"
                  />
                </div>
                
                <div>
                  <Label>Address</Label>
                  <Input
                    value={profile.address}
                    onChange={(e) => setProfile({...profile, address: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="123 Main Street, City"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <Label>Description</Label>
                  <Textarea
                    value={profile.description}
                    onChange={(e) => setProfile({...profile, description: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10 min-h-[120px]"
                    placeholder="Describe your organization..."
                  />
                </div>
                
                <div className="md:col-span-2">
                  <Label>Logo URL</Label>
                  <Input
                    value={profile.logo_url}
                    onChange={(e) => setProfile({...profile, logo_url: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="https://example.com/logo.png"
                  />
                </div>
              </div>
              
              <Button onClick={handleSaveProfile} disabled={saving} className="bg-blue-500 hover:bg-blue-600">
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Save Profile
              </Button>
            </div>
          </TabsContent>

          {/* Social Media Tab */}
          <TabsContent value="social">
            <div className="glass-card p-6 space-y-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Globe className="w-5 h-5 text-violet-400" />
                Social Media Links
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label className="flex items-center gap-2">
                    <Facebook className="w-4 h-4 text-blue-500" />
                    Facebook
                  </Label>
                  <Input
                    value={profile.facebook}
                    onChange={(e) => setProfile({...profile, facebook: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="https://facebook.com/yourpage"
                  />
                </div>
                
                <div>
                  <Label className="flex items-center gap-2">
                    <Twitter className="w-4 h-4 text-sky-400" />
                    Twitter / X
                  </Label>
                  <Input
                    value={profile.twitter}
                    onChange={(e) => setProfile({...profile, twitter: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="https://twitter.com/yourhandle"
                  />
                </div>
                
                <div>
                  <Label className="flex items-center gap-2">
                    <Linkedin className="w-4 h-4 text-blue-600" />
                    LinkedIn
                  </Label>
                  <Input
                    value={profile.linkedin}
                    onChange={(e) => setProfile({...profile, linkedin: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="https://linkedin.com/company/yourcompany"
                  />
                </div>
                
                <div>
                  <Label className="flex items-center gap-2">
                    <Instagram className="w-4 h-4 text-pink-500" />
                    Instagram
                  </Label>
                  <Input
                    value={profile.instagram}
                    onChange={(e) => setProfile({...profile, instagram: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="https://instagram.com/yourhandle"
                  />
                </div>
              </div>
              
              <Button onClick={handleSaveProfile} disabled={saving} className="bg-violet-500 hover:bg-violet-600">
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Save Social Links
              </Button>
            </div>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents">
            <div className="space-y-6">
              <div className="glass-card p-6">
                <h2 className="text-xl font-semibold flex items-center gap-2 mb-4">
                  <Upload className="w-5 h-5 text-emerald-400" />
                  Upload Document
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <Label>Document Title</Label>
                    <Input
                      value={newDoc.title}
                      onChange={(e) => setNewDoc({...newDoc, title: e.target.value})}
                      className="mt-1 bg-zinc-800 border-white/10"
                      placeholder="Training Manual"
                    />
                  </div>
                  
                  <div>
                    <Label>Document Type</Label>
                    <select
                      value={newDoc.docType}
                      onChange={(e) => setNewDoc({...newDoc, docType: e.target.value})}
                      className="mt-1 w-full p-2 rounded-md bg-zinc-800 border border-white/10 text-white"
                    >
                      <option value="reference">Reference Material</option>
                      <option value="syllabus">Syllabus</option>
                      <option value="policy">Policy Document</option>
                      <option value="training">Training Material</option>
                    </select>
                  </div>
                  
                  <div className="md:col-span-2">
                    <Label>Description</Label>
                    <Input
                      value={newDoc.description}
                      onChange={(e) => setNewDoc({...newDoc, description: e.target.value})}
                      className="mt-1 bg-zinc-800 border-white/10"
                      placeholder="Brief description..."
                    />
                  </div>
                  
                  <div className="md:col-span-2">
                    <Label>File (PDF, DOCX, TXT)</Label>
                    <Input
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={(e) => setNewDoc({...newDoc, file: e.target.files[0]})}
                      className="mt-1 bg-zinc-800 border-white/10"
                    />
                  </div>
                </div>
                
                <Button onClick={handleUploadDocument} disabled={uploadingDoc} className="bg-emerald-500 hover:bg-emerald-600">
                  {uploadingDoc ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
                  Upload Document
                </Button>
              </div>
              
              <div className="glass-card p-6">
                <h2 className="text-xl font-semibold flex items-center gap-2 mb-4">
                  <FileText className="w-5 h-5 text-blue-400" />
                  Uploaded Documents ({documents.length})
                </h2>
                
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                      <div className="flex items-center gap-3">
                        <FileText className="w-8 h-8 text-blue-400" />
                        <div>
                          <p className="font-medium">{doc.title}</p>
                          <p className="text-sm text-zinc-500">{doc.doc_type} • {doc.filename}</p>
                        </div>
                      </div>
                      <span className="text-xs text-zinc-500">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  ))}
                  {documents.length === 0 && (
                    <p className="text-center text-zinc-500 py-8">No documents uploaded yet</p>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Database Tab */}
          <TabsContent value="database">
            <div className="glass-card p-6 space-y-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Database className="w-5 h-5 text-amber-400" />
                External Database Connection
              </h2>
              
              {dbStatus?.status === 'connected' ? (
                <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                  <p className="text-emerald-400 font-medium flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Database Connected
                  </p>
                  <p className="text-zinc-400 text-sm mt-1">
                    Type: {dbStatus.db_type} • Database: {dbStatus.db_name || 'N/A'}
                  </p>
                  <p className="text-zinc-500 text-xs mt-1">
                    Connected at: {new Date(dbStatus.connected_at).toLocaleString()}
                  </p>
                </div>
              ) : (
                <div className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                  <p className="text-zinc-400">No external database connected</p>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Database Type</Label>
                  <select
                    value={dbConfig.db_type}
                    onChange={(e) => setDbConfig({...dbConfig, db_type: e.target.value})}
                    className="mt-1 w-full p-2 rounded-md bg-zinc-800 border border-white/10 text-white"
                  >
                    <option value="mongodb">MongoDB</option>
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                  </select>
                </div>
                
                <div>
                  <Label>Database Name</Label>
                  <Input
                    value={dbConfig.db_name}
                    onChange={(e) => setDbConfig({...dbConfig, db_name: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="my_database"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <Label>Connection String</Label>
                  <Input
                    value={dbConfig.connection_string}
                    onChange={(e) => setDbConfig({...dbConfig, connection_string: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="mongodb://username:password@host:port"
                    type="password"
                  />
                </div>
                
                <div>
                  <Label>Collection/Table Name</Label>
                  <Input
                    value={dbConfig.collection_name}
                    onChange={(e) => setDbConfig({...dbConfig, collection_name: e.target.value})}
                    className="mt-1 bg-zinc-800 border-white/10"
                    placeholder="courses_data"
                  />
                </div>
              </div>
              
              <Button onClick={handleConnectDatabase} disabled={connectingDb} className="bg-amber-500 hover:bg-amber-600">
                {connectingDb ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Link className="w-4 h-4 mr-2" />}
                Connect Database
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
