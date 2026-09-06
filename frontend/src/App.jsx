import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { Cameras } from './pages/Cameras';
import { Zones } from './pages/Zones';
import { Events } from './pages/Events';
import { useCameras } from './hooks/useCameras';
import { useEvents } from './hooks/useEvents';
import './App.css';

export function App() {
  const {
    cameras,
    healthMap,
    globalHealth,
    startStream,
    stopStream,
    deleteCamera,
    createCamera,
  } = useCameras(3000);

  const { events, wsStatus, clearEvents } = useEvents(50);

  return (
    <Router>
      <div className="app-shell">
        <Navbar wsStatus={wsStatus} globalHealth={globalHealth} />

        <main className="app-main">
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  cameras={cameras}
                  healthMap={healthMap}
                  globalHealth={globalHealth}
                  events={events}
                  onStart={startStream}
                  onStop={stopStream}
                  onClearEvents={clearEvents}
                />
              }
            />
            <Route
              path="/cameras"
              element={
                <Cameras
                  cameras={cameras}
                  healthMap={healthMap}
                  onStart={startStream}
                  onStop={stopStream}
                  onDelete={deleteCamera}
                  onCreate={createCamera}
                />
              }
            />
            <Route path="/zones" element={<Zones cameras={cameras} healthMap={healthMap} />} />
            <Route path="/events" element={<Events cameras={cameras} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
