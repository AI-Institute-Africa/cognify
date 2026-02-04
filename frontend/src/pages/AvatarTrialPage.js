import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { 
  Bot, ArrowLeft, Send, Mic, Volume2, User, Sparkles, 
  Loader2, MessageSquare, Play, Pause, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AVATAR_PRESETS = [
  { id: 'professor', name: 'Professor Ada', style: 'Academic & Detailed', image: '👩‍🏫', color: 'violet' },
  { id: 'mentor', name: 'Mentor Max', style: 'Friendly & Encouraging', image: '🧑‍💼', color: 'blue' },
  { id: 'tutor', name: 'Tutor Tina', style: 'Patient & Step-by-step', image: '👩‍🎓', color: 'emerald' },
  { id: 'coach', name: 'Coach Chris', style: 'Motivational & Direct', image: '🏋️', color: 'amber' },
];

const DEMO_TOPICS = [
  { id: 'math', title: 'Introduction to Algebra', subject: 'Mathematics' },
  { id: 'science', title: 'The Water Cycle', subject: 'Science' },
  { id: 'history', title: 'Ancient Civilizations', subject: 'History' },
  { id: 'language', title: 'English Grammar Basics', subject: 'Language Arts' },
];

export default function AvatarTrialPage() {
  const navigate = useNavigate();
  const [selectedAvatar, setSelectedAvatar] = useState(AVATAR_PRESETS[0]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState('select-avatar'); // select-avatar, select-topic, chat
  const [isSpeaking, setIsSpeaking] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startLesson = () => {
    if (!selectedTopic) {
      toast.error('Please select a topic first');
      return;
    }
    
    setStep('chat');
    setMessages([{
      role: 'assistant',
      content: `Hello! I'm ${selectedAvatar.name}, and I'll be your AI tutor today. We're going to learn about "${selectedTopic.title}" together. This is a demo of our Avatar-Based Learning feature.\n\nLet's start with a question: What do you already know about ${selectedTopic.title.toLowerCase()}?`,
      avatar: selectedAvatar
    }]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMsg = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/ai/avatar-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputMessage,
          avatar_name: selectedAvatar.name,
          avatar_style: selectedAvatar.style,
          topic: selectedTopic.title,
          subject: selectedTopic.subject,
          conversation_history: messages.slice(-6).map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          avatar: selectedAvatar
        }]);
      } else {
        // Fallback response
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Great question! In ${selectedTopic.title}, we learn about fundamental concepts that build upon each other. Let me explain this in a way that's easy to understand...\n\nWould you like me to go into more detail, or shall we try a practice question?`,
          avatar: selectedAvatar
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `I understand your question! Let me help you understand this better. ${selectedTopic.title} is a fascinating topic that connects to many real-world applications.\n\nWhat specific aspect would you like to explore?`,
        avatar: selectedAvatar
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const speakMessage = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-white">
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-40 bg-[#09090B]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button 
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </button>
            <div className="flex items-center gap-2">
              <Bot className="w-6 h-6 text-violet-400" />
              <span className="font-semibold">Avatar Learning Trial</span>
            </div>
            <Button onClick={() => navigate('/register')} className="bg-blue-500 hover:bg-blue-600">
              Create Account
            </Button>
          </div>
        </div>
      </div>

      <main className="pt-24 pb-12 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Step 1: Select Avatar */}
          {step === 'select-avatar' && (
            <div className="space-y-8">
              <div className="text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/20 border border-violet-500/30 mb-4">
                  <Sparkles className="w-4 h-4 text-violet-400" />
                  <span className="text-sm text-violet-400">Step 1 of 2</span>
                </div>
                <h1 className="text-3xl md:text-4xl font-bold mb-4">Choose Your AI Tutor</h1>
                <p className="text-zinc-400 max-w-xl mx-auto">
                  Select an avatar that matches your preferred learning style. Each tutor has a unique teaching approach.
                </p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {AVATAR_PRESETS.map((avatar) => (
                  <button
                    key={avatar.id}
                    onClick={() => setSelectedAvatar(avatar)}
                    className={`p-6 rounded-2xl border transition-all ${
                      selectedAvatar.id === avatar.id
                        ? `border-${avatar.color}-500 bg-${avatar.color}-500/10`
                        : 'border-white/10 hover:border-white/20 bg-zinc-900/50'
                    }`}
                  >
                    <div className="text-5xl mb-4">{avatar.image}</div>
                    <h3 className="font-semibold mb-1">{avatar.name}</h3>
                    <p className="text-xs text-zinc-400">{avatar.style}</p>
                  </button>
                ))}
              </div>

              <div className="text-center">
                <Button
                  size="lg"
                  onClick={() => setStep('select-topic')}
                  className="bg-violet-500 hover:bg-violet-600"
                >
                  Continue with {selectedAvatar.name}
                  <ChevronRight className="w-5 h-5 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: Select Topic */}
          {step === 'select-topic' && (
            <div className="space-y-8">
              <div className="text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/20 border border-blue-500/30 mb-4">
                  <Sparkles className="w-4 h-4 text-blue-400" />
                  <span className="text-sm text-blue-400">Step 2 of 2</span>
                </div>
                <h1 className="text-3xl md:text-4xl font-bold mb-4">Choose a Demo Topic</h1>
                <p className="text-zinc-400 max-w-xl mx-auto">
                  Select a topic to explore with {selectedAvatar.name}. This is a 5-minute demo experience.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {DEMO_TOPICS.map((topic) => (
                  <button
                    key={topic.id}
                    onClick={() => setSelectedTopic(topic)}
                    className={`p-6 rounded-2xl border text-left transition-all ${
                      selectedTopic?.id === topic.id
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-white/10 hover:border-white/20 bg-zinc-900/50'
                    }`}
                  >
                    <div className="text-xs text-zinc-500 mb-2">{topic.subject}</div>
                    <h3 className="text-lg font-semibold">{topic.title}</h3>
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-center gap-4">
                <Button
                  variant="outline"
                  onClick={() => setStep('select-avatar')}
                  className="border-white/10"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button
                  size="lg"
                  onClick={startLesson}
                  disabled={!selectedTopic}
                  className="bg-blue-500 hover:bg-blue-600"
                >
                  <Play className="w-5 h-5 mr-2" />
                  Start Learning
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Chat with Avatar */}
          {step === 'chat' && (
            <div className="space-y-6">
              {/* Avatar Info Bar */}
              <div className="flex items-center justify-between bg-zinc-900/50 border border-white/10 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <div className="text-4xl">{selectedAvatar.image}</div>
                  <div>
                    <h3 className="font-semibold">{selectedAvatar.name}</h3>
                    <p className="text-sm text-zinc-400">{selectedTopic.title}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setStep('select-topic');
                      setMessages([]);
                    }}
                    className="border-white/10"
                  >
                    Change Topic
                  </Button>
                  <Button
                    onClick={() => navigate('/register')}
                    size="sm"
                    className="bg-emerald-500 hover:bg-emerald-600"
                  >
                    Unlock Full Access
                  </Button>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="bg-zinc-900/30 border border-white/10 rounded-xl p-4 h-[400px] overflow-y-auto">
                <div className="space-y-4">
                  {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] ${msg.role === 'user' ? '' : 'flex gap-3'}`}>
                        {msg.role === 'assistant' && (
                          <div className="text-3xl flex-shrink-0">{msg.avatar?.image}</div>
                        )}
                        <div className={`p-4 rounded-2xl ${
                          msg.role === 'user'
                            ? 'bg-blue-500 text-white'
                            : 'bg-zinc-800'
                        }`}>
                          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                          {msg.role === 'assistant' && (
                            <button
                              onClick={() => speakMessage(msg.content)}
                              className="mt-2 text-xs text-zinc-400 hover:text-white flex items-center gap-1"
                            >
                              {isSpeaking ? <Pause className="w-3 h-3" /> : <Volume2 className="w-3 h-3" />}
                              {isSpeaking ? 'Stop' : 'Listen'}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex gap-3">
                      <div className="text-3xl">{selectedAvatar.image}</div>
                      <div className="bg-zinc-800 p-4 rounded-2xl">
                        <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              {/* Input */}
              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask a question or respond to your tutor..."
                  className="flex-1 bg-zinc-900/50 border-white/10 h-12"
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                />
                <Button
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="h-12 px-6 bg-blue-500 hover:bg-blue-600"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>

              {/* Demo Notice */}
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-center">
                <p className="text-sm text-amber-400">
                  This is a demo experience. Create an account to unlock full Avatar-Based Learning with voice cloning, custom avatars, and unlimited lessons.
                </p>
                <Button onClick={() => navigate('/register')} className="mt-3 bg-amber-500 hover:bg-amber-600">
                  Create Free Account
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
