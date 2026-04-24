import React, { useState, useEffect } from 'react';

const PanelHoneypots = ({ serverUrl }) => {
  const [honeypots, setHoneypots] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHoneypots = async () => {
      try {
        const response = await fetch(`${serverUrl}/honeypots`);
        const data = await response.json();
        setHoneypots(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch honeypots:', error);
        setLoading(false);
      }
    };

    fetchHoneypots();
    const interval = setInterval(fetchHoneypots, 3000);
    return () => clearInterval(interval);
  }, [serverUrl]);

  const getModeColor = (mode) => {
    switch (mode) {
      case 'PASSIVE':
        return '#60A5FA'; // Blue
      case 'ACTIVE':
        return '#FBBF24'; // Amber
      case 'DECEPTION_MODE':
        return '#EF4444'; // Red
      default:
        return '#9CA3AF'; // Gray
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span>Honeypot Status</span>
      </div>
      <div style={{ padding: '16px', height: 'calc(100% - 40px)', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', color: '#9CA3AF', paddingTop: '20px' }}>Loading...</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            {honeypots.map((hp) => (
              <div
                key={hp.name}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                  borderRadius: '8px',
                  padding: '12px',
                  backdropFilter: 'blur(10px)'
                }}
              >
                <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '8px' }}>
                  {hp.name}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: getModeColor(hp.mode),
                      boxShadow: `0 0 12px ${getModeColor(hp.mode)}`
                    }}
                  />
                  <span style={{ fontSize: '12px', fontWeight: 'bold' }}>
                    {hp.mode}
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: '#6B7280', marginTop: '8px' }}>
                  Hits: {hp.total_hits}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PanelHoneypots;
