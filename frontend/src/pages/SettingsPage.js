import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
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
  Sun
} from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { user } = useAuth();
  const [darkMode, setDarkMode] = useState(true);
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    grades: true,
    attendance: true,
    fees: true,
    announcements: true
  });
  const [saving, setSaving] = useState(false);

  const getInitials = (name) => {
    return name
      ?.split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'U';
  };

  const handleSave = async () => {
    setSaving(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    toast.success('Settings saved successfully!');
    setSaving(false);
  };

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
              <Button variant="outline" size="sm" className="border-white/10">
                <Camera className="w-4 h-4 mr-2" />
                Change Photo
              </Button>
            </div>
            
            <div className="flex-1 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input 
                    defaultValue={user?.full_name} 
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
              
              <div className="space-y-2">
                <Label>Role</Label>
                <Input 
                  defaultValue={user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)} 
                  disabled
                  className="bg-zinc-900/50 border-white/10 opacity-60 w-40"
                />
              </div>
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
                checked={notifications.email}
                onCheckedChange={(checked) => setNotifications({...notifications, email: checked})}
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
                checked={notifications.push}
                onCheckedChange={(checked) => setNotifications({...notifications, push: checked})}
              />
            </div>
            
            <Separator className="bg-white/5" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Grade Updates</p>
                <p className="text-sm text-zinc-500">Get notified when grades are posted</p>
              </div>
              <Switch 
                checked={notifications.grades}
                onCheckedChange={(checked) => setNotifications({...notifications, grades: checked})}
              />
            </div>
            
            <Separator className="bg-white/5" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Attendance Alerts</p>
                <p className="text-sm text-zinc-500">Get notified about attendance records</p>
              </div>
              <Switch 
                checked={notifications.attendance}
                onCheckedChange={(checked) => setNotifications({...notifications, attendance: checked})}
              />
            </div>
            
            <Separator className="bg-white/5" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Fee Reminders</p>
                <p className="text-sm text-zinc-500">Get reminded about pending fees</p>
              </div>
              <Switch 
                checked={notifications.fees}
                onCheckedChange={(checked) => setNotifications({...notifications, fees: checked})}
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
          
          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              {darkMode ? <Moon className="w-5 h-5 text-blue-400" /> : <Sun className="w-5 h-5 text-amber-400" />}
              <div>
                <p className="font-medium">Dark Mode</p>
                <p className="text-sm text-zinc-500">Use dark theme throughout the app</p>
              </div>
            </div>
            <Switch 
              checked={darkMode}
              onCheckedChange={setDarkMode}
              data-testid="dark-mode-switch"
            />
          </div>
        </div>
        
        {/* Security Section */}
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Shield className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold">Security</h2>
          </div>
          
          <div className="space-y-4">
            <Button variant="outline" className="border-white/10 w-full justify-start h-12">
              <Key className="w-4 h-4 mr-3" />
              Change Password
            </Button>
            
            <Button variant="outline" className="border-white/10 w-full justify-start h-12">
              <Shield className="w-4 h-4 mr-3" />
              Two-Factor Authentication
            </Button>
          </div>
        </div>
        
        {/* Save Button */}
        <div className="flex justify-end">
          <Button 
            onClick={handleSave}
            disabled={saving}
            data-testid="save-settings-btn"
            className="bg-blue-500 hover:bg-blue-600"
          >
            {saving ? (
              <>
                <svg className="animate-spin w-4 h-4 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
    </DashboardLayout>
  );
}
