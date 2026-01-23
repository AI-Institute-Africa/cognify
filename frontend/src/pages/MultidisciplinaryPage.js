import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { generateMultidisciplinaryLesson } from '../services/api';
import { 
  Layers,
  Brain,
  BookOpen,
  RefreshCw,
  CheckCircle,
  ArrowRight,
  Link,
  Sparkles,
  Target,
  Clock,
  Plus,
  X
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const AVAILABLE_SUBJECTS = [
  'Mathematics', 'Physics', 'Chemistry', 'Biology', 'History', 
  'Geography', 'Economics', 'Literature', 'Computer Science', 
  'Philosophy', 'Psychology', 'Art', 'Music', 'Environmental Science'
];

export default function MultidisciplinaryPage() {
  const { user } = useAuth();
  const [topic, setTopic] = useState('');
  const [selectedSubjects, setSelectedSubjects] = useState([]);
  const [duration, setDuration] = useState(45);
  const [loading, setLoading] = useState(false);
  const [lesson, setLesson] = useState(null);

  const toggleSubject = (subject) => {
    if (selectedSubjects.includes(subject)) {
      setSelectedSubjects(selectedSubjects.filter(s => s !== subject));
    } else if (selectedSubjects.length < 5) {
      setSelectedSubjects([...selectedSubjects, subject]);
    } else {
      toast.error('Maximum 5 subjects allowed');
    }
  };

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast.error('Please enter a topic');
      return;
    }
    if (selectedSubjects.length < 2) {
      toast.error('Please select at least 2 subjects');
      return;
    }

    setLoading(true);
    try {
      const result = await generateMultidisciplinaryLesson(topic, selectedSubjects, duration);
      setLesson(result);
      toast.success('Multi-disciplinary lesson generated!');
    } catch (error) {
      console.error('Generation failed:', error);
      toast.error('Failed to generate lesson');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <Header 
        title="Multi-Disciplinary Learning"
        subtitle="Combine subjects to see the bigger picture"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border-indigo-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                <Layers className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Learn Without Boundaries</h3>
                <p className="text-zinc-400 text-sm">
                  Real-world problems don't fit into single subjects. Combine History, Geography, Science, 
                  and more to understand concepts from multiple perspectives. The AI creates connections you never saw.
                </p>
              </div>
            </div>
          </div>

          {!lesson ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Configuration */}
              <div className="glass-card p-6 space-y-6">
                <h3 className="font-semibold flex items-center gap-2">
                  <Brain className="w-5 h-5 text-indigo-400" />
                  Configure Your Lesson
                </h3>

                <div className="space-y-2">
                  <Label>Topic to Explore</Label>
                  <Input
                    placeholder="e.g., Climate Change, Industrial Revolution, Human Body"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="bg-zinc-800 border-white/10"
                    data-testid="topic-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Duration (minutes)</Label>
                  <div className="flex gap-2">
                    {[30, 45, 60, 90].map((mins) => (
                      <button
                        key={mins}
                        onClick={() => setDuration(mins)}
                        className={`flex-1 py-2 rounded-lg border transition-all ${
                          duration === mins
                            ? 'bg-indigo-500/20 border-indigo-500'
                            : 'bg-zinc-800/50 border-white/5 hover:border-white/10'
                        }`}
                      >
                        {mins}min
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Select Subjects (2-5)</Label>
                  <div className="flex flex-wrap gap-2">
                    {selectedSubjects.map((subject) => (
                      <Badge 
                        key={subject} 
                        className="bg-indigo-500/20 text-indigo-300 cursor-pointer"
                        onClick={() => toggleSubject(subject)}
                      >
                        {subject}
                        <X className="w-3 h-3 ml-1" />
                      </Badge>
                    ))}
                  </div>
                </div>

                <Button
                  onClick={handleGenerate}
                  disabled={!topic.trim() || selectedSubjects.length < 2 || loading}
                  className="w-full bg-indigo-500 hover:bg-indigo-600"
                  data-testid="generate-lesson-btn"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Multi-Subject Lesson
                    </>
                  )}
                </Button>
              </div>

              {/* Subject Selection */}
              <div className="glass-card p-6">
                <h3 className="font-semibold flex items-center gap-2 mb-4">
                  <BookOpen className="w-5 h-5 text-indigo-400" />
                  Available Subjects
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {AVAILABLE_SUBJECTS.map((subject) => (
                    <button
                      key={subject}
                      onClick={() => toggleSubject(subject)}
                      className={`p-3 rounded-lg border text-left text-sm transition-all ${
                        selectedSubjects.includes(subject)
                          ? 'bg-indigo-500/20 border-indigo-500'
                          : 'bg-zinc-800/50 border-white/5 hover:border-white/10'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span>{subject}</span>
                        {selectedSubjects.includes(subject) && (
                          <CheckCircle className="w-4 h-4 text-indigo-400" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Lesson Header */}
              <div className="glass-card p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <Badge className="mb-2 bg-indigo-500/20 text-indigo-400">Multi-Disciplinary</Badge>
                    <h2 className="text-2xl font-bold">{lesson.title || topic}</h2>
                    <p className="text-zinc-500 mt-1">
                      {lesson.central_theme || 'Exploring connections across disciplines'}
                    </p>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {selectedSubjects.map((subject, i) => (
                        <Badge key={i} variant="outline" className="border-indigo-500/30 text-indigo-300">
                          {subject}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => setLesson(null)}
                    className="border-white/10"
                  >
                    New Lesson
                  </Button>
                </div>
              </div>

              {/* Discipline Contributions */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {lesson.disciplines?.map((discipline, index) => (
                  <div key={index} className="glass-card p-5">
                    <h4 className="font-semibold text-lg mb-2">{discipline.subject}</h4>
                    <p className="text-sm text-zinc-400 mb-3">{discipline.contribution}</p>
                    {discipline.key_concepts && (
                      <div className="space-y-1">
                        {discipline.key_concepts.map((concept, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm">
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                            {concept}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Connections */}
              {lesson.connections?.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <Link className="w-5 h-5 text-violet-400" />
                    Cross-Discipline Connections
                  </h3>
                  <div className="space-y-3">
                    {lesson.connections.map((connection, index) => (
                      <div key={index} className="flex items-center gap-4 p-3 rounded-lg bg-zinc-800/50">
                        <Badge className="bg-blue-500/20 text-blue-300">{connection.from}</Badge>
                        <ArrowRight className="w-4 h-4 text-zinc-500" />
                        <Badge className="bg-purple-500/20 text-purple-300">{connection.to}</Badge>
                        <span className="text-sm text-zinc-400 flex-1">{connection.relationship}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Integrated Project */}
              {lesson.integrated_project && (
                <div className="glass-card p-6 bg-gradient-to-r from-indigo-500/10 to-violet-500/10 border-indigo-500/20">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <Target className="w-5 h-5 text-indigo-400" />
                    Integrated Project
                  </h3>
                  <p className="text-zinc-300 mb-4">{lesson.integrated_project.description}</p>
                  {lesson.integrated_project.requirements && (
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-zinc-400">Requirements:</div>
                      <ul className="space-y-1">
                        {lesson.integrated_project.requirements.map((req, i) => (
                          <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5" />
                            {req}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Reflection Questions */}
              {lesson.reflection_questions?.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <Brain className="w-5 h-5 text-amber-400" />
                    Reflection Questions
                  </h3>
                  <div className="space-y-3">
                    {lesson.reflection_questions.map((question, index) => (
                      <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/50">
                        <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-sm font-medium text-amber-400">{index + 1}</span>
                        </div>
                        <p className="text-sm text-zinc-300">{question}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
