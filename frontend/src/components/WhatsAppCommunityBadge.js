import React, { useState, useEffect } from 'react';
import { MessageCircle, X } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export default function WhatsAppCommunityBadge() {
  const [communityUrl, setCommunityUrl] = useState('https://chat.whatsapp.com/');
  const [visible, setVisible] = useState(true);
  const [tooltip, setTooltip] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/whatsapp/community`)
      .then(r => r.json())
      .then(d => { if (d.url) setCommunityUrl(d.url); })
      .catch(() => {});
  }, []);

  if (!visible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      {tooltip && (
        <div className="bg-[#111] border border-white/10 rounded-xl px-4 py-3 shadow-xl text-sm text-white max-w-[220px] transition-all">
          <p className="font-semibold text-green-400 mb-1">AIIA WhatsApp Community 🌍</p>
          <p className="text-zinc-400 text-xs">Join prospective students, researchers, and professionals across Africa!</p>
        </div>
      )}
      <div className="relative flex items-center gap-2">
        <button 
          onClick={() => setVisible(false)} 
          className="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-500 hover:text-white transition-all text-xs"
          title="Dismiss"
        >
          <X className="w-3 h-3" />
        </button>
        <a
          href={communityUrl}
          target="_blank"
          rel="noopener noreferrer"
          onMouseEnter={() => setTooltip(true)}
          onMouseLeave={() => setTooltip(false)}
          className="w-14 h-14 rounded-full bg-green-500 hover:bg-green-400 flex items-center justify-center shadow-lg shadow-green-500/30 transition-all hover:scale-110 group relative"
          aria-label="Join Official WhatsApp Community"
        >
          <MessageCircle className="w-7 h-7 text-white" />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-400 border-2 border-[#09090B] rounded-full flex items-center justify-center text-[9px] text-zinc-900 font-bold animate-pulse">
            ●
          </span>
        </a>
      </div>
    </div>
  );
}
