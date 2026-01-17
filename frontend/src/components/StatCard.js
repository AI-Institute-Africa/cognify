import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export const StatCard = ({ 
  title, 
  value, 
  change, 
  changeType = 'neutral', 
  icon: Icon, 
  iconColor = 'text-blue-400',
  className = '' 
}) => {
  const changeIcon = {
    up: TrendingUp,
    down: TrendingDown,
    neutral: Minus
  };
  
  const changeColor = {
    up: 'text-emerald-400',
    down: 'text-red-400',
    neutral: 'text-zinc-400'
  };

  const ChangeIcon = changeIcon[changeType];

  return (
    <div
      className={`glass-card p-6 hover:border-white/20 transition-all duration-300 group ${className}`}
      data-testid={`stat-card-${title.toLowerCase().replace(/\s/g, '-')}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-zinc-500 font-medium">{title}</p>
          <h3 className="text-3xl font-bold mt-2 tracking-tight">{value}</h3>
          {change !== undefined && (
            <div className={`flex items-center gap-1 mt-2 ${changeColor[changeType]}`}>
              <ChangeIcon className="w-4 h-4" />
              <span className="text-sm font-medium">{change}</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={`p-3 rounded-xl bg-white/5 ${iconColor} group-hover:scale-110 transition-transform duration-300`}>
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </div>
  );
};

export const WideStatCard = ({ 
  title, 
  value, 
  subtitle,
  icon: Icon,
  gradient = 'from-blue-500 to-violet-500',
  children 
}) => {
  return (
    <div
      className="glass-card p-6 col-span-2 relative overflow-hidden"
      data-testid={`wide-stat-card-${title.toLowerCase().replace(/\s/g, '-')}`}
    >
      {/* Background gradient */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-5`} />
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-sm text-zinc-500 font-medium">{title}</p>
            <h3 className="text-4xl font-bold mt-2 tracking-tight">{value}</h3>
            {subtitle && <p className="text-sm text-zinc-400 mt-1">{subtitle}</p>}
          </div>
          {Icon && (
            <div className={`p-4 rounded-2xl bg-gradient-to-br ${gradient}`}>
              <Icon className="w-8 h-8 text-white" />
            </div>
          )}
        </div>
        {children}
      </div>
    </div>
  );
};
