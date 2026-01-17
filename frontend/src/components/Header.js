import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getNotifications, markNotificationRead } from '../services/api';
import { Bell, Search, User, ChevronDown } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';

export const Header = ({ title, subtitle }) => {
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      const data = await getNotifications();
      setNotifications(data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      await markNotificationRead(notification.id);
      loadNotifications();
    }
  };

  const getInitials = (name) => {
    return name
      ?.split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'U';
  };

  const getRoleBadge = (role) => {
    const colors = {
      admin: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
      teacher: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      student: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      parent: 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    };
    return colors[role] || colors.student;
  };

  return (
    <header className="sticky top-0 z-40 bg-[#09090B]/80 backdrop-blur-xl border-b border-white/5">
      <div className="flex items-center justify-between px-8 py-4">
        {/* Title */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          {subtitle && <p className="text-sm text-zinc-500 mt-0.5">{subtitle}</p>}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative hidden md:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Search..."
              data-testid="header-search"
              className="w-64 pl-10 pr-4 py-2 bg-zinc-900/50 border border-white/10 rounded-lg text-sm placeholder:text-zinc-500 focus:outline-none focus:border-blue-500/50 transition-colors"
            />
          </div>

          {/* Notifications */}
          <DropdownMenu open={showNotifications} onOpenChange={setShowNotifications}>
            <DropdownMenuTrigger asChild>
              <button
                data-testid="notifications-btn"
                className="relative p-2 rounded-lg hover:bg-white/5 transition-colors"
              >
                <Bell className="w-5 h-5 text-zinc-400" />
                {unreadCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-blue-500 rounded-full text-[10px] font-bold flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80 bg-zinc-900 border-white/10">
              <DropdownMenuLabel className="text-zinc-400">Notifications</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-white/10" />
              {notifications.length === 0 ? (
                <div className="p-4 text-center text-zinc-500 text-sm">
                  No notifications yet
                </div>
              ) : (
                notifications.slice(0, 5).map((notification) => (
                  <DropdownMenuItem
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`flex flex-col gap-1 p-3 cursor-pointer ${
                      !notification.is_read ? 'bg-blue-500/5' : ''
                    }`}
                  >
                    <span className="font-medium text-sm">{notification.title}</span>
                    <span className="text-xs text-zinc-500 line-clamp-2">{notification.message}</span>
                  </DropdownMenuItem>
                ))
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                data-testid="user-menu-btn"
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
              >
                <Avatar className="w-8 h-8">
                  <AvatarImage src={user?.profile_image} />
                  <AvatarFallback className="bg-gradient-to-br from-blue-500 to-violet-500 text-white text-xs">
                    {getInitials(user?.full_name)}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium">{user?.full_name}</p>
                  <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${getRoleBadge(user?.role)}`}>
                    {user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
                  </Badge>
                </div>
                <ChevronDown className="w-4 h-4 text-zinc-500 hidden md:block" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-zinc-900 border-white/10">
              <DropdownMenuLabel className="text-zinc-400">My Account</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-white/10" />
              <DropdownMenuItem className="cursor-pointer">
                <User className="w-4 h-4 mr-2" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer text-red-400" onClick={logout}>
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
};
