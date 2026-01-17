import React from 'react';
import { Sidebar } from './Sidebar';

export const DashboardLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#09090B]">
      <Sidebar />
      <main className="ml-64">
        {children}
      </main>
    </div>
  );
};
