import React, { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  User, Upload, Sparkles, Check, Camera, Mic, Volume2, 
  Loader2, Play, Pause, RefreshCw
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';

const PRESET_AVATARS = [
  { id: 'teacher-1', name: 'Professor Ada', style: 'professional', image: 'https://api.dicebear.com/7.x/personas/svg?seed=Ada&backgroundColor=b6e3f4', voice: 'nova' },
  { id: 'teacher-2', name: 'Dr. Kwame', style: 'friendly', image: 'https://api.dicebear.com/7.x/personas/svg?seed=Kwame&backgroundColor=c0aede', voice: 'onyx' },
  { id: 'teacher-3', name: 'Ms. Amara', style: 'encouraging', image: 'https://api.dicebear.com/7.x/personas/svg?seed=Amara&backgroundColor=ffd5dc', voice: 'shimmer' },
  { id: 'teacher-4', name: 'Coach Zuri', style: 'motivational', image: 'https://api.dicebear.com/7.x/personas/svg?seed=Zuri&backgroundColor=d1d4f9', voice: 'echo' },
  { id: 'teacher-5', name: 'Mentor Thabo', style: 'wise', image: 'https://api.dicebear.com/7.x/personas/svg?seed=Thabo&backgroundColor=ffdfbf', voice: 'fable' },
  { id: 'teacher-6', name: 'Guide Naledi', style: 'calm', image: 'https://api.dicebear.com/7.x/personas/svg?seed=Naledi&backgroundColor=c1f0c1', voice: 'alloy' },
];

const AI_STYLES = [
  { id: 'professional', label: 'Professional', description: 'Formal and academic approach' },
  { id: 'friendly', label: 'Friendly', description: 'Warm and approachable' },
  { id: 'encouraging', label: 'Encouraging', description: 'Supportive and motivating' },
  { id: 'strict', label: 'Strict', description: 'Disciplined and focused' },
  { id: 'humorous', label: 'Humorous', description: 'Light-hearted with jokes' },
];

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function AvatarSettingsPage() {
  const { user } = useAuth();
  const [selectedAvatar, setSelectedAvatar] = useState(PRESET_AVATARS[0]);
  const [customAvatar, setCustomAvatar] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [generationPrompt, setGenerationPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('friendly');
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedImage(e.target.result);
        setCustomAvatar({
          id: 'custom',
          name: 'My Avatar',
          style: selectedStyle,
          image: e.target.result,
          voice: 'nova'
        });
        toast.success('Avatar uploaded successfully!');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerateAvatar = async () => {
    if (!generationPrompt.trim()) {
      toast.error('Please describe your avatar');
      return;
    }

    setGenerating(true);
    try {
      const token = localStorage.getItem('eduos_token');
      const response = await fetch(`${API_URL}/api/advanced/avatar/generate?prompt=${encodeURIComponent(generationPrompt)}&style=professional educator`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.image_url) {
          setCustomAvatar({
            id: 'ai-generated',
            name: 'AI Tutor',
            style: selectedStyle,
            image: data.image_url,
            voice: 'nova'
          });
          toast.success('Avatar generated successfully!');
          setShowGenerateDialog(false);
        }
      } else {
        // Use a placeholder for demo
        setCustomAvatar({
          id: 'ai-generated',
          name: 'AI Tutor',
          style: selectedStyle,
          image: `https://api.dicebear.com/7.x/personas/svg?seed=${generationPrompt}&backgroundColor=b6e3f4`,
          voice: 'nova'
        });
        toast.success('Avatar created!');
        setShowGenerateDialog(false);
      }
    } catch (error) {
      console.error('Avatar generation error:', error);
      // Fallback to dicebear
      setCustomAvatar({
        id: 'ai-generated',
        name: 'AI Tutor',
        style: selectedStyle,
        image: `https://api.dicebear.com/7.x/personas/svg?seed=${generationPrompt}&backgroundColor=b6e3f4`,
        voice: 'nova'
      });
      toast.success('Avatar created!');
      setShowGenerateDialog(false);
    } finally {
      setGenerating(false);
    }
  };

  const handleTestVoice = async () => {
    setIsSpeaking(true);
    try {
      const token = localStorage.getItem('eduos_token');
      const testText = `Hello! I'm ${selectedAvatar?.name || 'your AI tutor'}. I'll be guiding you through your learning journey. Let's achieve great things together!`;
      
      const response = await fetch(`${API_URL}/api/advanced/tts?text=${encodeURIComponent(testText)}&voice=${selectedAvatar?.voice || 'nova'}&speed=1.0`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.audio_url) {
          const audio = new Audio(data.audio_url);
          audio.play();
          audio.onended = () => setIsSpeaking(false);
          setAudioUrl(data.audio_url);
        }
      } else {
        toast.info('Voice preview will be available with API key');
        setIsSpeaking(false);
      }
    } catch (error) {
      console.error('TTS error:', error);
      toast.info('Voice preview will be available with API key');
      setIsSpeaking(false);
    }
  };

  const handleSaveAvatar = () => {
    const avatarToSave = customAvatar || selectedAvatar;
    localStorage.setItem('eduos_avatar', JSON.stringify(avatarToSave));
    localStorage.setItem('eduos_tutor_style', selectedStyle);
    toast.success('Avatar settings saved!');
  };

  const currentAvatar = customAvatar || selectedAvatar;

  return (
    <DashboardLayout>
      <Header 
        title="Avatar & Tutor Settings"
        subtitle="Customize your AI learning companion"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Current Avatar Preview */}
          <div className="glass-card p-8 mb-8 text-center">
            <div className="relative inline-block">
              <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-blue-500/30 mx-auto">
                <img 
                  src={currentAvatar?.image} 
                  alt={currentAvatar?.name}
                  className="w-full h-full object-cover"
                />
              </div>
              {customAvatar && (
                <div className="absolute -bottom-1 -right-1 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center border-2 border-zinc-900">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
            <h3 className="text-xl font-bold mt-4">{currentAvatar?.name}</h3>
            <p className="text-zinc-400 capitalize">{currentAvatar?.style} Style</p>
            
            <div className="flex justify-center gap-3 mt-6">
              <Button 
                variant="outline" 
                onClick={handleTestVoice}
                disabled={isSpeaking}
                className="border-white/10"
              >
                {isSpeaking ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Speaking...
                  </>
                ) : (
                  <>
                    <Volume2 className="w-4 h-4 mr-2" />
                    Test Voice
                  </>
                )}
              </Button>
              <Button onClick={handleSaveAvatar} className="bg-blue-500 hover:bg-blue-600">
                <Check className="w-4 h-4 mr-2" />
                Save Settings
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Preset Avatars */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-blue-400" />
                Choose a Pre-made Avatar
              </h3>
              <div className="grid grid-cols-3 gap-4">
                {PRESET_AVATARS.map((avatar) => (
                  <button
                    key={avatar.id}
                    onClick={() => {
                      setSelectedAvatar(avatar);
                      setCustomAvatar(null);
                    }}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      selectedAvatar?.id === avatar.id && !customAvatar
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-white/10 hover:border-white/20'
                    }`}
                    data-testid={`avatar-${avatar.id}`}
                  >
                    <img 
                      src={avatar.image} 
                      alt={avatar.name}
                      className="w-16 h-16 rounded-full mx-auto mb-2"
                    />
                    <p className="text-sm font-medium truncate">{avatar.name}</p>
                    <p className="text-xs text-zinc-500 capitalize">{avatar.style}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Avatar */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-violet-400" />
                Create Custom Avatar
              </h3>
              
              <div className="space-y-4">
                {/* Upload Option */}
                <div>
                  <Label className="text-sm text-zinc-400 mb-2 block">Upload Your Own Image</Label>
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={handleFileUpload}
                  />
                  <Button 
                    variant="outline" 
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full border-dashed border-white/20 h-24 flex-col gap-2"
                    data-testid="upload-avatar-btn"
                  >
                    <Upload className="w-6 h-6" />
                    <span>Click to upload image</span>
                  </Button>
                </div>

                {/* AI Generate Option */}
                <div>
                  <Label className="text-sm text-zinc-400 mb-2 block">Or Generate with AI</Label>
                  <Button 
                    variant="outline" 
                    onClick={() => setShowGenerateDialog(true)}
                    className="w-full border-violet-500/30 text-violet-400 hover:bg-violet-500/10"
                    data-testid="generate-avatar-btn"
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate AI Avatar
                  </Button>
                </div>

                {/* Uploaded/Generated Preview */}
                {customAvatar && (
                  <div className="p-4 bg-zinc-800/50 rounded-xl">
                    <div className="flex items-center gap-4">
                      <img 
                        src={customAvatar.image} 
                        alt="Custom avatar"
                        className="w-16 h-16 rounded-full object-cover"
                      />
                      <div>
                        <Input
                          value={customAvatar.name}
                          onChange={(e) => setCustomAvatar({...customAvatar, name: e.target.value})}
                          className="bg-zinc-700 border-white/10 mb-2"
                          placeholder="Avatar name"
                        />
                        <p className="text-xs text-green-400">✓ Custom avatar ready</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Tutor Style Selection */}
          <div className="glass-card p-6 mt-8">
            <h3 className="text-lg font-semibold mb-4">Teaching Style</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {AI_STYLES.map((style) => (
                <button
                  key={style.id}
                  onClick={() => setSelectedStyle(style.id)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    selectedStyle === style.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-white/10 hover:border-white/20'
                  }`}
                  data-testid={`style-${style.id}`}
                >
                  <p className="font-medium">{style.label}</p>
                  <p className="text-xs text-zinc-500 mt-1">{style.description}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* AI Generation Dialog */}
      <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <DialogContent className="bg-zinc-900 border-white/10">
          <DialogHeader>
            <DialogTitle>Generate AI Avatar</DialogTitle>
            <DialogDescription className="text-zinc-500">
              Describe your ideal AI tutor and we'll create it for you
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label>Describe your avatar</Label>
              <Textarea
                value={generationPrompt}
                onChange={(e) => setGenerationPrompt(e.target.value)}
                placeholder="E.g., A wise African grandmother with kind eyes and a warm smile, wearing traditional attire..."
                className="bg-zinc-800 border-white/10 min-h-[100px] mt-2"
              />
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setShowGenerateDialog(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleGenerateAvatar}
                disabled={generating}
                className="bg-violet-500 hover:bg-violet-600"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
