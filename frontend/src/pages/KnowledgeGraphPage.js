import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getConcepts, getUserKnowledgeProgress, getConceptHint, updateConceptState, generateConceptsFromCourses } from '../services/api';
import ReactFlow, {
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  Network, 
  Brain, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Lightbulb,
  BookOpen,
  Target,
  Zap,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Maximize2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';

const statusColors = {
  mastered: { bg: '#10B981', border: '#059669', text: 'Mastered' },
  learning: { bg: '#3B82F6', border: '#2563EB', text: 'Learning' },
  needs_review: { bg: '#F59E0B', border: '#D97706', text: 'Needs Review' },
  not_started: { bg: '#6B7280', border: '#4B5563', text: 'Not Started' }
};

// Custom node component for concepts
const ConceptNode = ({ data }) => {
  const status = data.status || 'not_started';
  const colors = statusColors[status];
  
  return (
    <div
      className="px-4 py-3 rounded-xl shadow-lg border-2 min-w-[160px] cursor-pointer transition-all hover:scale-105"
      style={{
        background: `linear-gradient(135deg, ${colors.bg}20, ${colors.bg}40)`,
        borderColor: colors.border,
      }}
      onClick={data.onClick}
    >
      <div className="flex items-center gap-2 mb-1">
        {status === 'mastered' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
        {status === 'learning' && <Clock className="w-4 h-4 text-blue-400" />}
        {status === 'needs_review' && <AlertCircle className="w-4 h-4 text-amber-400" />}
        {status === 'not_started' && <BookOpen className="w-4 h-4 text-zinc-400" />}
        <span className="text-xs font-medium" style={{ color: colors.border }}>
          {colors.text}
        </span>
      </div>
      <h3 className="font-semibold text-white text-sm">{data.label}</h3>
      <div className="mt-2 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
        <div 
          className="h-full rounded-full transition-all"
          style={{ 
            width: `${(data.confidence || 0) * 100}%`,
            backgroundColor: colors.border 
          }}
        />
      </div>
      <p className="text-xs text-zinc-400 mt-1">{Math.round((data.confidence || 0) * 100)}% confident</p>
    </div>
  );
};

const nodeTypes = { concept: ConceptNode };

export default function KnowledgeGraphPage() {
  const { user } = useAuth();
  const [concepts, setConcepts] = useState([]);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [hintLoading, setHintLoading] = useState(false);
  const [hint, setHint] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      let conceptsData = await getConcepts();
      
      // If no concepts exist, generate them from enrolled courses
      if (!conceptsData || conceptsData.length === 0) {
        toast.info('Generating knowledge graph from your courses...');
        try {
          const result = await generateConceptsFromCourses();
          conceptsData = result.concepts || [];
          toast.success(`Generated ${conceptsData.length} concepts from your courses`);
        } catch (genError) {
          console.error('Failed to generate concepts:', genError);
          toast.error('Could not generate concepts. Enroll in courses first.');
        }
      }
      
      const progressData = await getUserKnowledgeProgress();
      setConcepts(conceptsData);
      setProgress(progressData);
      
      // Generate graph nodes and edges
      generateGraph(conceptsData, progressData);
    } catch (error) {
      console.error('Failed to load knowledge graph:', error);
      toast.error('Failed to load knowledge graph');
    } finally {
      setLoading(false);
    }
  };

  const getConceptProgress = (conceptId) => {
    return progress.find(p => p.concept_id === conceptId) || { status: 'not_started', confidence: 0 };
  };

  const generateGraph = useCallback((conceptsData, progressData) => {
    if (!conceptsData.length) return;
    
    // Group concepts by subject
    const subjects = {};
    conceptsData.forEach(c => {
      if (!subjects[c.subject]) subjects[c.subject] = [];
      subjects[c.subject].push(c);
    });
    
    const newNodes = [];
    const newEdges = [];
    let yOffset = 0;
    
    Object.entries(subjects).forEach(([subject, subjectConcepts], subjectIndex) => {
      // Add subject header node
      newNodes.push({
        id: `subject-${subjectIndex}`,
        type: 'default',
        position: { x: 50, y: yOffset },
        data: { label: subject },
        style: {
          background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
          color: 'white',
          border: 'none',
          borderRadius: '12px',
          padding: '8px 16px',
          fontWeight: 'bold',
          fontSize: '14px'
        },
        draggable: true
      });
      
      // Add concept nodes
      subjectConcepts.forEach((concept, index) => {
        const state = progressData.find(p => p.concept_id === concept.id) || { status: 'not_started', confidence: 0 };
        
        newNodes.push({
          id: concept.id,
          type: 'concept',
          position: { 
            x: 250 + (index % 3) * 220, 
            y: yOffset + Math.floor(index / 3) * 120 
          },
          data: {
            label: concept.name,
            status: state.status,
            confidence: state.confidence,
            concept: concept,
            onClick: () => setSelectedConcept(concept)
          },
          draggable: true
        });
        
        // Create edge from subject to concept
        newEdges.push({
          id: `e-subject-${subjectIndex}-${concept.id}`,
          source: `subject-${subjectIndex}`,
          target: concept.id,
          type: 'smoothstep',
          animated: state.status === 'learning',
          style: { stroke: statusColors[state.status].border, strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: statusColors[state.status].border }
        });
        
        // Create edges for prerequisites
        if (concept.prerequisites) {
          concept.prerequisites.forEach(prereqId => {
            if (conceptsData.find(c => c.id === prereqId)) {
              newEdges.push({
                id: `e-prereq-${prereqId}-${concept.id}`,
                source: prereqId,
                target: concept.id,
                type: 'smoothstep',
                animated: true,
                style: { stroke: '#F59E0B', strokeWidth: 2, strokeDasharray: '5 5' },
                label: 'requires',
                labelStyle: { fill: '#F59E0B', fontSize: 10 }
              });
            }
          });
        }
      });
      
      yOffset += Math.ceil(subjectConcepts.length / 3) * 120 + 100;
    });
    
    setNodes(newNodes);
    setEdges(newEdges);
  }, [setNodes, setEdges]);

  const handleGetHint = async (conceptId) => {
    setHintLoading(true);
    try {
      const result = await getConceptHint(conceptId);
      setHint(result.hint);
    } catch (error) {
      toast.error('Failed to get hint');
    } finally {
      setHintLoading(false);
    }
  };

  const handleStartLearning = async (conceptId) => {
    try {
      // Start learning via API
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/advanced/concept/${conceptId}/start-learning`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        await loadData();
        setSelectedConcept(null);
        
        // Navigate to the concept learning page with the content
        // For now, show the content in a modal or toast
        toast.success(`Started learning: ${data.concept_name}!`);
        
        // Store learning content and navigate
        sessionStorage.setItem('currentLearning', JSON.stringify(data));
        window.location.href = `/ktce-learning?concept=${conceptId}`;
      } else {
        toast.error('Failed to start learning');
      }
    } catch (error) {
      console.error('Start learning error:', error);
      toast.error('Failed to start learning');
    }
  };

  const calculateStats = () => {
    const total = concepts.length;
    const mastered = progress.filter(p => p.status === 'mastered').length;
    const learning = progress.filter(p => p.status === 'learning').length;
    const needsReview = progress.filter(p => p.status === 'needs_review').length;
    return { total, mastered, learning, needsReview };
  };

  const stats = calculateStats();

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Knowledge Graph"
        subtitle="Interactive visualization of your learning journey"
      />
      
      <div className="p-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500">Total Concepts</p>
                <h3 className="text-2xl font-bold">{stats.total}</h3>
              </div>
              <Network className="w-8 h-8 text-blue-400" />
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500">Mastered</p>
                <h3 className="text-2xl font-bold text-emerald-400">{stats.mastered}</h3>
              </div>
              <CheckCircle className="w-8 h-8 text-emerald-400" />
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500">In Progress</p>
                <h3 className="text-2xl font-bold text-blue-400">{stats.learning}</h3>
              </div>
              <Clock className="w-8 h-8 text-blue-400" />
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500">Needs Review</p>
                <h3 className="text-2xl font-bold text-amber-400">{stats.needsReview}</h3>
              </div>
              <RefreshCw className="w-8 h-8 text-amber-400" />
            </div>
          </div>
        </div>

        {/* Interactive Graph */}
        <div className="glass-card" style={{ height: '600px' }}>
          {concepts.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Network className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No concepts yet</h3>
                <p className="text-zinc-500 mb-4">Upload a syllabus or enroll in courses to see your knowledge graph</p>
                <Button onClick={() => window.location.href = '/syllabus-ingestion'}>
                  Upload Syllabus
                </Button>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-left"
              style={{ background: '#09090B' }}
            >
              <Controls 
                style={{ 
                  background: '#18181B', 
                  borderRadius: '12px',
                  border: '1px solid rgba(255,255,255,0.1)'
                }} 
              />
              <Background color="#27272A" gap={20} />
              <Panel position="top-right" className="flex gap-2">
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                  <CheckCircle className="w-3 h-3 mr-1" /> Mastered
                </Badge>
                <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                  <Clock className="w-3 h-3 mr-1" /> Learning
                </Badge>
                <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                  <AlertCircle className="w-3 h-3 mr-1" /> Review
                </Badge>
              </Panel>
            </ReactFlow>
          )}
        </div>

        {/* Concept Detail Dialog */}
        <Dialog open={!!selectedConcept} onOpenChange={() => { setSelectedConcept(null); setHint(null); }}>
          <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
            <DialogHeader>
              <DialogTitle>{selectedConcept?.name}</DialogTitle>
              <DialogDescription className="text-zinc-500">
                {selectedConcept?.description}
              </DialogDescription>
            </DialogHeader>
            
            {selectedConcept && (
              <div className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 rounded-lg bg-zinc-800/50">
                    <p className="text-xs text-zinc-500">Subject</p>
                    <p className="font-medium">{selectedConcept.subject}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/50">
                    <p className="text-xs text-zinc-500">Difficulty</p>
                    <p className="font-medium">Level {selectedConcept.difficulty}/10</p>
                  </div>
                </div>
                
                {hint && (
                  <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <Lightbulb className="w-4 h-4 text-violet-400" />
                      <span className="text-sm font-medium text-violet-400">AI Hint</span>
                    </div>
                    <p className="text-sm text-zinc-300">{hint}</p>
                  </div>
                )}
                
                <div className="flex gap-3 pt-4">
                  <Button
                    variant="outline"
                    onClick={() => handleGetHint(selectedConcept.id)}
                    disabled={hintLoading}
                    className="flex-1 border-white/10"
                  >
                    <Lightbulb className="w-4 h-4 mr-2" />
                    {hintLoading ? 'Loading...' : 'Get Hint'}
                  </Button>
                  <Button
                    onClick={() => handleStartLearning(selectedConcept.id)}
                    className="flex-1 bg-blue-500 hover:bg-blue-600"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Start Learning
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
