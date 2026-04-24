import React, { useState, useEffect } from 'react';

const APTSuspects = ({ serverUrl }) => {
  const [suspects, setSuspects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAPT = async () => {
      try {
        const response = await fetch(`${serverUrl}/apt/suspects`);
        const data = await response.json();
        setSuspects(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch APT data:', error);
        setLoading(false);
      }
    };

    fetchAPT();
    const interval = setInterval(fetchAPT, 3000);
    return () => clearInterval(interval);
  }, [serverUrl]);

  const getClassificationColor = (classification) => {
    if (classification === 'CONFIRMED_APT_PATTERN') {
      return '#DC2626'; // Red
    }
    return '#EF4444'; // Orange-red
  };

  const getClassificationLabel = (classification) => {
    if (classification === 'CONFIRMED_APT_PATTERN') {
      return 'CONFIRMED APT';
    }
    return 'SUSPECTED APT';
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span>APT Activity</span>
      </div>
      <div style={{ padding: '16px', height: 'calc(100% - 40px)', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', color: '#9CA3AF', paddingTop: '20px' }}>Loading...</div>
        ) : suspects.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#9CA3AF', paddingTop: '20px' }}>No APT activity detected</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {suspects.map((suspect) => (
              <div
                key={suspect.ip}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: `2px solid ${getClassificationColor(suspect.classification)}66`,
                  borderRadius: '8px',
                  padding: '12px',
                  backdropFilter: 'blur(10px)',
                  boxShadow: `0 0 12px ${getClassificationColor(suspect.classification)}22`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div
                    style={{
                      fontSize: '11px',
                      fontFamily: 'JetBrains Mono, monospace',
                      color: '#E5E7EB',
                      fontWeight: 'bold'
                    }}
                  >
                    {suspect.ip}
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      background: `${getClassificationColor(suspect.classification)}22`,
                      color: getClassificationColor(suspect.classification),
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: 'bold'
                    }}
                  >
                    <div
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        backgroundColor: getClassificationColor(suspect.classification),
                        animation: suspect.classification === 'CONFIRMED_APT_PATTERN' ? 'pulse 2s infinite' : 'none'
                      }}
                    />
                    {getClassificationLabel(suspect.classification)}
                  </div>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
                  <div>
                    <div style={{ fontSize: '10px', color: '#9CA3AF' }}>APT Score</div>
                    <div style={{ fontSize: '14px', fontWeight: 'bold', color: getClassificationColor(suspect.classification) }}>
                      {suspect.apt_score}/100
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: '#9CA3AF' }}>Events</div>
                    <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#E5E7EB' }}>
                      {suspect.event_count}
                    </div>
                  </div>
                </div>

                {suspect.indicators.length > 0 && (
                  <div style={{ fontSize: '10px', color: '#9CA3AF', marginTop: '8px' }}>
                    <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>Indicators:</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {suspect.indicators.slice(0, 3).map((ind, idx) => (
                        <span
                          key={idx}
                          style={{
                            background: `${getClassificationColor(suspect.classification)}11`,
                            color: getClassificationColor(suspect.classification),
                            padding: '2px 6px',
                            borderRadius: '3px',
                            fontSize: '9px',
                            border: `1px solid ${getClassificationColor(suspect.classification)}33`
                          }}
                        >
                          {ind}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default APTSuspects;
