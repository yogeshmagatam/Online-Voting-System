import React, { useState, useEffect } from 'react';
import SiteLayout from './layout/SiteLayout';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

function AdminDashboard({ token, onLogout }) {
  const [electionData, setElectionData] = useState([]);
  const [statistics, setStatistics] = useState({
    total_precincts: 0,
    total_votes: 0,
    avg_turnout: 0,
    suspicious_precincts: 0,
    candidate_a_votes: 0,
    candidate_b_votes: 0,
    total_voters: 0,
    total_candidates: 0,
    verified_voters: 0,
    total_attempts: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    precinct: '',
    votes_candidate_a: '',
    votes_candidate_b: '',
    registered_voters: '',
    turnout_percentage: '',
    timestamp: new Date().toISOString()
  });
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [activityLogs, setActivityLogs] = useState([]);
  const [securityLogs, setSecurityLogs] = useState([]);
  const [voters, setVoters] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [identityVerifications, setIdentityVerifications] = useState([]);

  useEffect(() => {
    fetchUserData();
    fetchData();
    fetchActivityLogs();
    fetchSecurityLogs();
    fetchUserStats();
    fetchIdentityVerifications();
  }, [token]);

  const fetchUserData = async () => {
    try {
      const tokenParts = token.split('.');
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1]));
        setUser(payload);
      }
    } catch (err) {
      console.error('Error fetching user data:', err);
    }
  };

  const fetchActivityLogs = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/activity-logs', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setActivityLogs(data.slice(0, 50)); // Last 50 activities
      }
    } catch (err) {
      console.error('Error fetching activity logs:', err);
    }
  };

  const fetchSecurityLogs = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/security-logs', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSecurityLogs(data.slice(0, 50)); // Last 50 security events
      }
    } catch (err) {
      console.error('Error fetching security logs:', err);
    }
  };

  const fetchUserStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/user-stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        console.log('[Admin Dashboard] User stats received:', data);
        setStatistics(prev => ({ ...prev, ...data }));
      } else {
        console.error('[Admin Dashboard] Failed to fetch user stats:', response.status);
      }
    } catch (err) {
      console.error('Error fetching user stats:', err);
    }
  };

  const fetchIdentityVerifications = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/identity-verifications', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setIdentityVerifications(data.slice(0, 50)); // Last 50 verifications
      }
    } catch (err) {
      console.error('Error fetching identity verifications:', err);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const dataResponse = await fetch('http://localhost:5000/api/election-data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!dataResponse.ok) {
        throw new Error('Failed to fetch election data');
      }

      const dataResult = await dataResponse.json();
      // Handle both array and object responses
      if (Array.isArray(dataResult)) {
        setElectionData(dataResult);
      } else if (dataResult.data && Array.isArray(dataResult.data)) {
        setElectionData(dataResult.data);
      } else {
        setElectionData([]);
      }

      const statsResponse = await fetch('http://localhost:5000/api/statistics', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!statsResponse.ok) {
        throw new Error('Failed to fetch statistics');
      }

      const statsResult = await statsResponse.json();
      setStatistics(prev => ({ ...prev, ...statsResult }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });

    if ((name === 'votes_candidate_a' || name === 'votes_candidate_b' || name === 'registered_voters') &&
      formData.registered_voters && (parseInt(formData.votes_candidate_a) || 0) + (parseInt(formData.votes_candidate_b) || 0) > 0) {
      const totalVotes = (parseInt(formData.votes_candidate_a) || 0) + (parseInt(formData.votes_candidate_b) || 0);
      const registeredVoters = parseInt(formData.registered_voters) || 1;
      const turnout = (totalVotes / registeredVoters) * 100;

      setFormData({
        ...formData,
        [name]: value,
        turnout_percentage: turnout.toFixed(2)
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:5000/api/election-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to add election data');
      }

      setFormData({
        precinct: '',
        votes_candidate_a: '',
        votes_candidate_b: '',
        registered_voters: '',
        turnout_percentage: '',
        timestamp: new Date().toISOString()
      });

      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  const runAnalysis = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to run analysis');
      }

      const result = await response.json();
      setElectionData(result.data);
      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };



  const votesChartData = {
    labels: ['Narendra Modi ji', 'Rahul Gandhi ji'],
    datasets: [
      {
        label: 'Votes',
        data: [statistics.candidate_a_votes, statistics.candidate_b_votes],
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 99, 132, 0.6)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 99, 132, 1)'
        ],
        borderWidth: 1,
      },
    ],
  };

  const precinctChartData = {
    labels: ['Normal', 'Suspicious'],
    datasets: [
      {
        label: 'Precincts',
        data: [
          (statistics.total_precincts || 3) - (statistics.suspicious_precincts || 0),
          statistics.suspicious_precincts || 0
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 159, 64, 0.6)'
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(255, 159, 64, 1)'
        ],
        borderWidth: 1,
      },
    ],
  };

  // Election outcome summary
  const candidateAVotes = statistics.candidate_a_votes || 0;
  const candidateBVotes = statistics.candidate_b_votes || 0;
  const totalCandidateVotes = candidateAVotes + candidateBVotes;
  let winnerLabel = 'Tie';
  let winnerVotes = candidateAVotes;
  let marginVotes = 0;

  if (candidateAVotes > candidateBVotes) {
    winnerLabel = 'Narendra Modi ji';
    winnerVotes = candidateAVotes;
    marginVotes = candidateAVotes - candidateBVotes;
  } else if (candidateBVotes > candidateAVotes) {
    winnerLabel = 'Rahul Gandhi ji';
    winnerVotes = candidateBVotes;
    marginVotes = candidateBVotes - candidateAVotes;
  }

  const marginPercent = totalCandidateVotes > 0
    ? ((marginVotes / totalCandidateVotes) * 100).toFixed(2)
    : '0.00';

  return (
    <SiteLayout isLoggedIn={true} onLogout={onLogout}>
      <div className="eci-content">
        {error && <div className="alert alert-danger">{error}</div>}

        {/* Admin Header */}
        <div className="eci-card">
          <h2>🔐 Admin Monitoring Dashboard</h2>
          {user && (
            <div className="alert alert-info">
              Welcome, Administrator <strong>{user.sub}</strong>. System monitoring active.
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="eci-card" style={{ marginBottom: '10px' }}>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', borderBottom: '2px solid #ddd', paddingBottom: '10px' }}>
            {['overview', 'activity', 'security', 'identity', 'data', 'fraud'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: activeTab === tab ? '#007bff' : '#f0f0f0',
                  color: activeTab === tab ? 'white' : '#333',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: activeTab === tab ? 'bold' : 'normal'
                }}
              >
                {tab === 'overview' && '📊 Overview'}
                {tab === 'activity' && '📋 Activity Logs'}
                {tab === 'security' && '🔒 Security Events'}
                {tab === 'identity' && '👤 Identity Verification'}
                {tab === 'data' && '📈 Election Data'}
                {tab === 'fraud' && '⚠️ Fraud Detection'}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            {/* Election Outcome */}
            <div className="eci-card">
              <h2>🏁 Election Outcome</h2>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
                <div className="stat-card" style={{ flex: '1 1 240px', background: '#fff7ec' }}>
                  <h3>Leading</h3>
                  <div className="stat-value">{winnerLabel}</div>
                  <div style={{ color: '#666', marginTop: '4px' }}>Votes: {winnerVotes}</div>
                </div>
                <div className="stat-card" style={{ flex: '1 1 240px', background: '#f0f7ff' }}>
                  <h3>Margin</h3>
                  <div className="stat-value">{marginVotes}</div>
                  <div style={{ color: '#666', marginTop: '4px' }}>({marginPercent}% of counted votes)</div>
                </div>
                <div className="stat-card" style={{ flex: '1 1 240px', background: '#f7fcf5' }}>
                  <h3>Total Counted Votes</h3>
                  <div className="stat-value">{totalCandidateVotes}</div>
                  <div style={{ color: '#666', marginTop: '4px' }}>Across all candidates</div>
                </div>
              </div>
            </div>

            {/* Election Statistics */}
            <div className="eci-card">
              <h2>Election Statistics</h2>
              <div className="stats-container">
                <div className="stat-card">
                  <h3>Average Turnout</h3>
                  <div className="stat-value">{statistics.avg_turnout?.toFixed(2) || '0.00'}%</div>
                </div>
                <div className="stat-card">
                  <h3>🗳️ Total Votes</h3>
                  <div className="stat-value">{statistics.total_votes || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Narendra Modi ji Votes</h3>
                  <div className="stat-value">{statistics.candidate_a_votes || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Rahul Gandhi ji Votes</h3>
                  <div className="stat-value">{statistics.candidate_b_votes || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>⚠️ Suspicious Precincts</h3>
                  <div className="stat-value">{statistics.suspicious_precincts || 0}</div>
                </div>
              </div>

              {/* Charts */}
              <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '20px', flexWrap: 'wrap' }}>
                <div style={{ width: '45%', minWidth: '300px' }}>
                  <h3>Vote Distribution</h3>
                  <Pie data={votesChartData} />
                </div>
                <div style={{ width: '45%', minWidth: '300px' }}>
                  <h3>Precinct Status</h3>
                  <Pie data={precinctChartData} />
                </div>
              </div>
            </div>
          </>
        )}

        {/* Activity Logs Tab */}
        {activeTab === 'activity' && (
          <div className="eci-card">
            <h2>📋 Recent Activity Logs</h2>
            <p style={{ color: '#666', marginBottom: '15px' }}>Last 50 user activities across the system</p>
            {activityLogs.length === 0 ? (
              <p>No activity logs available</p>
            ) : (
              <table className="data-table" style={{ fontSize: '13px' }}>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User ID</th>
                    <th>Action</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {activityLogs.map((log, idx) => (
                    <tr key={idx}>
                      <td>{new Date(log.timestamp).toLocaleString()}</td>
                      <td>{log.user_id || 'N/A'}</td>
                      <td><strong>{log.action}</strong></td>
                      <td>{JSON.stringify(log.metadata || {}).substring(0, 50)}...</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Security Events Tab */}
        {activeTab === 'security' && (
          <div className="eci-card">
            <h2>🔒 Security Events</h2>
            <p style={{ color: '#666', marginBottom: '15px' }}>Last 50 security events and alerts</p>
            {securityLogs.length === 0 ? (
              <p>No security events</p>
            ) : (
              <table className="data-table" style={{ fontSize: '13px' }}>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Event Type</th>
                    <th>IP Address</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {securityLogs.map((log, idx) => (
                    <tr key={idx} style={{ backgroundColor: log.event_type?.includes('failed') ? '#ffe6e6' : 'inherit' }}>
                      <td>{new Date(log.timestamp).toLocaleString()}</td>
                      <td><strong>{log.event_type}</strong></td>
                      <td>{log.ip_address || 'N/A'}</td>
                      <td>{JSON.stringify(log.event_data || {}).substring(0, 80)}...</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Identity Verification Tab */}
        {activeTab === 'identity' && (
          <div className="eci-card">
            <h2>👤 Identity Verification Records</h2>
            <p style={{ color: '#666', marginBottom: '15px' }}>Face recognition verification attempts and results</p>
            {identityVerifications.length === 0 ? (
              <p>No identity verification records</p>
            ) : (
              <table className="data-table" style={{ fontSize: '13px' }}>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User ID</th>
                    <th>Liveness Score</th>
                    <th>Face Match</th>
                    <th>Status</th>
                    <th>Fraud Indicators</th>
                  </tr>
                </thead>
                <tbody>
                  {identityVerifications.map((verify, idx) => (
                    <tr key={idx} style={{ backgroundColor: verify.is_genuine ? '#e6ffe6' : '#ffe6e6' }}>
                      <td>{new Date(verify.timestamp).toLocaleString()}</td>
                      <td>{verify.user_id || 'N/A'}</td>
                      <td>{(verify.liveness_score * 100).toFixed(1)}%</td>
                      <td>{(verify.face_match_confidence * 100).toFixed(1)}%</td>
                      <td>{verify.is_genuine ? '✅ Verified' : '❌ Failed'}</td>
                      <td>{verify.spoofing_indicators?.join(', ') || 'None'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Election Data Tab */}
        {activeTab === 'data' && (
          <>
            <div className="eci-card">
              <h2>📈 Add Election Data</h2>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="precinct">Precinct Name</label>
                  <input
                    type="text"
                    className="form-control"
                    id="precinct"
                    name="precinct"
                    value={formData.precinct}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="votes_candidate_a">Votes for Narendra Modi ji</label>
                  <input
                    type="number"
                    className="form-control"
                    id="votes_candidate_a"
                    name="votes_candidate_a"
                    value={formData.votes_candidate_a}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="votes_candidate_b">Votes for Rahul Gandhi ji</label>
                  <input
                    type="number"
                    className="form-control"
                    id="votes_candidate_b"
                    name="votes_candidate_b"
                    value={formData.votes_candidate_b}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="registered_voters">Registered Voters</label>
                  <input
                    type="number"
                    className="form-control"
                    id="registered_voters"
                    name="registered_voters"
                    value={formData.registered_voters}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="turnout_percentage">Turnout Percentage</label>
                  <input
                    type="number"
                    className="form-control"
                    id="turnout_percentage"
                    name="turnout_percentage"
                    value={formData.turnout_percentage}
                    onChange={handleInputChange}
                    readOnly
                  />
                </div>
                <button type="submit" className="btn btn-primary">Submit Data</button>
              </form>
            </div>

            <div className="eci-card">
              <h2>🗳️ Election Data Records</h2>
              {loading ? (
                <p>Loading data...</p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Precinct</th>
                      <th>Narendra Modi ji</th>
                      <th>Rahul Gandhi ji</th>
                      <th>Registered Voters</th>
                      <th>Turnout %</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {electionData.map((item) => (
                      <tr key={item.id} className={item.flagged_suspicious ? 'suspicious' : ''}>
                        <td>{item.precinct}</td>
                        <td>{item.votes_candidate_a}</td>
                        <td>{item.votes_candidate_b}</td>
                        <td>{item.registered_voters}</td>
                        <td>{item.turnout_percentage}%</td>
                        <td>{item.flagged_suspicious ? '⚠️ Suspicious' : '✅ Normal'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        {/* Fraud Detection Tab */}
        {activeTab === 'fraud' && (
          <>
            <div className="eci-card">
              <h2>⚠️ Fraud Detection Analysis</h2>
              <p>Run machine learning analysis to detect potential election fraud based on statistical anomalies.</p>
              <button className="btn btn-primary" onClick={runAnalysis}>
                Run ML Analysis
              </button>
            </div>
          </>
        )}
      </div>
    </SiteLayout>
  );
}

export default AdminDashboard;
