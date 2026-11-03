import React, { useState, useEffect } from 'react';
import { Sparkles, Layers, Video, MessageSquare, ChevronDown, CheckCircle2, AlertTriangle, Calendar } from 'lucide-react';
import { getLearnerEntitlements } from '../services/api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';

export const AITokenBalancePill = ({ variant = 'header' }) => {
  const [entitlements, setEntitlements] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await getLearnerEntitlements();
        if (mounted && data) {
          setEntitlements(data);
        }
      } catch (err) {
        console.warn('Could not load AI entitlements:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 20000); // Poll every 20s
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const free = entitlements?.free_allowances || {};
  const imgSlideRemaining = free.image_slide?.remaining ?? 2;
  const videoSecsRemaining = free.video?.remaining_seconds ?? 12;
  const textInputRemaining = free.text?.input_remaining ?? 200000;
  const textOutputRemaining = free.text?.output_remaining ?? 100000;
  const totalTextK = Math.round((textInputRemaining + textOutputRemaining) / 1000);
  const courseAllocations = entitlements?.course_allocations || [];
  const exhaustionMessages = entitlements?.exhaustion_messages || [];

  if (loading && !entitlements) {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 animate-pulse">
        <Sparkles className="w-3.5 h-3.5" />
        <span>Loading AI Tokens...</span>
      </div>
    );
  }

  if (variant === 'dashboard-card') {
    return (
      <div className="bg-zinc-900/90 border border-white/10 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-blue-500/10 via-violet-500/5 to-transparent rounded-full blur-2xl -z-10 pointer-events-none" />
        
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">AI Learning Tokens & Entitlements</h3>
              <p className="text-xs text-zinc-400">Lifetime free onboarding allowance & active course allocations</p>
            </div>
          </div>
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Live Synced
          </span>
        </div>

        {exhaustionMessages.length > 0 && (
          <div className="mb-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              {exhaustionMessages.map((msg, i) => (
                <p key={i}>{msg}</p>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {/* Images & Slides */}
          <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-zinc-400 text-xs mb-2">
              <span className="flex items-center gap-1.5"><Layers className="w-4 h-4 text-blue-400" /> Slides & Images</span>
              <span className="font-mono text-zinc-300">{imgSlideRemaining} / {free.image_slide?.total ?? 2}</span>
            </div>
            <div className="text-2xl font-bold text-white mb-1">
              {imgSlideRemaining} <span className="text-xs font-normal text-zinc-400">generations left</span>
            </div>
            <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all ${imgSlideRemaining > 0 ? 'bg-blue-500' : 'bg-red-500'}`} 
                style={{ width: `${Math.min(100, (imgSlideRemaining / (free.image_slide?.total || 2)) * 100)}%` }} 
              />
            </div>
          </div>

          {/* Video Seconds */}
          <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-zinc-400 text-xs mb-2">
              <span className="flex items-center gap-1.5"><Video className="w-4 h-4 text-violet-400" /> Video Seconds</span>
              <span className="font-mono text-zinc-300">{videoSecsRemaining}s / {free.video?.total_seconds ?? 12}s</span>
            </div>
            <div className="text-2xl font-bold text-white mb-1">
              {videoSecsRemaining}s <span className="text-xs font-normal text-zinc-400">remaining</span>
            </div>
            <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all ${videoSecsRemaining > 0 ? 'bg-violet-500' : 'bg-red-500'}`} 
                style={{ width: `${Math.min(100, (videoSecsRemaining / (free.video?.total_seconds || 12)) * 100)}%` }} 
              />
            </div>
          </div>

          {/* Text Tokens */}
          <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-zinc-400 text-xs mb-2">
              <span className="flex items-center gap-1.5"><MessageSquare className="w-4 h-4 text-emerald-400" /> Monthly Text Tokens</span>
              <span className="font-mono text-zinc-300">{totalTextK}k</span>
            </div>
            <div className="text-2xl font-bold text-white mb-1">
              {totalTextK}k <span className="text-xs font-normal text-zinc-400">tokens available</span>
            </div>
            <div className="text-[11px] text-zinc-400">
              {textInputRemaining.toLocaleString()} in / {textOutputRemaining.toLocaleString()} out
            </div>
          </div>
        </div>

        {/* Active Course Allocations */}
        <div>
          <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-3">Active Course Allocations</h4>
          {courseAllocations.length === 0 ? (
            <div className="text-xs text-zinc-500 py-3 text-center bg-white/3 rounded-xl border border-white/5">
              No course allocations active. Enrolling in accredited diplomas unlocks automatic monthly course wallet credits.
            </div>
          ) : (
            <div className="space-y-2">
              {courseAllocations.map((alloc, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                  <div className="flex items-center gap-2.5">
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                    <div>
                      <p className="text-sm font-medium text-white">{alloc.course_name}</p>
                      <p className="text-xs text-zinc-400 flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-zinc-500" />
                        Expires: {alloc.course_end ? new Date(alloc.course_end).toLocaleDateString() : 'Active'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-emerald-400">
                      ${((alloc.wallet_balance_minor || 0) / 100).toFixed(2)}
                    </p>
                    <span className="text-[10px] text-zinc-500 capitalize">{alloc.subscription_status || 'active'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Header Pill view
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-blue-500/10 via-violet-500/10 to-transparent border border-white/10 hover:border-blue-500/30 transition-all text-xs"
          title="Click to view AI Token & Allowance details"
        >
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span className="hidden sm:inline text-zinc-300 font-medium">AI Tokens:</span>
          <span className="text-blue-400 font-semibold">{imgSlideRemaining} Img/Slide</span>
          <span className="text-zinc-600 hidden md:inline">•</span>
          <span className="text-violet-400 font-semibold hidden md:inline">{videoSecsRemaining}s Video</span>
          <ChevronDown className="w-3 h-3 text-zinc-500 ml-0.5" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-80 p-4 bg-zinc-900 border-white/10 text-white rounded-xl shadow-2xl">
        <DropdownMenuLabel className="p-0 mb-3 flex items-center justify-between">
          <span className="font-semibold text-sm flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-blue-400" /> AI Balance & Allowances
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Active
          </span>
        </DropdownMenuLabel>
        
        <DropdownMenuSeparator className="bg-white/10 mb-3" />

        {exhaustionMessages.length > 0 && (
          <div className="mb-3 p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300 flex items-start gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              {exhaustionMessages.map((m, i) => (
                <p key={i}>{m}</p>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-2.5 text-xs">
          <div className="flex items-center justify-between p-2 rounded-lg bg-white/5">
            <span className="flex items-center gap-1.5 text-zinc-400">
              <Layers className="w-3.5 h-3.5 text-blue-400" /> Image / Slide Generations
            </span>
            <span className="font-semibold text-white">{imgSlideRemaining} left</span>
          </div>

          <div className="flex items-center justify-between p-2 rounded-lg bg-white/5">
            <span className="flex items-center gap-1.5 text-zinc-400">
              <Video className="w-3.5 h-3.5 text-violet-400" /> Video Generations
            </span>
            <span className="font-semibold text-white">{videoSecsRemaining}s left</span>
          </div>

          <div className="flex items-center justify-between p-2 rounded-lg bg-white/5">
            <span className="flex items-center gap-1.5 text-zinc-400">
              <MessageSquare className="w-3.5 h-3.5 text-emerald-400" /> Monthly Text Tokens
            </span>
            <span className="font-semibold text-white">{totalTextK}k tokens</span>
          </div>
        </div>

        {courseAllocations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-white/10">
            <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">Active Course Wallets</p>
            <div className="space-y-1.5 max-h-36 overflow-y-auto">
              {courseAllocations.map((c, i) => (
                <div key={i} className="p-2 rounded-lg bg-white/5 text-[11px] flex justify-between items-center">
                  <div>
                    <p className="font-medium text-white truncate max-w-[170px]">{c.course_name}</p>
                    <p className="text-[10px] text-zinc-400">
                      Expires: {c.course_end ? new Date(c.course_end).toLocaleDateString() : 'Active'}
                    </p>
                  </div>
                  <span className="font-semibold text-emerald-400">
                    ${((c.wallet_balance_minor || 0) / 100).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
