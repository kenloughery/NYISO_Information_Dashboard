/**
 * Main layout component for the dashboard
 */

import type { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-lg sm:text-xl md:text-2xl font-bold">New York Power Market (NYISO) Dashboard</h1>
          </div>
                 <div className="flex items-center gap-4">
                   <span className="text-sm text-slate-500">Built by Ken with Cursor AI</span>
                 </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full">
        {children}
      </main>
    </div>
  );
};

