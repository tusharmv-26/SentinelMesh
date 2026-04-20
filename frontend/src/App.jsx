import React, { useState, useEffect } from 'react';
import DashboardLayout from './components/DashboardLayout';
import LandingPage from './components/LandingPage';

function App() {
  const [showDashboard, setShowDashboard] = useState(false);
  const [events, setEvents] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [systemStatus, setSystemStatus] = useState({
    status: "Monitoring",
    peak_score: 0,
    total_events: 0,
    total_healing: 0
  });

  // Polling architecture every 3 seconds as required by PRD
  useEffect(() => {
    if (!showDashboard) return;

    const fetchData = async () => {
      try {
        const eventsRes = await fetch('http://13.48.58.234:8000/events', { method: 'GET' });
        const auditRes = await fetch('http://13.48.58.234:8000/audit', { method: 'GET' });
        const statusRes = await fetch('http://13.48.58.234:8000/status', { method: 'GET' });
        
        if (eventsRes.ok) setEvents(await eventsRes.json());
        if (auditRes.ok) setAuditLog(await auditRes.json());
        if (statusRes.ok) setSystemStatus(await statusRes.json());
      } catch (err) {
        console.error("Failed to connect to backend", err);
      }
    };
    
    // Fetch immediately on mount of dashboard
    fetchData();

    // Setup polling
    const id = setInterval(fetchData, 3000);
    return () => clearInterval(id);
  }, [showDashboard]);

  if (!showDashboard) {
    return <LandingPage onEnter={() => setShowDashboard(true)} />;
  }

  return (
    <div className="App fade-in">
      <DashboardLayout
        events={events}
        auditLog={auditLog}
        systemStatus={systemStatus}
      />
    </div>
  );
}

export default App;
