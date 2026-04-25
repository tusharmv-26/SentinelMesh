import React, { useState } from 'react';
import PanelEventFeed from './PanelEventFeed';
import PanelRiskGauge from './PanelRiskGauge';
import PanelWorldMap from './PanelWorldMap';
import PanelAuditLog from './PanelAuditLog';
import PanelAttackerIntelligence from './PanelAttackerIntelligence';
import PanelHoneypots from './PanelHoneypots';
import MITREMatrixSimulator from './MITREMatrixSimulator';
import APTSuspects from './APTSuspects';

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
          {['Dashboard', 'Attacker Intelligence', 'Live Events', 'Audit Log', 'Honeypots', 'MITRE Simulator', 'APT Activity', 'System Parameters'].map((nav) => {
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
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
            <div style={{ flex: '1 1 50%', minHeight: 0, padding: '16px 16px 8px 16px', overflow: 'hidden' }}>
                <PanelWorldMap events={events} />
            </div>
            <div style={{ flex: '1 1 50%', minHeight: 0, padding: '8px 16px 16px 16px', overflow: 'hidden' }}>
                <PanelEventFeed events={events} />
            </div>
          </div>
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



        {activeTab === 'Honeypots' && (
          <div style={{ flex: 1, padding: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', minHeight: 0, overflow: 'hidden' }}>
            <div style={{ minHeight: 0, minWidth: 0, overflow: 'hidden' }}>
              <PanelHoneypots serverUrl="http://localhost:8000" />
            </div>
            <div style={{ minHeight: 0, minWidth: 0, overflow: 'hidden' }}>
              {/* MITRE Heatmap removed per user request */}
            </div>
          </div>
        )}



        {activeTab === 'MITRE Simulator' && (
          <div style={{ flex: 1, padding: '16px', overflow: 'hidden' }}>
            <MITREMatrixSimulator serverUrl="http://localhost:8000" />
          </div>
        )}

        {activeTab === 'APT Activity' && (
          <div style={{ flex: 1, padding: '16px', overflow: 'hidden' }}>
            <APTSuspects serverUrl="http://localhost:8000" />
          </div>
        )}



        {activeTab === 'System Parameters' && (
          <div style={{ flex: 1, padding: '16px', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
                <div style={{ padding: '32px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: '4px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <div style={{ marginBottom: '32px' }}>
                        <h2 className="mono text-gradient-cyan" style={{ fontSize: '24px', color: 'var(--text-primary)', marginBottom: '8px', letterSpacing: '0.05em' }}>CORE SYSTEM ARCHITECTURE</h2>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Operational parameters, cloud integration flags, and intelligence routing configurations.</p>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '24px' }}>
                        {/* Infrastructure Box */}
                        <div style={{ backgroundColor: 'var(--bg-surface-raised)', border: '1px solid var(--border-strong)', borderRadius: '4px', padding: '24px', display: 'flex', flexDirection: 'column', boxShadow: '0 4px 6px rgba(0,0,0,0.2)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px' }}>
                                <span style={{ fontSize: '24px' }}>☁️</span>
                                <div>
                                    <h3 style={{ fontSize: '14px', color: 'var(--accent-cyan)', letterSpacing: '0.05em', textTransform: 'uppercase' }} className="mono">AWS Infrastructure</h3>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Cloud compute & ingress network</div>
                                </div>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Primary Region</span>
                                    <span className="mono" style={{ color: 'var(--text-primary)', fontSize: '12px', backgroundColor: 'var(--bg-base)', padding: '6px 12px', borderRadius: '4px', border: '1px solid var(--border-strong)' }}>eu-north-1</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Gateway Routing</span>
                                    <span className="mono" style={{ color: 'var(--text-primary)', fontSize: '12px', backgroundColor: 'var(--bg-base)', padding: '6px 12px', borderRadius: '4px', border: '1px solid var(--border-strong)' }}>API Gateway / ALB</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Compute Node</span>
                                    <span className="mono" style={{ color: 'var(--text-primary)', fontSize: '12px', backgroundColor: 'var(--bg-base)', padding: '6px 12px', borderRadius: '4px', border: '1px solid var(--border-strong)' }}>EC2 Amazon Linux</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Event Pipeline</span>
                                    <span className="mono" style={{ color: 'var(--accent-amber)', fontSize: '12px', backgroundColor: 'var(--accent-amber-dim)', padding: '6px 12px', borderRadius: '4px', border: '1px solid var(--accent-amber)', boxShadow: '0 0 10px rgba(245, 158, 11, 0.1)' }}>S3 → SNS → Lambda</span>
                                </div>
                            </div>
                        </div>

                        {/* Intelligence Box */}
                        <div style={{ backgroundColor: 'var(--bg-surface-raised)', border: '1px solid var(--border-strong)', borderRadius: '4px', padding: '24px', display: 'flex', flexDirection: 'column', boxShadow: '0 4px 6px rgba(0,0,0,0.2)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px' }}>
                                <span style={{ fontSize: '24px' }}>🧠</span>
                                <div>
                                    <h3 style={{ fontSize: '14px', color: '#a855f7', letterSpacing: '0.05em', textTransform: 'uppercase' }} className="mono">Intelligence Core</h3>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>AI heuristics & inference engine</div>
                                </div>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>LLM Provider</span>
                                    <span className="mono" style={{ color: 'var(--text-primary)', fontSize: '12px', backgroundColor: 'var(--bg-base)', padding: '6px 12px', borderRadius: '4px', border: '1px solid var(--border-strong)' }}>GroqCloud API</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Inference Model</span>
                                    <span className="mono" style={{ color: '#d8b4fe', fontSize: '12px', backgroundColor: '#3b0764', padding: '6px 12px', borderRadius: '4px', border: '1px solid #9333ea', boxShadow: '0 0 10px rgba(147, 51, 234, 0.15)' }}>Llama-3-8b-8192</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Engine Modules</span>
                                    <span className="mono" style={{ color: 'var(--text-primary)', fontSize: '12px', backgroundColor: 'var(--bg-base)', padding: '6px 12px', borderRadius: '4px', border: '1px solid var(--border-strong)' }}>IP Hist, Tor, Behaviors</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Action Threshold</span>
                                    <span className="mono" style={{ color: 'var(--accent-red)', fontSize: '12px', backgroundColor: 'var(--accent-red-dim)', padding: '6px 12px', borderRadius: '4px', border: '1px solid var(--accent-red)', boxShadow: '0 0 10px rgba(239, 68, 68, 0.15)' }}>≥ 70 Risk Score</span>
                                </div>
                            </div>
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
