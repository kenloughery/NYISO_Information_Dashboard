import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './services/queryClient';
import './index.css';
import App from './App.tsx';

// Scroll to top on initial page load
window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
document.documentElement.scrollTop = 0;
document.body.scrollTop = 0;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
    <App />
    </QueryClientProvider>
  </StrictMode>,
);
