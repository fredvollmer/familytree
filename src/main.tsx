import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import FamilyExplorer from '../app/family-explorer';
import '../app/globals.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <FamilyExplorer />
  </StrictMode>,
);
