import React, { useState, useEffect, useCallback } from 'react';
import SiteLayout from './layout/SiteLayout.jsx';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

function AdminDashboard({ token, onLogout, onNavigateToMission, onNavigateToSecurity, onNavigateToPrivacy, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility, onNavigateToRegister, onNavigateToLogin, onNavigateToRegisterAdmin }) {
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
  const [activityLogs, setActivityLogs] = useState([]);
  const [identityVerifications, setIdentityVerifications] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [datasetSummary, setDatasetSummary] = useState(null);

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

  const fetchModelStatus = async () => {
    try {
      console.log('[Admin Dashboard] Fetching model status from /api/admin/model-status');
      const response = await fetch('http://localhost:5000/api/admin/model-status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        console.log('[Admin Dashboard] Model status received:', data);
        setModelStatus(data);
      } else {
        console.error('[Admin Dashboard] Failed to fetch model status:', response.status, response.statusText);
      }
    } catch (err) {
      console.error('[Admin Dashboard] Error fetching model status:', err);
    }
  };

  const fetchDatasetSummary = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/fraud-dataset-summary', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDatasetSummary(data);
      } else {
        console.warn('[Admin Dashboard] Dataset summary not available');
        setDatasetSummary(null);
      }
    } catch (err) {
      console.error('[Admin Dashboard] Error fetching dataset summary:', err);
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
      console.log('[AdminDashboard] Statistics received from /api/statistics:', statsResult);
      console.log('[AdminDashboard] avg_turnout value:', statsResult.avg_turnout);
      setStatistics(prev => {
        const updated = { ...prev, ...statsResult };
        console.log('[AdminDashboard] Updated statistics state:', updated);
        return updated;
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const refreshAll = useCallback(() => {
    fetchUserData();
    fetchData();
    fetchActivityLogs();
    fetchUserStats();
    fetchIdentityVerifications();
    fetchModelStatus();
    fetchDatasetSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    refreshAll();
    const intervalId = setInterval(refreshAll, 30000); // auto-refresh every 30s
    return () => clearInterval(intervalId);
  }, [refreshAll]);

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



  // Election outcome summary (combines CSV dataset and live votes)
  const useDatasetOutcome = datasetSummary?.available;
  const datasetLegitimateVotes = datasetSummary?.legitimate_votes || 0;
  const datasetFraudulentVotes = datasetSummary?.fraudulent_votes || 0;
  
  // Vote distribution: Combine dataset votes with live votes from database
  const candidateAVotes = datasetLegitimateVotes + (statistics.candidate_a_votes || 0);
  const candidateBVotes = datasetFraudulentVotes + (statistics.candidate_b_votes || 0);
  const totalCandidateVotes = candidateAVotes + candidateBVotes;
  let winnerLabel = 'Tie';
  let winnerVotes = candidateAVotes;
  let marginVotes = 0;

  if (candidateAVotes > candidateBVotes) {
    winnerLabel = 'Candidate A';
    winnerVotes = candidateAVotes;
    marginVotes = candidateAVotes - candidateBVotes;
  } else if (candidateBVotes > candidateAVotes) {
    winnerLabel = 'Candidate B';
    winnerVotes = candidateBVotes;
    marginVotes = candidateBVotes - candidateAVotes;
  }

  const marginPercent = totalCandidateVotes > 0
    ? ((marginVotes / totalCandidateVotes) * 100).toFixed(2)
    : '0.00';

  const totalVotesStat = (datasetSummary?.total_rows || 0) + (statistics.total_votes || 0);

  const candidateLabels = ['Candidate A', 'Candidate B'];

  const votesChartData = {
    labels: candidateLabels,
    datasets: [
      {
        label: 'Votes',
        data: [candidateAVotes, candidateBVotes],
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

  // Use live data from statistics
  const totalPrecincts = statistics.total_precincts || 0;
  const suspiciousPrecincts = statistics.suspicious_precincts || 0;
  const normalPrecincts = totalPrecincts - suspiciousPrecincts;

  // Breakdown by candidate - distribute votes proportionally across normal/suspicious
  const totalCandidateAVotes = candidateAVotes || 0;
  const totalCandidateBVotes = candidateBVotes || 0;
  const totalAllVotes = totalCandidateAVotes + totalCandidateBVotes;
  
  // Estimate suspicious votes (assume 30% of votes from suspicious precincts)
  const suspiciousVotesEstimate = totalAllVotes > 0 && totalPrecincts > 0 
    ? Math.round((suspiciousPrecincts / totalPrecincts) * totalAllVotes * 0.3)
    : 0;
  const normalVotesEstimate = totalAllVotes - suspiciousVotesEstimate;
  
  // Distribute by candidate proportionally
  const candidateARatio = totalAllVotes > 0 ? totalCandidateAVotes / totalAllVotes : 0.5;
  const candidateASuspicious = Math.round(suspiciousVotesEstimate * candidateARatio);
  const candidateBSuspicious = suspiciousVotesEstimate - candidateASuspicious;
  const candidateANormal = Math.round(normalVotesEstimate * candidateARatio);
  const candidateBNormal = normalVotesEstimate - candidateANormal;

  const precinctChartData = {
    labels: ['Candidate A - Suspicious', 'Candidate B - Suspicious', 'Candidate A - Normal', 'Candidate B - Normal'],
    datasets: [
      {
        label: 'Precinct Votes',
        data: [
          candidateASuspicious,
          candidateBSuspicious,
          candidateANormal,
          candidateBNormal
        ],
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(255, 159, 64, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(75, 192, 192, 0.6)'
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(75, 192, 192, 1)'
        ],
        borderWidth: 1,
      },
    ],
  };

  return (
    <SiteLayout
      isLoggedIn={true}
      onLogout={onLogout}
      onLoginClick={onNavigateToLogin}
      onRegisterClick={onNavigateToRegister}
      onNavigateToRegisterAdmin={onNavigateToRegisterAdmin}
      onNavigateToMission={onNavigateToMission}
      onNavigateToSecurity={onNavigateToSecurity}
      onNavigateToPrivacy={onNavigateToPrivacy}
      onNavigateToFAQ={onNavigateToFAQ}
      onNavigateToSupport={onNavigateToSupport}
      onNavigateToAccessibility={onNavigateToAccessibility}
    >
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
          <div style={{ marginTop: '8px' }}>
            <button className="btn btn-secondary" onClick={refreshAll}>Refresh data</button>
          </div>
        </div>

        {/* Overview Content */}
        <>
            {/* Fraud Detection Model Status */}
            {modelStatus ? (
              <div className="eci-card" style={{ background: modelStatus.rf_service_ready ? '#f0f7ff' : '#fff7ec', borderLeft: `4px solid ${modelStatus.rf_service_ready ? '#28a745' : '#ffc107'}` }}>
                <h2>🤖 Fraud Detection Model Status</h2>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', marginTop: '12px' }}>
                  <div className="stat-card" style={{ flex: '1 1 200px' }}>
                    <h3>Model Status</h3>
                    <div className="stat-value" style={{ fontSize: '1.2rem' }}>
                      {modelStatus.rf_service_ready ? '✓ Active' : '✗ Not Ready'}
                    </div>
                  </div>
                  <div className="stat-card" style={{ flex: '1 1 200px' }}>
                    <h3>Model Type</h3>
                    <div className="stat-value" style={{ fontSize: '1.2rem' }}>
                      {modelStatus.model_type || 'Unknown'}
                    </div>
                  </div>
                  <div className="stat-card" style={{ flex: '1 1 200px' }}>
                    <h3>Features</h3>
                    <div className="stat-value" style={{ fontSize: '1.2rem' }}>
                      {modelStatus.features_count || 0}
                    </div>
                  </div>
                </div>
                {modelStatus.rf_service_ready && modelStatus.features && modelStatus.features.length > 0 && (
                  <div style={{ marginTop: '12px', fontSize: '0.9rem', color: '#666' }}>
                    <strong>Features:</strong> {modelStatus.features.join(', ')}
                  </div>
                )}
              </div>
            ) : (
              <div className="eci-card" style={{ background: '#f8f9fa', borderLeft: '4px solid #ccc' }}>
                <h2>🤖 Fraud Detection Model Status</h2>
                <p style={{ color: '#666' }}>Loading model status...</p>
              </div>
            )}

            {/* Election Outcome */}
            <div className="eci-card">
              <h2>🏁 Election Outcome</h2>
              <div className="alert alert-info" style={{ marginBottom: '10px' }}>
                {useDatasetOutcome 
                  ? 'Combined results from voting_fraud_dataset.csv and live votes' 
                  : 'Showing live votes (Candidate A vs Candidate B)'}
              </div>
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
                  <div className="stat-value">{totalVotesStat}</div>
                </div>
                <div className="stat-card">
                  <h3>{candidateLabels[0]}{useDatasetOutcome ? '' : ''}</h3>
                  <div className="stat-value">{candidateAVotes}</div>
                </div>
                <div className="stat-card">
                  <h3>{candidateLabels[1]}{useDatasetOutcome ? '' : ''}</h3>
                  <div className="stat-value">{candidateBVotes}</div>
                </div>
                <div className="stat-card">
                  <h3>⚠️ Suspicious Precincts</h3>
                  <div className="stat-value">{suspiciousPrecincts}</div>
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

      </div>
    </SiteLayout>
  );
}

export default AdminDashboard;
