import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { 
  updateUserProfileSettings, 
  uploadProfilePhoto, 
  updateNotificationSettings, 
  getUserSettings,
  updateAppearance,
  changePassword
} from '../services/api';
import { 
  User, 
  Bell, 
  Shield, 
  Palette, 
  Globe, 
  Key,
  Camera,
  Save,
  Moon,
  Sun,
  Loader2,
  Check,
  Eye,
  EyeOff,
  FileText,
  Award,
  Upload,
  Trash2,
  Download
} from 'lucide-react';
import { toast } from 'sonner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const { language, setLanguage, languages } = useLanguage();
  const fileInputRef = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [linkedinUrl, setLinkedinUrl] = useState(user?.linkedin_url || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [appearance, setAppearance] = useState('dark');
  
  const [notifications, setNotifications] = useState({
    email_notifications: true,
    push_notifications: true,
    grade_notifications: true,
    attendance_alerts: true,
    fee_reminders: true
  });
  
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showPasswords, setShowPasswords] = useState(false);
  
  // Document uploads state (for students)
  const [documents, setDocuments] = useState([]);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const docInputRef = useRef(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const settings = await getUserSettings();
      setNotifications({
        email_notifications: settings.email_notifications ?? true,
        push_notifications: settings.push_notifications ?? true,
        grade_notifications: settings.grade_notifications ?? true,
        attendance_alerts: settings.attendance_alerts ?? true,
        fee_reminders: settings.fee_reminders ?? true
      });
      setAppearance(settings.appearance || 'dark');
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (name) => {
    return name
      ?.split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'U';
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      await updateUserProfileSettings(fullName, phone, linkedinUrl, bio);
      if (refreshUser) await refreshUser();
      toast.success('Profile updated successfully!');
    } catch (error) {
      console.error('Save profile error:', error);
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
      toast.info('Uploading photo...');
      await uploadProfilePhoto(file);
      if (refreshUser) await refreshUser();
      toast.success('Photo uploaded successfully!');
    } catch (error) {
      console.error('Photo upload error:', error);
      toast.error('Failed to upload photo');
    }
  };

  const handleNotificationChange = async (key, value) => {
    const newNotifications = { ...notifications, [key]: value };
    setNotifications(newNotifications);
    
    try {
      await updateNotificationSettings(newNotifications);
      toast.success('Notification settings updated');
    } catch (error) {
      console.error('Notification update error:', error);
      // Revert
      setNotifications(notifications);
      toast.error('Failed to update notifications');
    }
  };

  const handleAppearanceChange = async (theme) => {
    setAppearance(theme);
    try {
      await updateAppearance(theme);
      toast.success('Appearance updated');
    } catch (error) {
      console.error('Appearance update error:', error);
      toast.error('Failed to update appearance');
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (passwordData.newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setSavingPassword(true);
    try {
      await changePassword(passwordData.currentPassword, passwordData.newPassword);
      toast.success('Password changed successfully!');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      console.error('Password change error:', error);
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setSavingPassword(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Settings"
        subtitle="Manage your account preferences"
      />
      
      <div className="p-8 max-w-4xl">
        {/* Profile Section */}
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <User className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold">Profile Information</h2>
          </div>
          
          <div className="flex flex-col md:flex-row gap-8">
            <div className="flex flex-col items-center gap-4">
              <Avatar className="w-24 h-24">
                <AvatarImage src={user?.profile_image} />
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-violet-500 text-white text-2xl">
                  {getInitials(user?.full_name)}
                </AvatarFallback>
              </Avatar>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handlePhotoUpload}
                accept="image/*"
                className="hidden"
              />
              <Button 
                variant="outline" 
                size="sm" 
                className="border-white/10"
                onClick={() => fileInputRef.current?.click()}
                data-testid="change-photo-btn"
              >
                <Camera className="w-4 h-4 mr-2" />
                Change Photo
              </Button>
            </div>
            
            <div className="flex-1 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input 
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="bg-zinc-900/50 border-white/10"
                    data-testid="settings-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input 
                    defaultValue={user?.email} 
                    disabled
                    className="bg-zinc-900/50 border-white/10 opacity-60"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input 
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+263..."
                    className="bg-zinc-900/50 border-white/10"
                  />
                </div>
                <div className="space-y-2">
                  <Label>LinkedIn Profile URL</Label>
                  <Input 
                    value={linkedinUrl}
                    onChange={(e) => setLinkedinUrl(e.target.value)}
                    placeholder="https://linkedin.com/in/yourprofile"
                    className="bg-zinc-900/50 border-white/10"
                    data-testid="linkedin-url-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Bio</Label>
                <textarea 
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Tell us about yourself..."
                  className="w-full p-3 rounded-md bg-zinc-900/50 border border-white/10 text-white placeholder:text-zinc-500 focus:outline-none focus:border-blue-500/50 min-h-[100px]"
                  data-testid="bio-input"
                />
              </div>

              <div className="flex items-center gap-4">
                <div className="space-y-2 flex-1">
                  <Label>Role</Label>
                  <Input 
                    defaultValue={user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)} 
                    disabled
                    className="bg-zinc-900/50 border-white/10 opacity-60"
                  />
                </div>
              </div>
              
              <Button 
                onClick={handleSaveProfile} 
                disabled={saving}
                className="bg-blue-500 hover:bg-blue-600"
                data-testid="save-profile-btn"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Profile
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
        
        {/* Notifications Section */}
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Bell className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold">Notification Preferences</h2>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Email Notifications</p>
                <p className="text-sm text-zinc-500">Receive notifications via email</p>
              </div>
              <Switch 
                checked={notifications.email_notifications}
                onCheckedChange={(checked) => handleNotificationChange('email_notifications', checked)}
                data-testid="email-notifications-switch"
              />
            </div>
            
            <Separator className="bg-white/5" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Push Notifications</p>
                <p className="text-sm text-zinc-500">Receive push notifications on your device</p>
              </div>
              <Switch 
                checked={notifications.push_notifications}
                onCheckedChange={(checked) => handleNotificationChange('push_notifications', checked)}
              />
            </div>
            
            <Separator className="bg-white/5" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Grade Notifications</p>
                <p className="text-sm text-zinc-500">Get notified when grades are posted</p>
              </div>
              <Switch 
                checked={notifications.grade_notifications}
                onCheckedChange={(checked) => handleNotificationChange('grade_notifications', checked)}
              />
            </div>
            
            <Separator className="bg-white/5" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Attendance Alerts</p>
                <p className="text-sm text-zinc-500">Get alerts about attendance</p>
              </div>
              <Switch 
                checked={notifications.attendance_alerts}
                onCheckedChange={(checked) => handleNotificationChange('attendance_alerts', checked)}
              />
            </div>
            
            <Separator className="bg-white/5" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Fee Reminders</p>
                <p className="text-sm text-zinc-500">Get reminders about fee payments</p>
              </div>
              <Switch 
                checked={notifications.fee_reminders}
                onCheckedChange={(checked) => handleNotificationChange('fee_reminders', checked)}
              />
            </div>
          </div>
        </div>
        
        {/* Appearance Section */}
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Palette className="w-5 h-5 text-violet-400" />
            <h2 className="text-lg font-semibold">Appearance</h2>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => handleAppearanceChange('dark')}
              className={`p-4 rounded-xl border-2 transition-all ${
                appearance === 'dark' 
                  ? 'border-blue-500 bg-blue-500/10' 
                  : 'border-white/10 hover:border-white/20'
              }`}
              data-testid="dark-mode-btn"
            >
              <Moon className="w-8 h-8 mx-auto mb-2 text-violet-400" />
              <p className="font-medium">Dark Mode</p>
              {appearance === 'dark' && <Check className="w-4 h-4 text-blue-400 mx-auto mt-2" />}
            </button>
            
            <button
              onClick={() => handleAppearanceChange('light')}
              className={`p-4 rounded-xl border-2 transition-all ${
                appearance === 'light' 
                  ? 'border-blue-500 bg-blue-500/10' 
                  : 'border-white/10 hover:border-white/20'
              }`}
              data-testid="light-mode-btn"
            >
              <Sun className="w-8 h-8 mx-auto mb-2 text-amber-400" />
              <p className="font-medium">Light Mode</p>
              {appearance === 'light' && <Check className="w-4 h-4 text-blue-400 mx-auto mt-2" />}
            </button>
          </div>
        </div>
        
        {/* Language Section */}
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Globe className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold">Language</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <Label>Platform Language</Label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="bg-zinc-900/50 border-white/10 mt-2 w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-800 border-white/10">
                  {languages.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      {lang.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-sm text-zinc-500 mt-2">
                This will change the language across all pages
              </p>
            </div>
          </div>
        </div>
        
        {/* Security Section */}
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Shield className="w-5 h-5 text-red-400" />
            <h2 className="text-lg font-semibold">Security</h2>
          </div>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Current Password</Label>
              <div className="relative">
                <Input 
                  type={showPasswords ? 'text' : 'password'}
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData({...passwordData, currentPassword: e.target.value})}
                  className="bg-zinc-900/50 border-white/10 pr-10"
                  data-testid="current-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords(!showPasswords)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500"
                >
                  {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>New Password</Label>
                <Input 
                  type={showPasswords ? 'text' : 'password'}
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})}
                  className="bg-zinc-900/50 border-white/10"
                  data-testid="new-password-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Confirm New Password</Label>
                <Input 
                  type={showPasswords ? 'text' : 'password'}
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                  className="bg-zinc-900/50 border-white/10"
                />
              </div>
            </div>
            
            <Button 
              onClick={handleChangePassword}
              disabled={savingPassword || !passwordData.currentPassword || !passwordData.newPassword}
              variant="outline"
              className="border-white/10"
              data-testid="change-password-btn"
            >
              {savingPassword ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Changing...
                </>
              ) : (
                <>
                  <Key className="w-4 h-4 mr-2" />
                  Change Password
                </>
              )}
            </Button>
            
            <Separator className="bg-white/5 my-4" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Two-Factor Authentication</p>
                <p className="text-sm text-zinc-500">Add an extra layer of security (Coming Soon)</p>
              </div>
              <Switch disabled />
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
