import React, { useState } from 'react';
import PanelEventFeed from './PanelEventFeed';
import PanelRiskGauge from './PanelRiskGauge';
import PanelWorldMap from './PanelWorldMap';
import PanelAuditLog from './PanelAuditLog';
import PanelAttackerIntelligence from './PanelAttackerIntelligence';

const DashboardLayout = ({ events, auditLog, systemStatus }) => {
  const [activeTab, setActiveTab] = useState('Dashboard');

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', backgroundColor: 'var(--bg-base)', overflow: 'hidden' }}>
      
      {/* Left Sidebar (220px fixed) */}
      <aside style={{ width: '220px', borderRight: '1px solid var(--border-strong)', padding: '24px 16px', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
        <div style={{ marginBottom: '40px' }}>
          <h1 className="mono text-gradient-cyan" style={{ fontSize: '18px', fontWeight: 700, margin: 0, letterSpacing: '0.05em' }}>
            SENTINEL_MESH
          </h1>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Threat Intel System
          </div>
        </div>

        <nav style={{ flex: 1 }}>
          {['Dashboard', 'Attacker Intelligence', 'Live Events', 'Audit Log', 'System Parameters'].map((nav) => {
            const isActive = activeTab === nav;
            return (
            <div key={nav} 
              onClick={() => setActiveTab(nav)}
              style={{ 
              padding: '10px 12px', 
              marginBottom: '4px',
              fontSize: '13px', 
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              backgroundColor: isActive ? 'var(--bg-surface-raised)' : 'transparent',
              borderLeft: isActive ? '2px solid var(--accent-cyan)' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: isActive ? 600 : 400,
              transition: 'all 0.2s ease'
            }}>
              {nav}
            </div>
          )})}
        </nav>

        {/* System Status bottom section */}
        <div style={{ 
          padding: '16px', 
          backgroundColor: 'var(--bg-surface)', 
          border: '1px solid var(--border-subtle)', 
          borderRadius: '4px' 
        }}>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.1em' }}>
            System Status
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ 
              width: '8px', height: '8px', borderRadius: '50%', 
              backgroundColor: systemStatus?.status === 'Healing active' ? 'var(--accent-red)' : 
                               systemStatus?.status === 'Alert' ? 'var(--accent-amber)' : 'var(--accent-cyan)',
              animation: 'pulse 1.5s infinite ease-in-out'
            }}></div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {systemStatus?.status || "Monitoring"}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Flex */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {activeTab === 'Dashboard' && (
          <>
            <div style={{ flex: '1 1 50%', minHeight: 0, padding: '16px 16px 8px 16px', overflow: 'hidden' }}>
                <PanelWorldMap events={events} />
            </div>
            <div style={{ flex: '1 1 50%', minHeight: 0, padding: '8px 16px 16px 16px', overflow: 'hidden' }}>
                <PanelEventFeed events={events} />
            </div>
          </>
        )}

        {activeTab === 'Live Events' && (
          <div style={{ flex: 1, padding: '16px', overflow: 'hidden' }}>
             <PanelEventFeed events={events} />
          </div>
        )}

        {activeTab === 'Attacker Intelligence' && (
          <div style={{ flex: 1, padding: '16px', overflow: 'hidden' }}>
             <PanelAttackerIntelligence />
          </div>
        )}

        {activeTab === 'Audit Log' && (
          <div style={{ flex: 1, padding: '16px', overflow: 'hidden' }}>
             <PanelAuditLog auditLog={auditLog} />
          </div>
        )}

        {activeTab === 'System Parameters' && (
          <div style={{ flex: 1, padding: '16px', display: 'flex', flexDirection: 'column' }}>
            <div className="panel" style={{ flex: 1, display:'flex', flexDirection:'column', justifyContent:'center', alignItems:'center', color: 'var(--text-secondary)' }}>
              <h2 className="text-gradient-cyan mono" style={{ fontSize:'24px', marginBottom:'16px' }}>System Parameters</h2>
              <div style={{ display:'flex', gap:'40px', textAlign:'left', marginTop:'20px' }}>
                 <div>
                   <p style={{ color:'var(--text-primary)', marginBottom:'8px' }}>Infrastructure Integration</p>
                   <li>Region: <code>eu-north-1</code></li>
                   <li>Gateway: <code>AWS API Gateway / ALB</code></li>
                   <li>Compute: <code>EC2 Amazon Linux 2023</code></li>
                   <li>Events: <code>S3 -&gt; SNS -&gt; Lambda</code></li>
                 </div>
                 <div>
                   <p style={{ color:'var(--text-primary)', marginBottom:'8px' }}>Intelligence Core</p>
                   <li>Provider: <code>GroqCloud</code></li>
                   <li>Model: <code>llama3-8b-8192</code></li>
                   <li>Heuristics: <code>IP Hist, Keyword Analysis</code></li>
                   <li>Threshold: <code>&ge; 70 Risk Score</code></li>
                 </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Right Sidebar (320px fixed) */}
      <aside style={{ width: '320px', borderLeft: '1px solid var(--border-strong)', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
        
        {/* Top right - Gauge */}
        <div style={{ height: '320px', padding: '16px 16px 8px 16px' }}>
           <PanelRiskGauge systemStatus={systemStatus} />
        </div>

        {/* Bottom right - Audit Log */}
        <div style={{ flex: 1, padding: '8px 16px 16px 16px', overflow: 'hidden' }}>
           <PanelAuditLog auditLog={auditLog} />
        </div>

      </aside>

    </div>
  );
};

export default DashboardLayout;
