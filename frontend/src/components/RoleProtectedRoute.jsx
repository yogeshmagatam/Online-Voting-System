import React from 'react';

/**
 * Component to protect routes based on user role
 * Only allows access if user has one of the required roles
 */
function RoleProtectedRoute({ userRole, requiredRoles, children, fallback }) {
  // Check if user's role is in the required roles
  const hasAccess = requiredRoles.includes(userRole);

  if (!hasAccess) {
    return fallback || (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h2>Access Denied</h2>
        <p>You do not have permission to access this page.</p>
        <p>Your role: <strong>{userRole}</strong></p>
        <p>Required role(s): <strong>{requiredRoles.join(', ')}</strong></p>
      </div>
    );
  }

  return children;
}

export default RoleProtectedRoute;
