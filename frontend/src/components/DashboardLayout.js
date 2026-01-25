import React from 'react';
import { Sidebar } from './Sidebar';
import { NotificationBanner } from './NotificationBanner';

export const DashboardLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#09090B]">
      <Sidebar />
      <main className="ml-64">
        <NotificationBanner />
        {children}
      </main>
    </div>
  );
};
