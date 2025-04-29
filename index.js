import React from 'react';
import { createRoot } from 'react-dom/client'; // Updated import
import './index.css';
import App from './App';
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet"></link>
// Create a root
const root = createRoot(document.getElementById('root'));

// Initial render
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);