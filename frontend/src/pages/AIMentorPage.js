import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { mentorChat, getMentorProfile, updateMentorProfile, textToSpeech, analyzeLinkedInProfile } from '../services/api';
import { 
  Sparkles, 
  Send, 
  User, 
  Volume2, 
  VolumeX,
  Upload,
  Image,
  FileText,
  Mic,
  MicOff,
  Settings,
  Brain,
  Target,
  Lightbulb,
  Linkedin,
  RefreshCw,
  CheckCircle
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const learningStyles = [
  { value: 'visual', label: 'Visual - I learn best with images and diagrams' },
  { value: 'auditory', label: 'Auditory - I learn best by listening' },
  { value: 'kinesthetic', label: 'Kinesthetic - I learn best by doing' },
  { value: 'reading', label: 'Reading/Writing - I learn best through text' }
];

const paceOptions = [
  { value: 'slow', label: 'Slow - Take your time' },
  { value: 'moderate', label: 'Moderate - Balanced pace' },
  { value: 'fast', label: 'Fast - Quick learner' }
];

export default function AIMentorPage() {
  const { user } = useAuth();
  const { language, languages, changeLanguage, currentLanguage } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [analyzingLinkedin, setAnalyzingLinkedin] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    loadProfile();
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: getWelcomeMessage()
    }]);
  }, [user, language]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getWelcomeMessage = () => {
    const greetings = {
      en: `Hello ${user?.full_name?.split(' ')[0] || 'there'}! I'm your personal AI mentor. I remember everything about your learning journey and adapt to your style. What would you like to learn today?`,
      sn: `Mhoro ${user?.full_name?.split(' ')[0] || 'iwe'}! Ndini mudzidzisi wako weAI. Ndinoyeuka zvose nezverwendo rwako rwekudzidza. Unoda kudzidzei nhasi?`,
      nd: `Sawubona ${user?.full_name?.split(' ')[0] || 'wena'}! Ngingumfundisi wakho we-AI. Ngikhumbula konke ngokufunda kwakho. Ufuna ukufundani namuhla?`,
      sw: `Habari ${user?.full_name?.split(' ')[0] || 'wewe'}! Mimi ni mshauri wako wa AI. Ninakumbuka kila kitu kuhusu safari yako ya kujifunza. Unataka kujifunza nini leo?`,
      zu: `Sawubona ${user?.full_name?.split(' ')[0] || 'wena'}! Ngingumfundisi wakho we-AI. Ngikhumbula konke ngokufunda kwakho. Ufuna ukufundani namuhla?`
    };
    return greetings[language] || greetings.en;
  };

  const loadProfile = async () => {
    try {
      const data = await getMentorProfile();
      setProfile(data);
    } catch (error) {
      console.error('Failed to load mentor profile:', error);
    }
  };

  const handleAnalyzeLinkedIn = async () => {
    setAnalyzingLinkedin(true);
    try {
      const result = await analyzeLinkedInProfile();
      if (result.success) {
        toast.success('LinkedIn profile analyzed! Your AI mentor now has personalized insights.');
        await loadProfile();
        // Add a message to the chat about the new insights
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: `I've analyzed your LinkedIn profile and updated your learner profile! Here's what I learned:\n\n**Your Strengths:** ${result.profile?.strengths?.join(', ') || 'Analyzing...'}\n\n**Recommended Topics:** ${result.profile?.recommended_topics?.join(', ') || 'Analyzing...'}\n\n**Career Insight:** ${result.profile?.career_insights || 'Ready to help you grow!'}\n\nI'll now use these insights to provide more personalized learning recommendations. What would you like to learn today?`
        }]);
      } else {
        toast.error(result.message || 'Failed to analyze LinkedIn profile');
      }
    } catch (error) {
      toast.error('Failed to analyze LinkedIn profile');
    } finally {
      setAnalyzingLinkedin(false);
    }
  };

  // File Upload Handler
  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    setUploadingFile(true);
    
    // Add user message showing the file
    const fileMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: `📎 Uploaded: ${file.name}${input.trim() ? `\n\n${input.trim()}` : '\n\nPlease analyze this file.'}`,
      hasFile: true,
      fileName: file.name
    };
    setMessages(prev => [...prev, fileMessage]);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('question', input.trim() || 'Please analyze this file and provide key insights.');
      
      const token = localStorage.getItem('cognify_token');
      const API = process.env.REACT_APP_BACKEND_URL;
      
      const response = await fetch(`${API}/api/mentor/upload-document`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (!response.ok) throw new Error('Upload failed');
      
      const data = await response.json();
      
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response
      }]);
      
      setInput('');
      toast.success('File analyzed successfully!');
    } catch (error) {
      console.error('File upload error:', error);
      toast.error('Failed to analyze file. Please try again.');
      // Remove the user message on error
      setMessages(prev => prev.filter(m => m.id !== fileMessage.id));
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Voice Recording Handler - Using Web Speech API (free, browser-native)
  const startRecording = async () => {
    try {
      // Check for browser support
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        toast.error('Speech recognition not supported in this browser. Try Chrome or Edge.');
        return;
      }
      
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = language || 'en-US';
      
      mediaRecorderRef.current = recognition;
      
      recognition.onstart = () => {
        setIsRecording(true);
        toast.success('Listening... Speak now');
      };
      
      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        
        // Update input with interim results
        setInput(transcript);
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
        if (event.error === 'no-speech') {
          toast.info('No speech detected. Try again.');
        } else if (event.error === 'not-allowed') {
          toast.error('Microphone access denied. Please allow microphone access.');
        } else {
          toast.error(`Speech recognition error: ${event.error}`);
        }
      };
      
      recognition.onend = () => {
        setIsRecording(false);
        toast.info('Voice input complete');
      };
      
      recognition.start();
    } catch (error) {
      console.error('Recording error:', error);
      toast.error('Could not start voice recognition. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.error('Stop recording error:', e);
      }
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleSend = async (text = input) => {
    if (!text.trim() || loading) return;
    
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      const response = await mentorChat(text.trim(), null, language, audioEnabled);
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        audioUrl: response.audio_url
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Auto-play audio if enabled
      if (response.audio_url && audioEnabled && audioRef.current) {
        audioRef.current.src = response.audio_url;
        audioRef.current.play().catch(() => {});
      }
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to get response');
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I encountered an error. Please try again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleProfileUpdate = async (updates) => {
    try {
      await updateMentorProfile(updates);
      await loadProfile();
      toast.success('Profile updated!');
    } catch (error) {
      toast.error('Failed to update profile');
    }
  };

  const playAudio = async (text) => {
    try {
      // First try ElevenLabs TTS
      const response = await textToSpeech(text, profile?.voice_id, language);
      if (response.audio_url && audioRef.current) {
        audioRef.current.src = response.audio_url;
        await audioRef.current.play();
        return;
      }
    } catch (error) {
      console.error('Primary TTS failed:', error);
      
      // Fallback to browser's built-in speech synthesis
      try {
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = language || 'en-US';
          utterance.rate = 0.9;
          window.speechSynthesis.speak(utterance);
          toast.info('Using browser voice (server TTS unavailable)');
          return;
        }
      } catch (fallbackError) {
        console.error('Fallback TTS failed:', fallbackError);
      }
      
      toast.error('Audio playback unavailable. Try enabling browser speech synthesis.');
    }
  };

  const suggestedPrompts = [
    { icon: Brain, text: "Help me understand my learning progress" },
    { icon: Target, text: "What should I focus on next?" },
    { icon: Lightbulb, text: "Give me a study strategy for my weak areas" }
  ];

  return (
    <DashboardLayout>
      <Header 
        title="AI Personal Mentor"
        subtitle="Your lifelong learning companion"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Top Bar */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <Badge className="bg-gradient-to-r from-violet-500 to-purple-500 text-white">
                <Sparkles className="w-3 h-3 mr-1" />
                AI Mentor
              </Badge>
              
              {/* Language Selector */}
              <Select value={language} onValueChange={changeLanguage}>
                <SelectTrigger className="w-[140px] h-9 bg-zinc-900/50 border-white/10">
                  <SelectValue>
                    <span className="flex items-center gap-2">
                      <span>{currentLanguage.flag}</span>
                      <span>{currentLanguage.native}</span>
                    </span>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10">
                  {languages.map(lang => (
                    <SelectItem key={lang.code} value={lang.code}>
                      <span className="flex items-center gap-2">
                        <span>{lang.flag}</span>
                        <span>{lang.native}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center gap-2">
              {/* LinkedIn Analysis Button */}
              {profile?.linkedin_profile ? (
                <Button
                  variant="outline"
                  size="sm"
                  className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 gap-2"
                  disabled
                >
                  <CheckCircle className="w-4 h-4" />
                  LinkedIn Connected
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAnalyzeLinkedIn}
                  disabled={analyzingLinkedin}
                  className="border-blue-500/30 bg-blue-500/10 text-blue-400 gap-2 hover:bg-blue-500/20"
                  data-testid="analyze-linkedin-btn"
                >
                  {analyzingLinkedin ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Linkedin className="w-4 h-4" />
                      Analyze LinkedIn
                    </>
                  )}
                </Button>
              )}
              
              {/* Audio Toggle */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAudioEnabled(!audioEnabled)}
                className={`border-white/10 ${audioEnabled ? 'bg-blue-500/20 text-blue-400' : ''}`}
              >
                {audioEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </Button>
              
              {/* Settings */}
              <Dialog open={showSettings} onOpenChange={setShowSettings}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="border-white/10">
                    <Settings className="w-4 h-4" />
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10 max-w-md">
                  <DialogHeader>
                    <DialogTitle>Mentor Settings</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Customize how your AI mentor teaches you
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Learning Style</Label>
                      <Select 
                        value={profile?.learning_style || 'visual'}
                        onValueChange={(value) => handleProfileUpdate({ learning_style: value })}
                      >
                        <SelectTrigger className="bg-zinc-800 border-white/10">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10">
                          {learningStyles.map(style => (
                            <SelectItem key={style.value} value={style.value}>{style.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Learning Pace</Label>
                      <Select 
                        value={profile?.preferred_pace || 'moderate'}
                        onValueChange={(value) => handleProfileUpdate({ preferred_pace: value })}
                      >
                        <SelectTrigger className="bg-zinc-800 border-white/10">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10">
                          {paceOptions.map(pace => (
                            <SelectItem key={pace.value} value={pace.value}>{pace.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Preferred Language</Label>
                      <Select 
                        value={profile?.preferred_language || 'en'}
                        onValueChange={(value) => handleProfileUpdate({ preferred_language: value })}
                      >
                        <SelectTrigger className="bg-zinc-800 border-white/10">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10">
                          {languages.map(lang => (
                            <SelectItem key={lang.code} value={lang.code}>
                              {lang.flag} {lang.native}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Chat Container */}
          <div className="glass-card min-h-[600px] flex flex-col">
            {/* Messages Area */}
            <div className="flex-1 p-6 overflow-y-auto space-y-6 max-h-[500px]">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-4 animate-fadeIn ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user' 
                      ? 'bg-blue-500' 
                      : 'bg-gradient-to-br from-violet-500 to-purple-600'
                  }`}>
                    {message.role === 'user' ? (
                      <User className="w-5 h-5 text-white" />
                    ) : (
                      <Sparkles className="w-5 h-5 text-white" />
                    )}
                  </div>
                  
                  <div className={`flex-1 max-w-[80%] ${message.role === 'user' ? 'text-right' : ''}`}>
                    <div className={`inline-block p-4 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-zinc-800/80 text-zinc-100'
                    }`}>
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                      
                      {/* Audio playback button for assistant messages */}
                      {message.role === 'assistant' && (
                        <button
                          onClick={() => playAudio(message.content)}
                          className="mt-2 p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                          title="Play audio"
                        >
                          <Volume2 className="w-4 h-4 text-zinc-400" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-zinc-800/80 p-4 rounded-2xl">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
            
            {/* Suggested Prompts */}
            {messages.length === 1 && (
              <div className="px-6 pb-4">
                <p className="text-sm text-zinc-500 mb-3">Suggested topics:</p>
                <div className="flex flex-wrap gap-2">
                  {suggestedPrompts.map((prompt, index) => (
                    <button
                      key={index}
                      onClick={() => handleSend(prompt.text)}
                      data-testid={`mentor-prompt-${index}`}
                      className="flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-800/50 hover:bg-zinc-800 border border-white/5 hover:border-white/10 transition-all text-sm"
                    >
                      <prompt.icon className="w-4 h-4 text-violet-400" />
                      {prompt.text}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Input Area */}
            <div className="p-4 border-t border-white/5">
              <div className="flex gap-3">
                {/* File Upload */}
                <label className={`p-3 rounded-xl cursor-pointer transition-colors border border-white/5 ${uploadingFile ? 'bg-blue-500/20 animate-pulse' : 'bg-zinc-800/50 hover:bg-zinc-800'}`}>
                  {uploadingFile ? (
                    <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
                  ) : (
                    <Upload className="w-5 h-5 text-zinc-400" />
                  )}
                  <input 
                    ref={fileInputRef}
                    type="file" 
                    className="hidden" 
                    accept="image/*,.pdf,.txt,.doc,.docx,.json,.csv"
                    onChange={handleFileUpload}
                    disabled={uploadingFile || loading}
                  />
                </label>
                
                {/* Voice Input */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleRecording}
                  disabled={loading || uploadingFile}
                  className={`p-3 rounded-xl border border-white/5 ${isRecording ? 'bg-red-500/20 text-red-400 animate-pulse' : 'bg-zinc-800/50'}`}
                >
                  {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5 text-zinc-400" />}
                </Button>
                
                {/* Text Input */}
                <div className="flex-1">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={uploadingFile ? "Processing file..." : isRecording ? "Listening..." : "Ask your mentor anything..."}
                    data-testid="mentor-chat-input"
                    className="min-h-[56px] max-h-[120px] bg-zinc-800/50 border-white/10 resize-none"
                    disabled={loading || uploadingFile}
                  />
                </div>
                
                {/* Send Button */}
                <Button
                  onClick={() => handleSend()}
                  disabled={!input.trim() || loading || uploadingFile}
                  data-testid="mentor-send-btn"
                  className="h-14 w-14 bg-violet-500 hover:bg-violet-600 p-0"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>
              
              <p className="text-xs text-zinc-600 mt-2 text-center">
                Upload files, record voice, or type • Your mentor remembers everything
              </p>
            </div>
          </div>
          
          {/* Hidden audio element */}
          <audio ref={audioRef} className="hidden" />
        </div>
      </div>
    </DashboardLayout>
  );
}
