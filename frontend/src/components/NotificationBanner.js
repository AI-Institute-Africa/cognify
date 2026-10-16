import React, { useState, useEffect } from 'react';
import { X, Sparkles, BookOpen, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';

const NOTIFICATIONS = [
  {
    id: 1,
    type: 'multidisciplinary',
    title: 'New Cross-Subject Course Available!',
    message: 'Explore "Climate Science & Economics" - combining environmental science with economic principles',
    link: '/multidisciplinary',
    color: 'violet'
  },
  {
    id: 2,
    type: 'research',
    title: 'Latest Research Paper Added',
    message: 'AI in Education: A Meta-Analysis of Learning Outcomes (2025)',
    link: '/live-research',
    color: 'blue'
  },
  {
    id: 3,
    type: 'course',
    title: 'Recommended Course for You',
    message: 'Based on your progress, we suggest "Advanced Problem Solving"',
    link: '/courses',
    color: 'emerald'
  },
  {
    id: 4,
    type: 'achievement',
    title: 'Keep Up the Great Work!',
    message: 'You\'re 2 lessons away from completing your weekly goal!',
    link: '/achievements',
    color: 'amber'
  }
];

export function NotificationBanner() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(true);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (isPaused) return;
    
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % NOTIFICATIONS.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [isPaused]);

  if (!isVisible) return null;

  const notification = NOTIFICATIONS[currentIndex];
  const colorClasses = {
    violet: 'from-violet-500/20 to-purple-500/20 border-violet-500/30',
    blue: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30',
    emerald: 'from-emerald-500/20 to-green-500/20 border-emerald-500/30',
    amber: 'from-amber-500/20 to-yellow-500/20 border-amber-500/30'
  };

  return (
    <div 
      className={`relative overflow-hidden bg-gradient-to-r ${colorClasses[notification.color]} border-b border-white/5`}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className={`w-8 h-8 rounded-lg bg-${notification.color}-500/20 flex items-center justify-center flex-shrink-0`}>
              <Sparkles className={`w-4 h-4 text-${notification.color}-400`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">{notification.title}</span>
              </div>
              <p className="text-sm text-zinc-400 truncate">{notification.message}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 flex-shrink-0">
            <Link to={notification.link}>
              <Button size="sm" variant="ghost" className="text-sm gap-1 hover:bg-white/10">
                Learn More
                <ArrowRight className="w-3 h-3" />
              </Button>
            </Link>
            <button 
              onClick={() => setIsVisible(false)}
              className="p-1 hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-zinc-500" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Progress indicator */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/10">
        <div 
          className="h-full bg-white/30 transition-all duration-100"
          style={{ 
            width: `${((currentIndex + 1) / NOTIFICATIONS.length) * 100}%`,
            transition: 'width 5s linear'
          }}
        />
      </div>
      
      {/* Slide indicators */}
      <div className="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-1">
        {NOTIFICATIONS.map((_, idx) => (
          <button
            key={idx}
            onClick={() => setCurrentIndex(idx)}
            className={`w-1.5 h-1.5 rounded-full transition-all ${
              idx === currentIndex ? 'bg-white w-4' : 'bg-white/30'
            }`}
          />
        ))}
      </div>
    </div>
  );
}

export default NotificationBanner;
