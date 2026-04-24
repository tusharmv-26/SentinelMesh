import React, { useState } from 'react';

const MITREMatrixSimulator = ({ serverUrl }) => {
  const [simulating, setSimulating] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const tactics = [
    {
      id: "TA0001",
      name: "Initial Access",
      color: "#8B5CF6",
      techniques: [
        { id: "T1190", name: "Exploit Public-Facing App" },
        { id: "T1566", name: "Phishing" },
        { id: "T1078", name: "Valid Accounts" },
        { id: "T1133", name: "External Remote Services" },
        { id: "T1091", name: "Replication Through Removable Media" }
      ]
    },
    {
      id: "TA0002",
      name: "Execution",
      color: "#3B82F6",
      techniques: [
        { id: "T1059", name: "Command and Scripting Interpreter" },
        { id: "T1203", name: "Exploitation for Client Execution" },
        { id: "T1053", name: "Scheduled Task/Job" },
        { id: "T1047", name: "Windows Management Instrumentation" },
        { id: "T1204", name: "User Execution" }
      ]
    },
    {
      id: "TA0003",
      name: "Persistence",
      color: "#F97316",
      techniques: [
        { id: "T1098", name: "Account Manipulation" },
        { id: "T1136", name: "Create Account" },
        { id: "T1543", name: "Create or Modify System Process" },
        { id: "T1546", name: "Event Triggered Execution" },
        { id: "T1505", name: "Server Software Component" }
      ]
    },
    {
      id: "TA0006",
      name: "Credential Access",
      color: "#F59E0B",
      techniques: [
        { id: "T1110", name: "Brute Force" },
        { id: "T1552", name: "Unsecured Credentials" },
        { id: "T1528", name: "Steal Application Access Token" },
        { id: "T1003", name: "OS Credential Dumping" },
        { id: "T1555", name: "Credentials from Password Stores" }
      ]
    },
    {
      id: "TA0007",
      name: "Discovery",
      color: "#EC4899",
      techniques: [
        { id: "T1580", name: "Cloud Infrastructure Discovery" },
        { id: "T1619", name: "Cloud Storage Object Discovery" },
        { id: "T1087", name: "Account Discovery" },
        { id: "T1082", name: "System Information Discovery" },
        { id: "T1046", name: "Network Service Discovery" }
      ]
    }
  ];

  const handleSimulate = async (technique, tactic) => {
    setSimulating(technique.id);
    setSuccessMsg(null);
    try {
      const res = await fetch(`${serverUrl}/simulate-mitre-path`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          technique_id: technique.id,
          technique_name: technique.name,
          tactic: tactic.name
        })
      });
      
      const data = await res.json();
      if (res.ok) {
        setSuccessMsg(`Simulated attacker chose ${technique.id}. Honeypot [${data.honeypot.resource_name}] deployed to trap them!`);
        setTimeout(() => setSuccessMsg(null), 5000);
      }
    } catch (e) {
      console.error(e);
    }
    setSimulating(null);
  };

  return (
    <div className="panel" style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Interactive MITRE ATT&CK® Matrix Simulator</span>
        <div style={{ fontSize: '11px', color: '#9CA3AF', fontWeight: 'normal' }}>
          Click any technique to simulate an attack path. SentinelMesh will instantly synthesize a honeypot to trap it.
        </div>
      </div>
      
      {successMsg && (
        <div style={{ 
          background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10B981', color: '#10B981', 
          padding: '10px 16px', margin: '16px 16px 0 16px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' 
        }}>
          {successMsg}
        </div>
      )}

      <div style={{ flex: 1, overflowX: 'auto', overflowY: 'auto', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '8px', minWidth: '800px' }}>
          {tactics.map(tactic => (
            <div key={tactic.id} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ 
                background: `linear-gradient(180deg, ${tactic.color}22 0%, transparent 100%)`, 
                borderTop: `2px solid ${tactic.color}`,
                padding: '12px 8px',
                borderRadius: '4px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: tactic.color }}>{tactic.name}</div>
                <div style={{ fontSize: '10px', color: '#6B7280' }}>{tactic.techniques.length} techniques</div>
              </div>
              
              {tactic.techniques.map(tech => (
                <button
                  key={tech.id}
                  onClick={() => handleSimulate(tech, tactic)}
                  disabled={simulating === tech.id}
                  style={{
                    background: simulating === tech.id ? '#1E2533' : 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '4px',
                    padding: '8px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
                    e.currentTarget.style.borderColor = tactic.color;
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                  }}
                >
                  <div style={{ fontSize: '10px', fontFamily: 'monospace', color: tactic.color, marginBottom: '4px' }}>
                    {tech.id}
                  </div>
                  <div style={{ fontSize: '11px', color: '#E5E7EB', lineHeight: 1.2 }}>
                    {simulating === tech.id ? 'Synthesizing...' : tech.name}
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MITREMatrixSimulator;
