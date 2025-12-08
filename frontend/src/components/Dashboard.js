import React, { useState, useEffect } from 'react';
import SiteLayout from './layout/SiteLayout';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

function Dashboard({ token, userRole, onLogout }) {
  const [electionData, setElectionData] = useState([]);
  const [statistics, setStatistics] = useState({
    total_precincts: 0,
    total_votes: 0,
    avg_turnout: 0,
    suspicious_precincts: 0,
    candidate_a_votes: 0,
    candidate_b_votes: 0
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

  // Fetch election data and statistics
  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch election data
      const dataResponse = await fetch('http://localhost:5000/api/election-data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!dataResponse.ok) {
        throw new Error('Failed to fetch election data');
      }
      
      const dataResult = await dataResponse.json();
      setElectionData(dataResult);
      
      // Fetch statistics
      const statsResponse = await fetch('http://localhost:5000/api/statistics', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!statsResponse.ok) {
        throw new Error('Failed to fetch statistics');
      }
      
      const statsResult = await statsResponse.json();
      setStatistics(statsResult);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Auto-calculate turnout percentage when both votes and registered voters are provided
    if ((name === 'votes_candidate_a' || name === 'votes_candidate_b' || name === 'registered_voters') && 
        formData.registered_voters && (parseInt(formData.votes_candidate_a) || 0) + (parseInt(formData.votes_candidate_b) || 0) > 0) {
      const totalVotes = (parseInt(formData.votes_candidate_a) || 0) + (parseInt(formData.votes_candidate_b) || 0);
      const registeredVoters = parseInt(formData.registered_voters) || 1; // Prevent division by zero
      const turnout = (totalVotes / registeredVoters) * 100;
      
      setFormData({
        ...formData,
        [name]: value,
        turnout_percentage: turnout.toFixed(2)
      });
    }
  };

  // Handle form submission
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
      
      // Reset form and refresh data
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

  // Run fraud detection analysis
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
      fetchData(); // Refresh statistics
      
    } catch (err) {
      setError(err.message);
    }
  };

  // Prepare chart data
  const votesChartData = {
    labels: ['Candidate A', 'Candidate B'],
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
          statistics.total_precincts - statistics.suspicious_precincts,
          statistics.suspicious_precincts
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

  return (
    <SiteLayout isLoggedIn={true} onLogout={onLogout}>
      <div className="eci-content">
        {error && <div className="alert alert-danger">{error}</div>}
        
        {/* Statistics Cards */}
        <div className="eci-card">
          <h2>Election Statistics</h2>
          <div className="stats-container">
            <div className="stat-card">
              <h3>Total Precincts</h3>
              <div className="stat-value">{statistics.total_precincts}</div>
            </div>
            <div className="stat-card">
              <h3>Total Votes</h3>
              <div className="stat-value">{statistics.total_votes}</div>
            </div>
            <div className="stat-card">
              <h3>Average Turnout</h3>
              <div className="stat-value">{statistics.avg_turnout.toFixed(2)}%</div>
            </div>
            <div className="stat-card">
              <h3>Suspicious Precincts</h3>
              <div className="stat-value">{statistics.suspicious_precincts}</div>
            </div>
          </div>
          
          {/* Charts */}
          <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '20px' }}>
            <div style={{ width: '40%' }}>
              <h3>Vote Distribution</h3>
              <Pie data={votesChartData} />
            </div>
            <div style={{ width: '40%' }}>
              <h3>Precinct Status</h3>
              <Pie data={precinctChartData} />
            </div>
          </div>
        </div>
        
        {/* Data Entry Form (Admin only) */}
        {userRole === 'admin' && (
          <div className="eci-card">
            <h2>Add Election Data</h2>
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
                <label htmlFor="votes_candidate_a">Votes for Candidate A</label>
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
                <label htmlFor="votes_candidate_b">Votes for Candidate B</label>
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
        )}
        
        {/* Fraud Detection (Admin only) */}
        {userRole === 'admin' && (
          <div className="eci-card">
            <h2>Fraud Detection</h2>
            <p>Run machine learning analysis to detect potential election fraud based on statistical anomalies.</p>
            <button className="btn btn-primary" onClick={runAnalysis}>Run Analysis</button>
          </div>
        )}
        
        {/* Election Data Table */}
        <div className="eci-card">
          <h2>Election Data</h2>
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
                    <td>{item.flagged_suspicious ? '⚠️ Suspicious' : 'Normal'}</td>
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

export default Dashboard;