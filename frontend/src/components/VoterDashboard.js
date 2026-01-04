import React, { useState, useEffect } from 'react';
import SiteLayout from './layout/SiteLayout';
import IdentityVerification from './IdentityVerification';

function VoterDashboard({ token, onLogout }) {
  const [user, setUser] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [precincts, setPrecincts] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState('');
  const [selectedPrecinct, setSelectedPrecinct] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);
  const [hasVoted, setHasVoted] = useState(false);
  const [verified, setVerified] = useState(false);
  const [showVerification, setShowVerification] = useState(false);

  useEffect(() => {
    fetchUserData();
    fetchCandidates();
    fetchPrecincts();
  }, [token]);

  const fetchUserData = async () => {
    try {
      // Decode JWT to get user info (basic decoding without verification)
      const tokenParts = token.split('.');
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1]));
        setUser(payload);
        // Check if user is already verified
        setVerified(payload.verified || false);
      }
    } catch (err) {
      console.error('Error fetching user data:', err);
    }
    setLoading(false);
  };

  const fetchCandidates = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/election-data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCandidates(data.candidates || []);
      }
    } catch (err) {
      console.error('Error fetching candidates:', err);
    }
  };

  const fetchPrecincts = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/election-data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPrecincts(data.precincts || []);
      }
    } catch (err) {
      console.error('Error fetching precincts:', err);
    }
  };

  const handleVerifyIdentity = () => {
    setShowVerification(true);
    setError('');
    setSuccess('');
  };

  const handleVerificationComplete = () => {
    setVerified(true);
    setShowVerification(false);
    setSuccess('✓ Identity verification successful! You can now cast your vote.');
  };

  const handleCancelVerification = () => {
    setShowVerification(false);
  };

  const handleCastVote = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!verified) {
      setError('Please verify your identity before voting');
      setShowVerification(true);
      return;
    }

    if (!selectedCandidate || !selectedPrecinct) {
      setError('Please select a candidate and precinct');
      return;
    }

    try {
      const voteData = {
        candidate_id: selectedCandidate,
        timestamp: new Date().toISOString()
      };

      const response = await fetch('http://localhost:5000/api/cast-vote', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          vote: voteData,
          precinct: selectedPrecinct,
          behavior_data: {
            timeSpent: 30,
            mouseMovements: [],
            keystrokes: []
          }
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to cast vote');
      }

      setSuccess(`Vote cast successfully! Transaction ID: ${data.transaction_id}`);
      setHasVoted(true);
      setSelectedCandidate('');
      setSelectedPrecinct('');
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <SiteLayout isLoggedIn={true} onLogout={onLogout}><div className="eci-content"><p>Loading...</p></div></SiteLayout>;
  }

  if (showVerification) {
    return (
      <SiteLayout isLoggedIn={true} onLogout={onLogout}>
        <IdentityVerification
          token={token}
          onVerificationComplete={handleVerificationComplete}
          onCancel={handleCancelVerification}
        />
      </SiteLayout>
    );
  }

  return (
    <SiteLayout isLoggedIn={true} onLogout={onLogout}>
      <div className="eci-content">
        <div className="eci-card">
          <h2>Voter Dashboard</h2>
          {error && <div className="alert alert-danger">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          {/* Verification Status */}
          <div className="alert" style={{ background: verified ? '#d4edda' : '#fff3cd', borderColor: verified ? '#c3e6cb' : '#ffc107', color: verified ? '#155724' : '#856404' }}>
            <strong>Verification Status:</strong> {verified ? '✓ Verified' : '✗ Not Verified'}
          </div>

          {/* Identity Verification Section */}
          {!verified && (
            <div className="eci-card" style={{ background: '#f8f9fa', marginBottom: '20px' }}>
              <h3>Step 1: Verify Your Identity</h3>
              <p>You must verify your identity before casting a vote. We will use your camera to capture and verify your face for fraud detection.</p>
              <button
                className="btn btn-primary"
                onClick={handleVerifyIdentity}
              >
                📷 Start Identity Verification
              </button>
            </div>
          )}

          {/* Vote Casting Section */}
          {verified && !hasVoted && (
            <div className="eci-card" style={{ background: '#f8f9fa' }}>
              <h3>Step 2: Cast Your Vote</h3>
              <form onSubmit={handleCastVote}>
                <div className="form-group">
                  <label htmlFor="candidate">Select Candidate</label>
                  <select
                    className="form-control"
                    id="candidate"
                    value={selectedCandidate}
                    onChange={(e) => setSelectedCandidate(e.target.value)}
                    required
                  >
                    <option value="">-- Select a Candidate --</option>
                    {candidates.map((c, idx) => (
                      <option key={idx} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="precinct">Select Your Precinct</label>
                  <select
                    className="form-control"
                    id="precinct"
                    value={selectedPrecinct}
                    onChange={(e) => setSelectedPrecinct(e.target.value)}
                    required
                  >
                    <option value="">-- Select a Precinct --</option>
                    {precincts.map(p => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>

                <button type="submit" className="btn btn-primary">Cast Vote</button>
              </form>
            </div>
          )}

          {/* Vote Confirmation */}
          {hasVoted && (
            <div className="alert alert-success">
              <h3>Thank You for Voting!</h3>
              <p>Your vote has been successfully recorded and encrypted.</p>
              <p>You have fulfilled your civic duty in this election.</p>
            </div>
          )}
        </div>
      </div>
    </SiteLayout>
  );
}

export default VoterDashboard;
