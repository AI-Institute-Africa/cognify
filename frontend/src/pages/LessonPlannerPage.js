import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { lessonPlanner } from '../services/api';
import { Sparkles, Send, User, BookOpen, FileText, ListChecks, HelpCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';

const suggestedPrompts = [
  { icon: FileText, text: "Create a lesson plan for teaching algebra to 10th graders" },
  { icon: ListChecks, text: "Generate 10 quiz questions about photosynthesis" },
  { icon: BookOpen, text: "Suggest engaging activities for teaching history" },
  { icon: HelpCircle, text: "How can I explain complex concepts simply?" }
];

export default function LessonPlannerPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: `Hello ${user?.full_name?.split(' ')[0] || 'Teacher'}! I'm your AI Lesson Planner. I can help you create lesson plans, generate quizzes and assessments, suggest teaching strategies, and provide educational resources. How can I assist you today?`
    }]);
  }, [user]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
      const response = await lessonPlanner(text.trim());
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to get response. Please try again.');
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I encountered an error. Please try again or rephrase your request."
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

  return (
    <DashboardLayout>
      <Header 
        title="AI Lesson Planner"
        subtitle="Create lessons, quizzes, and teaching materials"
      />
      
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
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
                      : 'bg-gradient-to-br from-emerald-500 to-teal-600'
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
                    </div>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
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
                <p className="text-sm text-zinc-500 mb-3">Suggested prompts:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {suggestedPrompts.map((q, index) => (
                    <button
                      key={index}
                      onClick={() => handleSend(q.text)}
                      data-testid={`suggested-prompt-${index}`}
                      className="flex items-center gap-3 p-3 rounded-xl bg-zinc-800/50 hover:bg-zinc-800 border border-white/5 hover:border-white/10 transition-all text-left group"
                    >
                      <div className="p-2 rounded-lg bg-emerald-500/20 group-hover:bg-emerald-500/30 transition-colors">
                        <q.icon className="w-4 h-4 text-emerald-400" />
                      </div>
                      <span className="text-sm text-zinc-300">{q.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Input Area */}
            <div className="p-4 border-t border-white/5">
              <div className="flex gap-3">
                <div className="flex-1">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask me to create lesson plans, quizzes, or teaching materials..."
                    data-testid="lesson-chat-input"
                    className="min-h-[56px] max-h-[120px] bg-zinc-800/50 border-white/10 resize-none"
                    disabled={loading}
                  />
                </div>
                <Button
                  onClick={() => handleSend()}
                  disabled={!input.trim() || loading}
                  data-testid="lesson-chat-send-btn"
                  className="h-14 w-14 bg-emerald-500 hover:bg-emerald-600 p-0"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>
              <p className="text-xs text-zinc-600 mt-2 text-center">
                AI-powered lesson planning assistant. Review all generated content before use.
              </p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
