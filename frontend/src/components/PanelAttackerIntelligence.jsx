import React, { useState, useEffect } from 'react';

const PanelAttackerIntelligence = () => {
    const [profiles, setProfiles] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchProfiles = async () => {
        try {
            const res = await fetch('http://13.61.240.101:8000/profiles');
            const data = await res.json();
            setProfiles(Array.isArray(data) ? data : []);
            setLoading(false);
        } catch (err) {
            console.error("Error fetching profiles:", err);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProfiles();
        const interval = setInterval(fetchProfiles, 3000);
        return () => clearInterval(interval);
    }, []);

    const getThreatColor = (t) => {
        switch (t) {
            case 'CRITICAL': return 'var(--accent-red)';
            case 'HIGH': return 'var(--accent-amber)';
            case 'MEDIUM': return '#eab308'; // raw yellow
            case 'LOW': return 'var(--accent-green)';
            default: return 'var(--text-secondary)';
        }
    };
    
    const getEscalationColor = (score) => {
        if (score >= 75) return 'var(--accent-red)';
        if (score >= 50) return 'var(--accent-amber)';
        if (score >= 25) return '#eab308';
        return 'var(--accent-green)';
    };

    const getBehaviorIcon = (b) => {
        switch (b) {
            case 'AUTOMATED_SCANNER': return '🤖';
            case 'MANUAL_ATTACKER': return '👤';
            case 'AGGRESSIVE_ENUMERATION': return '⚡';
            case 'RECONNAISSANCE': return '🔍';
            default: return '❓';
        }
    };

    const getIntentIcon = (i) => {
        switch (i) {
            case 'CREDENTIAL_HARVESTING': return '🔐';
            case 'DATA_EXFILTRATION': return '📤';
            case 'FINANCIAL_TARGETING': return '💰';
            case 'TARGETED_ATTACK': return '🎯';
            case 'BROAD_RECONNAISSANCE': return '📡';
            default: return '❓';
        }
    };

    if (loading && profiles.length === 0) {
        return (
            <div style={{ height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div className="mono" style={{ color: 'var(--accent-cyan)', fontSize: '13px', marginBottom: '8px' }}>⟳ INTELLIGENCE MATRIX INITIALIZING</div>
                </div>
            </div>
        );
    }

    return (
        <div style={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column', padding: '16px 8px 24px 8px', gap: '16px', overflowY: 'auto' }}>
            {profiles.length === 0 ? (
                <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '32px', marginBottom: '12px' }}>🛡️</div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>No Active Threats Detected</div>
                        <div className="mono" style={{ color: 'var(--text-mono)', fontSize: '11px', marginTop: '4px' }}>Awaiting attacker profiles...</div>
                    </div>
                </div>
            ) : (
                profiles.map((p, idx) => {
                    const threatColor = getThreatColor(p.threat_level);
                    return (
                        <div key={idx} className="panel" style={{ 
                            display: 'flex', flexDirection: 'column', padding: '16px', 
                            borderLeft: `4px solid ${threatColor}`,
                            boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                            marginBottom: '16px'
                        }}>
                            
                            {/* Top Section: IP + Threat Level */}
                            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid var(--border-strong)' }}>
                                <div style={{ flex: 1 }}>
                                    <div className="mono" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-cyan)', letterSpacing: '1px', marginBottom: '4px' }}>
                                        {p.ip}
                                    </div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                        IP Address Profile
                                    </div>
                                </div>
                                <div style={{ 
                                    padding: '6px 12px', borderRadius: '4px', textAlign: 'center',
                                    border: `1px solid ${threatColor}`, backgroundColor: `${threatColor}20` 
                                }}>
                                    <div className="mono" style={{ fontSize: '14px', fontWeight: 700, color: threatColor }}>
                                        {p.threat_level}
                                    </div>
                                    <div style={{ fontSize: '9px', color: 'var(--text-primary)', marginTop: '2px', opacity: 0.8 }}>
                                        THREAT
                                    </div>
                                </div>
                            </div>

                            {/* Middle Section: Behavior + Intent Grid */}
                            <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
                                {/* Behavior Card */}
                                <div style={{ flex: 1, backgroundColor: 'var(--bg-surface-raised)', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '12px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                                        <span style={{ fontSize: '16px' }}>{getBehaviorIcon(p.behavior_type)}</span>
                                        <div className="mono" style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-mono)', textTransform: 'uppercase' }}>Behavior</div>
                                    </div>
                                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-cyan)', textTransform: 'capitalize' }}>
                                        {(p.behavior_type || 'Unknown').replace(/_/g, ' ')}
                                    </div>
                                </div>

                                {/* Intent Card */}
                                <div style={{ flex: 1, backgroundColor: 'var(--bg-surface-raised)', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '12px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                                        <span style={{ fontSize: '16px' }}>{getIntentIcon(p.intent)}</span>
                                        <div className="mono" style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-mono)', textTransform: 'uppercase' }}>Intent</div>
                                    </div>
                                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-amber)', textTransform: 'capitalize' }}>
                                        {(p.intent || 'Unknown').replace(/_/g, ' ')}
                                    </div>
                                </div>
                            </div>

                            {/* Status Badges */}
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
                                {p.is_tor && (
                                    <div style={{ padding: '6px 12px', backgroundColor: 'var(--accent-red-dim)', border: '1px solid var(--accent-red)', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <div style={{ width: '6px', height: '6px', backgroundColor: 'var(--accent-red)', borderRadius: '50%', animation: 'pulse 1.5s infinite' }}></div>
                                        <span className="mono" style={{ fontSize: '11px', fontWeight: 700, color: 'white' }}>TOR EXIT NODE</span>
                                    </div>
                                )}
                                {p.is_datacenter && !p.is_tor && (
                                    <div style={{ padding: '6px 12px', backgroundColor: 'var(--accent-amber-dim)', border: '1px solid var(--accent-amber)', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <div style={{ width: '6px', height: '6px', backgroundColor: 'var(--accent-amber)', borderRadius: '50%' }}></div>
                                        <span className="mono" style={{ fontSize: '11px', fontWeight: 700, color: 'white', textTransform: 'uppercase' }}>DATACENTER</span>
                                    </div>
                                )}
                                <div style={{ padding: '6px 12px', backgroundColor: 'var(--accent-cyan-dim)', border: '1px solid var(--accent-cyan)', borderRadius: '4px' }}>
                                    <span className="mono" style={{ fontSize: '11px', fontWeight: 700, color: 'white', textTransform: 'uppercase' }}>
                                        {p.access_count || 0} Targets Probed
                                    </span>
                                </div>
                            </div>

                            {/* Escalation Probability Bar */}
                            <div style={{ marginBottom: '24px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Escalation Probability</span>
                                    <span className="mono" style={{ fontSize: '13px', fontWeight: 700, color: getEscalationColor(p.escalation_probability) }}>{p.escalation_probability || 0}%</span>
                                </div>
                                <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--border-strong)', borderRadius: '4px', overflow: 'hidden' }}>
                                    <div style={{
                                        height: '100%',
                                        backgroundColor: getEscalationColor(p.escalation_probability),
                                        width: `${p.escalation_probability || 0}%`,
                                        transition: 'width 1s ease-out'
                                    }}></div>
                                </div>
                            </div>

                            {/* Metadata Grid */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '4px', border: '1px solid var(--border-subtle)', padding: '12px', marginBottom: '20px' }}>
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)', marginBottom: '4px' }}>SESSION</div>
                                    <div className="mono" style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-cyan)' }}>{p.session_duration || 0}s</div>
                                </div>
                                <div style={{ width: '1px', backgroundColor: 'var(--border-strong)' }}></div>
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)', marginBottom: '4px' }}>RESOURCES</div>
                                    <div className="mono" style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-amber)' }}>{p.access_count || 0}</div>
                                </div>
                                <div style={{ width: '1px', backgroundColor: 'var(--border-strong)' }}></div>
                                <div style={{ textAlign: 'center', flex: 1, padding: '0 8px', overflow: 'hidden' }}>
                                    <div className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)', marginBottom: '4px' }}>ASN ORG</div>
                                    <div className="mono" style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {p.org || 'Unknown'}
                                    </div>
                                </div>
                            </div>

                            {/* Attack Pathway */}
                            {p.resources_probed && p.resources_probed.length > 0 && (
                                <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                                    <div className="mono" style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '10px', textTransform: 'uppercase' }}>Attack Pathway Array</div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                                        {p.resources_probed.map((res, i) => (
                                            <React.Fragment key={i}>
                                                <div className="mono" style={{ fontSize: '11px', color: 'var(--text-primary)', backgroundColor: 'var(--bg-base)', padding: '4px 8px', borderRadius: '4px', border: '1px solid var(--border-strong)', maxWidth: '140px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={res}>
                                                    {res}
                                                </div>
                                                {i < p.resources_probed.length - 1 && <span style={{ color: 'var(--accent-cyan)', fontSize: '12px', opacity: 0.6 }}>→</span>}
                                            </React.Fragment>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Action Button */}
                            <a 
                                href={`http://13.61.240.101:8000/report/${p.ip}`}
                                target="_blank" 
                                rel="noreferrer"
                                style={{
                                    display: 'block', width: '100%', textAlign: 'center', padding: '12px',
                                    backgroundColor: 'var(--bg-surface-raised)', border: '1px solid var(--accent-cyan)',
                                    borderRadius: '4px', color: 'var(--accent-cyan)', textDecoration: 'none',
                                    fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
                                    transition: 'all 0.2s ease', cursor: 'pointer'
                                }}
                                onMouseOver={(e) => { e.target.style.backgroundColor = 'var(--accent-cyan-dim)'; e.target.style.color = '#fff'; }}
                                onMouseOut={(e) => { e.target.style.backgroundColor = 'var(--bg-surface-raised)'; e.target.style.color = 'var(--accent-cyan)'; }}
                            >
                                📄 Generate Forensic Report
                            </a>
                        </div>
                    );
                })
            )}
        </div>
    );
};

export default PanelAttackerIntelligence;
