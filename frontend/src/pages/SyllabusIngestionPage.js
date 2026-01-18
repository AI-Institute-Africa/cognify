import React, { useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { ingestSyllabus, getCourses } from '../services/api';
import { 
  FileUp, 
  FileText, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  BookOpen,
  Sparkles,
  ArrowRight,
  Upload,
  File
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

export default function SyllabusIngestionPage() {
  const [file, setFile] = useState(null);
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  React.useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      const data = await getCourses();
      setCourses(data);
    } catch (error) {
      console.error('Failed to load courses:', error);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    const allowedTypes = ['.pdf', '.txt', '.md', '.docx'];
    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.'));
    
    if (!allowedTypes.includes(ext.toLowerCase())) {
      toast.error('Please upload a PDF, TXT, MD, or DOCX file');
      return;
    }
    
    setFile(selectedFile);
    setResult(null);
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleIngest = async () => {
    if (!file) {
      toast.error('Please select a file');
      return;
    }

    setLoading(true);
    setProgress(10);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const data = await ingestSyllabus(file, selectedCourse || null);
      
      clearInterval(progressInterval);
      setProgress(100);
      setResult(data);
      toast.success('Syllabus processed successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to process syllabus');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <Header 
        title="Syllabus Ingestion"
        subtitle="Convert documents into interactive courses"
      />
      
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
          {/* Info Card */}
          <div className="glass-card p-6 mb-8 border-blue-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-blue-500/20">
                <Sparkles className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">AI-Powered Course Generation</h3>
                <p className="text-zinc-400 text-sm">
                  Upload your syllabus, curriculum, or course outline. Our AI will analyze it and 
                  automatically generate structured learning concepts, prerequisites, and interactive content modules.
                </p>
              </div>
            </div>
          </div>

          {/* Upload Section */}
          <div className="glass-card p-8">
            <h2 className="text-xl font-semibold mb-6">Upload Syllabus</h2>
            
            {/* Drop Zone */}
            <div
              className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
                dragActive 
                  ? 'border-blue-500 bg-blue-500/10' 
                  : file 
                    ? 'border-emerald-500/50 bg-emerald-500/5'
                    : 'border-white/10 hover:border-white/20 bg-zinc-900/30'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                onChange={handleFileInput}
                accept=".pdf,.txt,.md,.docx"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                data-testid="syllabus-file-input"
              />
              
              {file ? (
                <div className="space-y-4">
                  <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 flex items-center justify-center mx-auto">
                    <FileText className="w-8 h-8 text-emerald-400" />
                  </div>
                  <div>
                    <p className="font-medium text-lg">{file.name}</p>
                    <p className="text-sm text-zinc-500">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => { e.stopPropagation(); setFile(null); setResult(null); }}
                    className="border-white/10"
                  >
                    Change File
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="w-16 h-16 rounded-2xl bg-zinc-800 flex items-center justify-center mx-auto">
                    <Upload className="w-8 h-8 text-zinc-500" />
                  </div>
                  <div>
                    <p className="font-medium text-lg">Drop your syllabus here</p>
                    <p className="text-sm text-zinc-500">or click to browse</p>
                  </div>
                  <div className="flex items-center justify-center gap-2 text-xs text-zinc-600">
                    <File className="w-4 h-4" />
                    PDF, TXT, MD, DOCX supported
                  </div>
                </div>
              )}
            </div>

            {/* Course Selection (Optional) */}
            <div className="mt-6 space-y-2">
              <Label>Link to Course (Optional)</Label>
              <Select value={selectedCourse} onValueChange={setSelectedCourse}>
                <SelectTrigger className="bg-zinc-900/50 border-white/10" data-testid="course-select">
                  <SelectValue placeholder="Select a course to link this syllabus to..." />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10">
                  <SelectItem value="">No course (create new)</SelectItem>
                  {courses.map(course => (
                    <SelectItem key={course.id} value={course.id}>
                      {course.code} - {course.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-zinc-500">
                Optionally link the generated concepts to an existing course
              </p>
            </div>

            {/* Progress Bar */}
            {loading && (
              <div className="mt-6 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-400">Processing syllabus...</span>
                  <span className="text-blue-400">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2 bg-zinc-800" />
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Analyzing content with AI...
                </div>
              </div>
            )}

            {/* Action Button */}
            <Button
              onClick={handleIngest}
              disabled={!file || loading}
              data-testid="ingest-btn"
              className="w-full mt-6 h-12 bg-blue-500 hover:bg-blue-600"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Analyze & Generate Course
                </>
              )}
            </Button>
          </div>

          {/* Results Section */}
          {result && (
            <div className="glass-card p-8 mt-8 animate-fadeIn">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg bg-emerald-500/20">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                </div>
                <h2 className="text-xl font-semibold">Processing Complete</h2>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="p-4 rounded-xl bg-zinc-800/50 text-center">
                  <p className="text-3xl font-bold text-blue-400">{result.concepts_created || 0}</p>
                  <p className="text-sm text-zinc-500">Concepts Created</p>
                </div>
                <div className="p-4 rounded-xl bg-zinc-800/50 text-center">
                  <p className="text-3xl font-bold text-violet-400">AI</p>
                  <p className="text-sm text-zinc-500">Analysis Complete</p>
                </div>
                <div className="p-4 rounded-xl bg-zinc-800/50 text-center">
                  <p className="text-3xl font-bold text-emerald-400">Ready</p>
                  <p className="text-sm text-zinc-500">For Learning</p>
                </div>
              </div>

              {/* Analysis Preview */}
              {result.analysis && (
                <div className="p-4 rounded-xl bg-zinc-900/50 border border-white/5">
                  <h3 className="text-sm font-medium text-zinc-400 mb-3">AI Analysis</h3>
                  <p className="text-sm text-zinc-300 whitespace-pre-wrap line-clamp-10">
                    {result.analysis}
                  </p>
                </div>
              )}

              {/* Next Steps */}
              <div className="mt-6 flex gap-4">
                <Button
                  variant="outline"
                  onClick={() => { setFile(null); setResult(null); }}
                  className="flex-1 border-white/10"
                >
                  Upload Another
                </Button>
                <Button
                  onClick={() => window.location.href = '/knowledge-graph'}
                  className="flex-1 bg-violet-500 hover:bg-violet-600"
                >
                  View Knowledge Graph
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
