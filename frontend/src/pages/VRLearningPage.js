import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Box, Maximize2, RotateCcw, Play, Pause, Volume2, VolumeX,
  Move3D, Glasses, Eye, Layers, ZoomIn, ZoomOut, Settings,
  ChevronLeft, ChevronRight, Loader2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Slider } from '../components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

// Sample VR environments
const VR_ENVIRONMENTS = [
  { id: 'lab', name: 'Science Laboratory', description: 'Interactive 3D chemistry and physics lab', thumbnail: 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400' },
  { id: 'history', name: 'Ancient History Museum', description: 'Walk through historical artifacts in 3D', thumbnail: 'https://images.unsplash.com/photo-1564399580075-5dfe19c205f3?w=400' },
  { id: 'space', name: 'Space Station', description: 'Explore the solar system in VR', thumbnail: 'https://images.unsplash.com/photo-1446776877081-d282a0f896e2?w=400' },
  { id: 'biology', name: 'Human Body Explorer', description: '3D anatomy and biology lessons', thumbnail: 'https://images.unsplash.com/photo-1559757175-5700dde675bc?w=400' },
  { id: 'math', name: 'Geometry World', description: '3D mathematical shapes and concepts', thumbnail: 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=400' },
  { id: 'art', name: 'Virtual Art Gallery', description: 'Explore famous artworks in 3D', thumbnail: 'https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=400' },
];

export default function VRLearningPage() {
  const { user } = useAuth();
  const [selectedEnvironment, setSelectedEnvironment] = useState(VR_ENVIRONMENTS[0]);
  const [isVRMode, setIsVRMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const viewerRef = useRef(null);
  const isDragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  // Handle mouse drag for 3D rotation
  const handleMouseDown = (e) => {
    isDragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e) => {
    if (!isDragging.current) return;
    const deltaX = e.clientX - lastPos.current.x;
    const deltaY = e.clientY - lastPos.current.y;
    setRotation(prev => ({
      x: prev.x + deltaY * 0.5,
      y: prev.y + deltaX * 0.5
    }));
    lastPos.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const enterVRMode = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsVRMode(true);
      setIsLoading(false);
      toast.success('Entering VR Mode - Use mouse to look around');
    }, 1500);
  };

  const exitVRMode = () => {
    setIsVRMode(false);
    setRotation({ x: 0, y: 0 });
    setZoom(1);
  };

  const handleZoom = (direction) => {
    setZoom(prev => {
      const newZoom = direction === 'in' ? prev + 0.2 : prev - 0.2;
      return Math.max(0.5, Math.min(2, newZoom));
    });
  };

  // Full VR View
  if (isVRMode) {
    return (
      <div 
        className="fixed inset-0 bg-black z-50 cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* VR Scene */}
        <div 
          className="w-full h-full relative overflow-hidden"
          style={{
            perspective: '1000px',
            transformStyle: 'preserve-3d'
          }}
        >
          <div
            className="absolute inset-0 transition-transform duration-100"
            style={{
              transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg) scale(${zoom})`,
              transformStyle: 'preserve-3d'
            }}
          >
            {/* 360 Environment Image */}
            <img 
              src={selectedEnvironment.thumbnail}
              alt={selectedEnvironment.name}
              className="w-full h-full object-cover"
              style={{
                filter: 'brightness(0.8)'
              }}
            />
            
            {/* 3D Elements Overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-32 h-32 mx-auto mb-4 rounded-full bg-blue-500/20 border-2 border-blue-500/50 flex items-center justify-center animate-pulse">
                  <Box className="w-16 h-16 text-blue-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">{selectedEnvironment.name}</h2>
                <p className="text-zinc-400">{selectedEnvironment.description}</p>
                <p className="text-sm text-zinc-500 mt-4">Drag to look around • Scroll to zoom</p>
              </div>
            </div>
          </div>
        </div>

        {/* VR Controls Overlay */}
        <div className="absolute top-4 left-4 right-4 flex justify-between items-start">
          <Button 
            onClick={exitVRMode}
            variant="outline"
            className="bg-black/50 border-white/20 hover:bg-black/70"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Exit VR
          </Button>
          
          <div className="flex items-center gap-2">
            <Button 
              size="icon" 
              variant="outline"
              onClick={() => handleZoom('out')}
              className="bg-black/50 border-white/20"
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-white text-sm px-2">{Math.round(zoom * 100)}%</span>
            <Button 
              size="icon" 
              variant="outline"
              onClick={() => handleZoom('in')}
              className="bg-black/50 border-white/20"
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button 
              size="icon" 
              variant="outline"
              onClick={() => setIsMuted(!isMuted)}
              className="bg-black/50 border-white/20"
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Bottom Controls */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-black/70 rounded-xl p-4 backdrop-blur-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button 
                  size="icon"
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="bg-blue-500 hover:bg-blue-600"
                >
                  {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                </Button>
                <div>
                  <p className="font-medium">{selectedEnvironment.name}</p>
                  <p className="text-sm text-zinc-400">Interactive 3D Environment</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <Button 
                  size="icon" 
                  variant="outline"
                  onClick={() => setRotation({ x: 0, y: 0 })}
                  className="border-white/20"
                >
                  <RotateCcw className="w-4 h-4" />
                </Button>
                <Button 
                  size="icon" 
                  variant="outline"
                  className="border-white/20"
                >
                  <Maximize2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* VR Headset Indicator */}
        <div className="absolute top-1/2 left-4 -translate-y-1/2">
          <div className="bg-black/50 rounded-lg p-2 text-center">
            <Glasses className="w-6 h-6 text-blue-400 mx-auto mb-1" />
            <p className="text-xs text-zinc-400">VR Ready</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="VR Learning Environment"
        subtitle="Immersive 3D educational experiences"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Featured Environment */}
          <div className="glass-card p-0 overflow-hidden mb-8">
            <div className="relative aspect-video">
              <img 
                src={selectedEnvironment.thumbnail}
                alt={selectedEnvironment.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
              
              {/* Play Button Overlay */}
              <div className="absolute inset-0 flex items-center justify-center">
                <Button
                  onClick={enterVRMode}
                  disabled={isLoading}
                  size="lg"
                  className="bg-blue-500 hover:bg-blue-600 h-16 px-8 text-lg gap-3"
                  data-testid="enter-vr-btn"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-6 h-6 animate-spin" />
                      Loading VR...
                    </>
                  ) : (
                    <>
                      <Glasses className="w-6 h-6" />
                      Enter VR Mode
                    </>
                  )}
                </Button>
              </div>
              
              {/* Info Overlay */}
              <div className="absolute bottom-0 left-0 right-0 p-6">
                <div className="flex items-end justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">{selectedEnvironment.name}</h2>
                    <p className="text-zinc-300">{selectedEnvironment.description}</p>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-400">
                    <Eye className="w-4 h-4" />
                    <span className="text-sm">360° View</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Environment Selection */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Choose Environment</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {VR_ENVIRONMENTS.map((env) => (
                <button
                  key={env.id}
                  onClick={() => setSelectedEnvironment(env)}
                  className={`rounded-xl overflow-hidden border-2 transition-all ${
                    selectedEnvironment.id === env.id
                      ? 'border-blue-500 ring-2 ring-blue-500/20'
                      : 'border-white/10 hover:border-white/20'
                  }`}
                  data-testid={`env-${env.id}`}
                >
                  <div className="aspect-video relative">
                    <img 
                      src={env.thumbnail}
                      alt={env.name}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/40" />
                    <div className="absolute bottom-2 left-2 right-2">
                      <p className="text-xs font-medium text-white truncate">{env.name}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-card p-6">
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4">
                <Move3D className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="font-semibold mb-2">360° Exploration</h3>
              <p className="text-sm text-zinc-400">
                Look around in any direction with full 360-degree movement support
              </p>
            </div>
            
            <div className="glass-card p-6">
              <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center mb-4">
                <Layers className="w-6 h-6 text-violet-400" />
              </div>
              <h3 className="font-semibold mb-2">Interactive Objects</h3>
              <p className="text-sm text-zinc-400">
                Click and interact with 3D objects to learn more about them
              </p>
            </div>
            
            <div className="glass-card p-6">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center mb-4">
                <Glasses className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">VR Headset Ready</h3>
              <p className="text-sm text-zinc-400">
                Compatible with WebXR devices for full immersive experience
              </p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
