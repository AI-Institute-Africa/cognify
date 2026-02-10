import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { analyzeSyllabus, generateLesson, createCourse } from '../services/api';
import { 
  FileText,
  Upload,
  BookOpen,
  Target,
  Layers,
  CheckCircle,
  Clock,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Brain,
  Lightbulb,
  GraduationCap,
  Plus
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';

export default function SyllabusIngestionPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [content, setContent] = useState('');
  const [contentType, setContentType] = useState('syllabus');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [generatingLesson, setGeneratingLesson] = useState(false);
  const [generatedLesson, setGeneratedLesson] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [creatingCourse, setCreatingCourse] = useState(false);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type === 'text/plain' || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setContent(e.target.result);
        toast.success('File loaded successfully');
      };
      reader.readAsText(file);
    } else {
      toast.error('Please upload a text file (.txt or .md)');
    }
  };

  const handleAnalyze = async () => {
    if (!content.trim()) {
      toast.error('Please enter or upload syllabus content');
      return;
    }

    setAnalyzing(true);
    try {
      const result = await analyzeSyllabus(content, contentType);
      setAnalysis(result);
      toast.success('Analysis complete!');
    } catch (error) {
      console.error('Analysis failed:', error);
      toast.error('Failed to analyze content');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateLesson = async (topic) => {
    setSelectedTopic(topic);
    setGeneratingLesson(true);
    try {
      const objectives = analysis?.objectives?.slice(0, 3) || [
        `Understand ${topic.name}`,
        `Apply ${topic.name} concepts`,
        `Analyze ${topic.name} examples`
      ];
      
      const result = await generateLesson(
        topic.name,
        objectives,
        topic.hours ? topic.hours * 60 : 30
      );
      setGeneratedLesson(result);
      toast.success('Lesson generated!');
    } catch (error) {
      console.error('Lesson generation failed:', error);
      toast.error('Failed to generate lesson');
    } finally {
      setGeneratingLesson(false);
    }
  };

  const handleCreateCourse = async () => {
    if (!analysis?.title) {
      toast.error('Please analyze syllabus first');
      return;
    }

    setCreatingCourse(true);
    try {
      const courseData = {
        code: `COURSE-${Date.now().toString(36).toUpperCase()}`,
        name: analysis.title,
        description: `Auto-generated course from syllabus analysis. Topics: ${analysis.topics?.map(t => t.name).join(', ')}`,
        grade_level: 'All Levels',
        credits: 3,
        max_students: 50
      };
      
      await createCourse(courseData);
      toast.success('Course created successfully!');
    } catch (error) {
      console.error('Course creation failed:', error);
      toast.error('Failed to create course');
    } finally {
      setCreatingCourse(false);
    }
  };

  return (
    <DashboardLayout>
      <Header 
        title="Content Ingestion Engine"
        subtitle="Transform any curriculum into AI-powered interactive learning"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">World's First Curriculum Transformer</h3>
                <p className="text-zinc-400 text-sm">
                  Upload sources (PDF, textbook chapter, slide deck) and the AI will automatically 
                  convert it into interactive lessons, concept maps, adaptive sequences, quizzes, and challenges.
                </p>
              </div>
            </div>
          </div>

          <Tabs defaultValue="upload" className="space-y-6">
            <TabsList className="bg-zinc-800/50">
              <TabsTrigger value="upload">1. Upload Sources</TabsTrigger>
              <TabsTrigger value="analysis" disabled={!analysis}>2. Analysis</TabsTrigger>
              <TabsTrigger value="lessons" disabled={!analysis}>3. Generate Lessons</TabsTrigger>
            </TabsList>

            {/* Upload Tab */}
            <TabsContent value="upload">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="glass-card p-6 space-y-6">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Upload className="w-5 h-5 text-blue-400" />
                    Upload Sources or Paste Content
                  </h3>

                  <div className="space-y-2">
                    <Label>Content Type</Label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {['syllabus', 'textbook', 'slides', 'outline'].map((type) => (
                        <button
                          key={type}
                          onClick={() => setContentType(type)}
                          className={`p-3 rounded-lg border text-center transition-all ${
                            contentType === type
                              ? 'bg-blue-500/20 border-blue-500'
                              : 'bg-zinc-800/50 border-white/5 hover:border-white/10'
                          }`}
                        >
                          <span className="text-sm capitalize">{type}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Upload File (Optional)</Label>
                    <Input
                      type="file"
                      accept=".txt,.md"
                      onChange={handleFileUpload}
                      className="bg-zinc-800 border-white/10"
                    />
                    <p className="text-xs text-zinc-500">Supports .txt and .md files</p>
                  </div>

                  <div className="space-y-2">
                    <Label>Or Paste Content</Label>
                    <Textarea
                      placeholder="Paste your syllabus, course outline, or textbook content here..."
                      value={content}
                      onChange={(e) => setContent(e.target.value)}
                      className="min-h-[300px] bg-zinc-800 border-white/10"
                      data-testid="syllabus-input"
                    />
                  </div>

                  <Button
                    onClick={handleAnalyze}
                    disabled={!content.trim() || analyzing}
                    data-testid="analyze-btn"
                    className="w-full bg-blue-500 hover:bg-blue-600"
                  >
                    {analyzing ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Brain className="w-4 h-4 mr-2" />
                        Analyze & Transform
                      </>
                    )}
                  </Button>
                </div>

                <div className="glass-card p-6">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <FileText className="w-5 h-5 text-blue-400" />
                    What Will Be Generated
                  </h3>

                  <div className="space-y-4">
                    {[
                      { icon: BookOpen, title: 'Interactive Lessons', desc: 'Engaging step-by-step learning modules' },
                      { icon: Layers, title: 'Concept Graph', desc: 'Visual map of interconnected concepts' },
                      { icon: Target, title: 'Learning Objectives', desc: 'Clear goals for each topic' },
                      { icon: GraduationCap, title: 'Assessments', desc: 'Quizzes, assignments, and challenges' },
                      { icon: Lightbulb, title: 'Real-World Applications', desc: 'Practical examples and use cases' },
                    ].map((item, index) => (
                      <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/50">
                        <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                          <item.icon className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                          <div className="font-medium">{item.title}</div>
                          <div className="text-sm text-zinc-500">{item.desc}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Analysis Tab */}
            <TabsContent value="analysis">
              {analysis && (
                <div className="space-y-6">
                  <div className="glass-card p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-2xl font-bold">{analysis.title || 'Analyzed Course'}</h2>
                        <p className="text-zinc-500 mt-1">
                          {analysis.topics?.length || 0} topics • 
                          {analysis.concepts?.length || 0} concepts identified
                        </p>
                      </div>
                      <Button
                        onClick={handleCreateCourse}
                        disabled={creatingCourse}
                        className="bg-emerald-500 hover:bg-emerald-600"
                      >
                        {creatingCourse ? (
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Plus className="w-4 h-4 mr-2" />
                        )}
                        Create Course
                      </Button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="glass-card p-6">
                      <h3 className="font-semibold flex items-center gap-2 mb-4">
                        <BookOpen className="w-5 h-5 text-blue-400" />
                        Topics Identified
                      </h3>
                      <div className="space-y-3">
                        {analysis.topics?.map((topic, index) => (
                          <div key={index} className="p-3 rounded-lg bg-zinc-800/50 border border-white/5">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{topic.name}</span>
                              {topic.hours && (
                                <Badge className="bg-blue-500/20 text-blue-400">
                                  <Clock className="w-3 h-3 mr-1" />
                                  {topic.hours}h
                                </Badge>
                              )}
                            </div>
                            {topic.subtopics && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {topic.subtopics.map((sub, i) => (
                                  <Badge key={i} variant="outline" className="text-xs border-white/10">
                                    {sub}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        )) || <p className="text-zinc-500">No topics extracted</p>}
                      </div>
                    </div>

                    <div className="glass-card p-6">
                      <h3 className="font-semibold flex items-center gap-2 mb-4">
                        <Target className="w-5 h-5 text-emerald-400" />
                        Learning Objectives
                      </h3>
                      <div className="space-y-2">
                        {analysis.objectives?.map((obj, index) => (
                          <div key={index} className="flex items-start gap-2 p-2">
                            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                            <span className="text-sm">{obj}</span>
                          </div>
                        )) || <p className="text-zinc-500">No objectives extracted</p>}
                      </div>
                    </div>

                    <div className="glass-card p-6">
                      <h3 className="font-semibold flex items-center gap-2 mb-4">
                        <Brain className="w-5 h-5 text-violet-400" />
                        Key Concepts
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {analysis.concepts?.map((concept, index) => (
                          <Badge key={index} className="bg-violet-500/20 text-violet-300">
                            {concept.name || concept}
                          </Badge>
                        )) || <p className="text-zinc-500">No concepts extracted</p>}
                      </div>
                    </div>

                    <div className="glass-card p-6">
                      <h3 className="font-semibold flex items-center gap-2 mb-4">
                        <Lightbulb className="w-5 h-5 text-amber-400" />
                        Real-World Applications
                      </h3>
                      <div className="space-y-2">
                        {analysis.applications?.map((app, index) => (
                          <div key={index} className="flex items-start gap-2 p-2">
                            <ArrowRight className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                            <span className="text-sm">{app}</span>
                          </div>
                        )) || <p className="text-zinc-500">No applications identified</p>}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </TabsContent>

            {/* Lessons Tab */}
            <TabsContent value="lessons">
              {analysis && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="glass-card p-6">
                    <h3 className="font-semibold flex items-center gap-2 mb-4">
                      <BookOpen className="w-5 h-5 text-blue-400" />
                      Select Topic
                    </h3>
                    <div className="space-y-2">
                      {analysis.topics?.map((topic, index) => (
                        <button
                          key={index}
                          onClick={() => handleGenerateLesson(topic)}
                          disabled={generatingLesson}
                          className={`w-full p-3 rounded-lg border text-left transition-all ${
                            selectedTopic?.name === topic.name
                              ? 'bg-blue-500/20 border-blue-500'
                              : 'bg-zinc-800/50 border-white/5 hover:border-white/10'
                          }`}
                        >
                          <div className="font-medium">{topic.name}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="lg:col-span-2 glass-card p-6">
                    <h3 className="font-semibold flex items-center gap-2 mb-4">
                      <Sparkles className="w-5 h-5 text-violet-400" />
                      Generated Lesson
                    </h3>

                    {generatingLesson ? (
                      <div className="flex items-center justify-center py-12">
                        <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
                        <span className="ml-3 text-zinc-400">Generating lesson...</span>
                      </div>
                    ) : generatedLesson ? (
                      <div className="space-y-4">
                        <h4 className="text-xl font-semibold">{generatedLesson.title}</h4>
                        
                        {generatedLesson.sections?.map((section, index) => (
                          <div key={index} className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">{section.title}</span>
                              <Badge className="text-xs">{section.type}</Badge>
                            </div>
                            <p className="text-sm text-zinc-400">{section.content?.substring(0, 200)}...</p>
                          </div>
                        ))}

                        {generatedLesson.key_takeaways && (
                          <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                            <h5 className="font-medium text-emerald-400 mb-2">Key Takeaways</h5>
                            <ul className="space-y-1">
                              {generatedLesson.key_takeaways.map((takeaway, i) => (
                                <li key={i} className="text-sm flex items-start gap-2">
                                  <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5" />
                                  {takeaway}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-12 text-zinc-500">
                        <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p>Select a topic to generate an interactive lesson</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </DashboardLayout>
  );
}
