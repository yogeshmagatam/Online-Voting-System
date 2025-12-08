import React, { useState, useEffect } from 'react';
import SiteLayout from './layout/SiteLayout';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

function CandidateDashboard({ token, onLogout }) {
  const [statistics, setStatistics] = useState({
    total_votes_cast: 0,
    total_precincts: 0,
    candidate_a_votes: 0,
    candidate_b_votes: 0,
    avg_turnout: 0
  });
  const [electionData, setElectionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetchUserData();
    fetchElectionStats();
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

  const fetchElectionStats = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/statistics', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }

      const data = await response.json();
      setStatistics(data);

      // Also fetch election data for table
      const dataResponse = await fetch('http://localhost:5000/api/election-data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (dataResponse.ok) {
        const electionDataResult = await dataResponse.json();
        setElectionData(electionDataResult);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data
  const votesChartData = {
    labels: ['Candidate A', 'Candidate B'],
    datasets: [
      {
        label: 'Votes Received',
        data: [statistics.candidate_a_votes || 0, statistics.candidate_b_votes || 0],
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

  const turnoutChartData = {
    labels: ['Voted', 'Not Voted'],
    datasets: [
      {
        label: 'Turnout',
        data: [
          (statistics.total_votes_cast || 0),
          Math.max(0, (statistics.total_votes_cast || 0) - (statistics.total_votes_cast || 0))
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(200, 200, 200, 0.6)'
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(200, 200, 200, 1)'
        ],
        borderWidth: 1,
      },
    ],
  };

  return (
    <SiteLayout isLoggedIn={true} onLogout={onLogout}>
      <div className="eci-content">
        {error && <div className="alert alert-danger">{error}</div>}

        {/* Candidate Info */}
        <div className="eci-card">
          <h2>Candidate Dashboard</h2>
          {user && (
            <div className="alert alert-info">
              Welcome, <strong>{user.sub}</strong>. Here's your election overview.
            </div>
          )}
        </div>

        {/* Statistics Cards */}
        <div className="eci-card">
          <h3>Election Overview</h3>
          {loading ? (
            <p>Loading statistics...</p>
          ) : (
            <>
              <div className="stats-container">
                <div className="stat-card">
                  <h4>Total Votes Cast</h4>
                  <div className="stat-value">{statistics.total_votes_cast || 0}</div>
                </div>
                <div className="stat-card">
                  <h4>Total Precincts</h4>
                  <div className="stat-value">{statistics.total_precincts || 0}</div>
                </div>
                <div className="stat-card">
                  <h4>Average Turnout</h4>
                  <div className="stat-value">{(statistics.avg_turnout || 0).toFixed(2)}%</div>
                </div>
                <div className="stat-card">
                  <h4>Votes for Candidate A</h4>
                  <div className="stat-value" style={{ color: 'rgba(54, 162, 235, 1)' }}>
                    {statistics.candidate_a_votes || 0}
                  </div>
                </div>
                <div className="stat-card">
                  <h4>Votes for Candidate B</h4>
                  <div className="stat-value" style={{ color: 'rgba(255, 99, 132, 1)' }}>
                    {statistics.candidate_b_votes || 0}
                  </div>
                </div>
              </div>

              {/* Charts */}
              <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '20px', flexWrap: 'wrap' }}>
                <div style={{ width: '45%', minWidth: '300px' }}>
                  <h4>Vote Distribution</h4>
                  <Pie data={votesChartData} />
                </div>
                <div style={{ width: '45%', minWidth: '300px' }}>
                  <h4>Total Turnout</h4>
                  <Pie data={turnoutChartData} />
                </div>
              </div>
            </>
          )}
        </div>

        {/* Election Data Table */}
        <div className="eci-card">
          <h3>Precinct Details</h3>
          {loading ? (
            <p>Loading data...</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Precinct</th>
                  <th>Candidate A</th>
                  <th>Candidate B</th>
                  <th>Registered Voters</th>
                  <th>Turnout %</th>
                </tr>
              </thead>
              <tbody>
                {electionData.map((item) => (
                  <tr key={item.id}>
                    <td>{item.precinct}</td>
                    <td>{item.votes_candidate_a}</td>
                    <td>{item.votes_candidate_b}</td>
                    <td>{item.registered_voters}</td>
                    <td>{item.turnout_percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </SiteLayout>
  );
}

export default CandidateDashboard;
