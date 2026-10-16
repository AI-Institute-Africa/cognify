import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getAchievements } from '../services/api';
import { Trophy, Award, Star, Medal, Crown, Target, Gem } from 'lucide-react';
import { Badge } from '../components/ui/badge';

const categoryIcons = {
  'Academic': Star,
  'Sports': Medal,
  'Leadership': Crown,
  'Arts': Gem,
  'Science': Target,
  'default': Award
};

const categoryColors = {
  'Academic': 'from-blue-500 to-cyan-500',
  'Sports': 'from-orange-500 to-red-500',
  'Leadership': 'from-violet-500 to-purple-500',
  'Arts': 'from-pink-500 to-rose-500',
  'Science': 'from-emerald-500 to-teal-500',
  'default': 'from-amber-500 to-yellow-500'
};

export default function AchievementsPage() {
  const { user } = useAuth();
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    loadAchievements();
  }, []);

  const loadAchievements = async () => {
    try {
      const data = await getAchievements();
      setAchievements(data);
    } catch (error) {
      console.error('Failed to load achievements:', error);
    } finally {
      setLoading(false);
    }
  };

  const categories = ['all', ...new Set(achievements.map(a => a.category))];

  const filteredAchievements = selectedCategory === 'all' 
    ? achievements 
    : achievements.filter(a => a.category === selectedCategory);

  const getIcon = (category) => {
    return categoryIcons[category] || categoryIcons.default;
  };

  const getGradient = (category) => {
    return categoryColors[category] || categoryColors.default;
  };

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
        title="Achievements & Awards"
        subtitle="Your accomplishments and certifications"
      />
      
      <div className="p-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Total Achievements</p>
                <h3 className="text-3xl font-bold mt-2">{achievements.length}</h3>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/20">
                <Trophy className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Verified</p>
                <h3 className="text-3xl font-bold mt-2 text-emerald-400">
                  {achievements.filter(a => a.is_verified).length}
                </h3>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/20">
                <Award className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
          </div>
          
          <div className="md:col-span-2 glass-card p-6">
            <p className="text-sm text-zinc-500 mb-4">Categories</p>
            <div className="flex flex-wrap gap-2">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  data-testid={`category-btn-${cat}`}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedCategory === cat
                      ? 'bg-blue-500 text-white'
                      : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                  }`}
                >
                  {cat === 'all' ? 'All' : cat}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        {/* Achievements Grid */}
        {filteredAchievements.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <Trophy className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No achievements yet</h3>
            <p className="text-zinc-500">
              {selectedCategory === 'all' 
                ? 'Your achievements will appear here as you earn them'
                : `No achievements in ${selectedCategory} category`
              }
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAchievements.map((achievement, index) => {
              const Icon = getIcon(achievement.category);
              const gradient = getGradient(achievement.category);
              
              return (
                <div
                  key={achievement.id}
                  className={`glass-card p-6 hover:border-white/20 transition-all duration-300 group animate-fadeIn stagger-${(index % 5) + 1}`}
                  data-testid={`achievement-card-${achievement.id}`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-4 rounded-2xl bg-gradient-to-br ${gradient} group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                    {achievement.is_verified && (
                      <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                        Verified
                      </Badge>
                    )}
                  </div>
                  
                  <h3 className="text-lg font-semibold mb-2">{achievement.title}</h3>
                  <p className="text-sm text-zinc-500 mb-4 line-clamp-2">{achievement.description}</p>
                  
                  <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <Badge variant="outline" className="text-zinc-400 border-zinc-700">
                      {achievement.category}
                    </Badge>
                    <span className="text-sm text-zinc-500">
                      {new Date(achievement.date_awarded).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short'
                      })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
