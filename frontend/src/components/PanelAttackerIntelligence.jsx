import React, { useState, useEffect } from 'react';

const PanelAttackerIntelligence = () => {
    const [profiles, setProfiles] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchProfiles = async () => {
        try {
            const res = await fetch('http://13.48.58.234:8000/profiles');
            const data = await res.json();
            setProfiles(data);
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

    const getBehaviorColor = (b) => {
        switch (b) {
            case 'AUTOMATED_SCANNER': return '#1d4ed8'; // blue
            case 'MANUAL_ATTACKER': return '#dc2626'; // red
            case 'AGGRESSIVE_ENUMERATION': return '#ea580c'; // orange
            case 'RECONNAISSANCE': return '#eab308'; // yellow
            default: return '#4b5563'; // gray
        }
    };

    const getIntentColor = (i) => {
        switch (i) {
            case 'CREDENTIAL_HARVESTING': return '#dc2626'; // red
            case 'DATA_EXFILTRATION': return '#d97706'; // amber
            case 'FINANCIAL_TARGETING': return '#dc2626'; // red
            case 'TARGETED_ATTACK': return '#991b1b'; // bright red
            case 'BROAD_RECONNAISSANCE': return '#4b5563'; // gray
            default: return '#4b5563';
        }
    };
    
    const getThreatColor = (t) => {
        switch (t) {
            case 'CRITICAL': return '#dc2626';
            case 'HIGH': return '#ea580c';
            case 'MEDIUM': return '#eab308';
            case 'LOW': return '#22c55e';
            default: return '#4b5563';
        }
    };

    const getBarColor = (score) => {
        if (score >= 75) return '#dc2626';
        if (score >= 50) return '#ea580c';
        if (score >= 25) return '#eab308';
        return '#22c55e';
    };

    if (loading && profiles.length === 0) {
        return <div className="p-4 text-cyan-500 font-mono">Initializing Intelligence Matrices...</div>;
    }

    return (
        <div className="h-full w-full flex flex-col pt-2 pb-6 px-4 gap-4 overflow-y-auto custom-scrollbar">
            {profiles.length === 0 ? (
                <div className="flex h-full items-center justify-center text-gray-500 font-mono text-sm uppercase">
                   [ No Malicious Profiles Detected ]
                </div>
            ) : (
                profiles.map((p, idx) => (
                    <div key={idx} className="flex flex-col bg-[#0f172a] rounded shadow-lg border border-gray-800 p-4 font-mono text-sm">
                        
                        {/* Header Row */}
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-cyan-400 font-bold text-lg">{p.ip}</span>
                            <span 
                                className="px-2 py-1 text-xs font-bold text-slate-100 rounded"
                                style={{backgroundColor: getThreatColor(p.threat_level)}}
                            >
                                {p.threat_level} THREAT
                            </span>
                        </div>
                        
                        {/* Badges Row */}
                        <div className="flex flex-wrap gap-2 mb-4">
                            {p.is_tor && (
                                <span className="px-2 py-0.5 text-[10px] rounded bg-red-900 border border-red-500 font-bold text-white animate-pulse">
                                    TOR EXIT NODE
                                </span>
                            )}
                            {p.is_datacenter && !p.is_tor && (
                                <span className="px-2 py-0.5 text-[10px] rounded bg-yellow-900 border border-yellow-500 font-bold text-white">
                                    DATACENTER SCANNER
                                </span>
                            )}
                            <span className="px-2 py-0.5 text-[10px] rounded border border-gray-700 font-bold" style={{color: getBehaviorColor(p.behavior_type)}}>
                                BEHAVIOR: {p.behavior_type.replace('_', ' ')}
                            </span>
                            <span className="px-2 py-0.5 text-[10px] rounded border border-gray-700 font-bold" style={{color: getIntentColor(p.intent)}}>
                                INTENT: {p.intent.replace('_', ' ')}
                            </span>
                        </div>

                        {/* Progress Bar */}
                        <div className="flex flex-col mb-4">
                            <div className="flex justify-between text-xs text-gray-400 mb-1">
                                <span>Escalation Probability</span>
                                <span style={{color: getBarColor(p.escalation_probability)}} className="font-bold">{p.escalation_probability}%</span>
                            </div>
                            <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                                <div 
                                    className="h-full transition-all duration-1000 ease-in-out" 
                                    style={{
                                        width: `${p.escalation_probability}%`, 
                                        backgroundColor: getBarColor(p.escalation_probability)
                                    }}
                                ></div>
                            </div>
                        </div>

                        {/* Metadata Footer */}
                        <div className="flex justify-between text-xs text-gray-500 mt-auto border-t border-gray-800 pt-2">
                            <span>Active: <span className="text-cyan-600">{p.session_duration}s</span></span>
                            <span>Targets Probed: <span className="text-amber-500">{p.access_count}</span></span>
                        </div>
                        
                        <div className="mt-2 flex flex-col text-xs">
                            <span className="text-gray-500 underline mb-1">Trace Pathway:</span>
                            <div className="flex flex-wrap gap-1">
                                {p.resources_probed.map((res, i) => (
                                    <span key={i} className="text-gray-400 truncate max-w-[150px]" title={res}>
                                        {res}{i < p.resources_probed.length -1 ? " → " : ""}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* PDF Download Action */}
                        <div className="mt-4 border-t border-gray-800 pt-3">
                            <a 
                                href={`http://127.0.0.1:8000/report/${p.ip}`} 
                                target="_blank" 
                                rel="noreferrer"
                                className="w-full text-center block bg-gray-800 hover:bg-cyan-900 border border-gray-700 hover:border-cyan-500 text-gray-300 hover:text-cyan-400 font-bold py-1.5 rounded text-xs transition duration-200"
                            >
                                📥 GENERATE FORENSIC PDF REPORT
                            </a>
                        </div>
                    </div>
                ))
            )}
        </div>
    );
};

export default PanelAttackerIntelligence;
