import React from 'react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';

const PanelRiskGauge = ({ systemStatus }) => {
  const peak = systemStatus?.peak_score || 0;
  // amber below 70, red above 70
  const color = peak >= 70 ? '#EF4444' : (peak > 0 ? '#F59E0B' : '#00C4CC');
  
  // Recharts requires specific data structures for multiple concentric bars
  // We'll create mock data for the inner rings (events in last 10m, healing actions) as requested
  const eventsCount = Math.min((systemStatus?.total_events || 0) * 2, 100); 
  const healCount = Math.min((systemStatus?.total_healing || 0) * 10 + 10, 100);

  const data = [
    { name: 'Self-Heals', value: healCount, fill: '#1E2533' }, // innermost grey
    { name: 'Event Rate', value: eventsCount, fill: '#2A3347' }, // middle dark 
    { name: 'Risk Score', value: peak, fill: color } // outer color
  ];

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <span>Risk Assessment</span>
      </div>
      <div style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        
        <div style={{ flex: 1, width: '100%', minHeight: 200 }}>
          <ResponsiveContainer width="100%" height="100%" debounce={300}>
            <RadialBarChart 
              cx="50%" 
              cy="50%" 
              innerRadius="50%" 
              outerRadius="100%" 
              barSize={12} 
              data={data} 
              startAngle={90} 
              endAngle={-270}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
              <RadialBar 
                minAngle={15} 
                background={{ fill: 'rgba(255, 255, 255, 0.02)' }} 
                clockWise 
                dataKey="value" 
                cornerRadius={4}
                animationDuration={800}
              />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Center overlay number */}
        <div style={{ 
          position: 'absolute', 
          top: '45%', left: '50%', 
          transform: 'translate(-50%, -50%)',
          textAlign: 'center'
        }}>
          <div className="mono text-primary" style={{ fontSize: '42px', fontWeight: 700, lineHeight: 1 }}>
            {peak}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Peak Risk
          </div>
        </div>

        {/* Legend */}
        <div style={{ padding: '0 16px 16px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
           <LegendItem label="Peak Risk Score" value={peak} color={color} />
           <LegendItem label="Events Today" value={systemStatus?.total_events || 0} color="#2A3347" />
           <LegendItem label="Auto-Heals" value={systemStatus?.total_healing || 0} color="#1E2533" />
        </div>

      </div>
    </div>
  );
};

const LegendItem = ({ label, value, color }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ width: '12px', height: '4px', backgroundColor: color, borderRadius: '2px' }}></div>
      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{label}</span>
    </div>
    <span className="mono text-primary" style={{ fontSize: '13px', fontWeight: 600 }}>{value}</span>
  </div>
);

export default PanelRiskGauge;
