import React, { useState, useEffect } from 'react';

const DevSecOpsCoverage = ({ serverUrl }) => {
  const [coverage, setCoverage] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCoverage = async () => {
      try {
        const [coverageRes, summaryRes] = await Promise.all([
          fetch(`${serverUrl}/devsecops/coverage`),
          fetch(`${serverUrl}/devsecops/coverage-summary`)
        ]);
        
        const coverageData = await coverageRes.json();
        const summaryData = await summaryRes.json();
        
        setCoverage(coverageData);
        setSummary(summaryData);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch coverage data:', error);
        setLoading(false);
      }
    };

    fetchCoverage();
    const interval = setInterval(fetchCoverage, 3000);
    return () => clearInterval(interval);
  }, [serverUrl]);

  const getCoverageColor = (status) => {
    switch (status) {
      case 'MONITORED':
        return '#10B981'; // Green
      case 'PARTIAL':
        return '#F59E0B'; // Amber
      case 'UNMONITORED':
        return '#EF4444'; // Red
      default:
        return '#9CA3AF'; // Gray
    }
  };

  const getCoverageLabel = (status) => {
    switch (status) {
      case 'MONITORED':
        return '✓ Monitored';
      case 'PARTIAL':
        return '◐ Partial';
      case 'UNMONITORED':
        return '✗ Unmonitored';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span>DevSecOps Coverage</span>
      </div>
      <div style={{ padding: '16px', height: 'calc(100% - 40px)', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', color: '#9CA3AF', paddingTop: '20px' }}>Loading...</div>
        ) : (
          <>
            {summary && (
              <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '6px' }}>
                <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '8px' }}>Coverage Summary</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: '#10B981' }}>Monitored</div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#10B981' }}>
                      {summary.monitored}/{summary.total_services}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: '#06B6D4' }}>Coverage</div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#06B6D4' }}>
                      {summary.coverage_percentage.toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            )}

            {coverage.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#9CA3AF', paddingTop: '10px' }}>No deployments recorded</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {coverage.map((svc) => (
                  <div
                    key={svc.service_name}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: `1px solid ${getCoverageColor(svc.coverage_status)}33`,
                      borderRadius: '6px',
                      padding: '12px',
                      backdropFilter: 'blur(10px)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#E5E7EB' }}>
                          {svc.service_name}
                        </div>
                        <div style={{ fontSize: '10px', color: '#9CA3AF', marginTop: '2px' }}>
                          v{svc.version} • {svc.environment}
                        </div>
                      </div>
                      <div
                        style={{
                          color: getCoverageColor(svc.coverage_status),
                          fontSize: '11px',
                          fontWeight: 'bold',
                          background: `${getCoverageColor(svc.coverage_status)}22`,
                          padding: '4px 8px',
                          borderRadius: '4px'
                        }}
                      >
                        {getCoverageLabel(svc.coverage_status)}
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '10px', color: '#9CA3AF' }}>
                      <div>
                        Covered: <span style={{ color: '#10B981' }}>{svc.covered_assets_count}</span>
                      </div>
                      <div>
                        Uncovered: <span style={{ color: '#EF4444' }}>{svc.uncovered_assets_count}</span>
                      </div>
                    </div>

                    {svc.uncovered_assets_count > 0 && (
                      <div style={{ marginTop: '8px', fontSize: '10px', color: '#EF4444' }}>
                        Suggested: <strong>{svc.suggested_honeypot}</strong>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default DevSecOpsCoverage;
