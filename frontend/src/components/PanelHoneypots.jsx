import React, { useState, useEffect } from 'react';

const PanelHoneypots = ({ serverUrl }) => {
  const [honeypots, setHoneypots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHoneypots = async () => {
      try {
        const response = await fetch(`${serverUrl}/honeypots`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        // Ensure data is array
        const honeypotsArray = Array.isArray(data) ? data : [];
        setHoneypots(honeypotsArray);
        setError(null);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch honeypots:', error);
        setError(error.message);
        setHoneypots([]);
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

  const getTrinityBadges = (hp) => {
    if (hp.type !== 'DYNAMIC_TRAP') return null;
    
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '12px' }}>
        <div style={{ fontSize: '9px', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ padding: '2px 4px', background: 'rgba(252, 211, 77, 0.1)', color: '#FCD34D', border: '1px solid rgba(252, 211, 77, 0.3)', borderRadius: '3px' }}>TRACKING TOKEN</span>
          <span style={{ color: '#9CA3AF' }}>{hp.canary_token}</span>
        </div>
        <div style={{ fontSize: '9px', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ padding: '2px 4px', background: 'rgba(96, 165, 250, 0.1)', color: '#60A5FA', border: '1px solid rgba(96, 165, 250, 0.3)', borderRadius: '3px' }}>INTENT LOGGER</span>
          <span style={{ color: '#9CA3AF' }}>{hp.intent_analysis}</span>
        </div>
        <div style={{ fontSize: '9px', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ padding: '2px 4px', background: 'rgba(239, 68, 68, 0.1)', color: '#EF4444', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '3px' }}>VULN EXPOSED</span>
          <span style={{ color: '#9CA3AF' }}>{hp.vuln_profile}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span>Honeypot Status</span>
      </div>
      <div style={{ padding: '16px', height: 'calc(100% - 40px)', overflowY: 'auto', minHeight: 0 }}>
        {error ? (
          <div style={{ textAlign: 'center', color: '#EF4444', paddingTop: '20px' }}>Error: {error}</div>
        ) : loading ? (
          <div style={{ textAlign: 'center', color: '#9CA3AF', paddingTop: '20px' }}>Loading...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {(Array.isArray(honeypots) ? honeypots : []).map((hp) => (
              <div
                key={hp.name}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                  borderLeft: `4px solid ${getModeColor(hp.mode)}`,
                  borderRadius: '8px',
                  padding: '20px',
                  backdropFilter: 'blur(10px)'
                }}
              >
                <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '8px' }}>
                  <span>{hp.name}</span>
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
                <div style={{ fontSize: '12px', color: '#6B7280', marginTop: '12px' }}>
                  Total Attacker Engagements: {hp.total_hits}
                </div>
                
                {getTrinityBadges(hp)}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PanelHoneypots;
