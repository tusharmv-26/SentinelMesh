import React, { useState, useEffect } from 'react';

const MITREHeatmap = ({ serverUrl }) => {
  const [techniques, setTechniques] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMITRE = async () => {
      try {
        const response = await fetch(`${serverUrl}/mitre/summary`);
        const data = await response.json();
        setTechniques(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch MITRE data:', error);
        setLoading(false);
      }
    };

    fetchMITRE();
    const interval = setInterval(fetchMITRE, 3000);
    return () => clearInterval(interval);
  }, [serverUrl]);

  const getTacticColor = (tactic) => {
    const colors = {
      'Reconnaissance': '#8B5CF6',
      'Discovery': '#EC4899',
      'Credential Access': '#F59E0B',
      'Lateral Movement': '#EF4444',
      'Collection': '#06B6D4',
      'Persistence': '#F97316',
      'Exfiltration': '#DC2626'
    };
    return colors[tactic] || '#9CA3AF';
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span>MITRE ATT&CK Techniques</span>
      </div>
      <div style={{ padding: '16px', height: 'calc(100% - 40px)', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', color: '#9CA3AF', paddingTop: '20px' }}>Loading...</div>
        ) : techniques.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#9CA3AF', paddingTop: '20px' }}>No techniques detected</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {techniques.slice(0, 10).map((tech) => (
              <div
                key={tech.technique_id}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${getTacticColor(tech.tactic)}33`,
                  borderRadius: '6px',
                  padding: '12px',
                  backdropFilter: 'blur(10px)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div
                      style={{
                        fontSize: '11px',
                        fontFamily: 'JetBrains Mono, monospace',
                        color: getTacticColor(tech.tactic),
                        fontWeight: 'bold'
                      }}
                    >
                      {tech.technique_id}
                    </div>
                    <div style={{ fontSize: '12px', color: '#E5E7EB', marginTop: '4px' }}>
                      {tech.name}
                    </div>
                    <div style={{ fontSize: '10px', color: '#9CA3AF', marginTop: '2px' }}>
                      {tech.tactic}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '14px', fontWeight: 'bold', color: getTacticColor(tech.tactic) }}>
                      {tech.count}
                    </div>
                    <div style={{ fontSize: '10px', color: '#6B7280' }}>
                      hits
                    </div>
                  </div>
                </div>
                <div style={{ marginTop: '8px', height: '4px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.min(tech.highest_confidence * 100, 100)}%`,
                      background: getTacticColor(tech.tactic)
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MITREHeatmap;
