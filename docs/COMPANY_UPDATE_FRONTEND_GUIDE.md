# Company Update API - Frontend Guide

This guide explains how to implement company information updates in the frontend application, covering both general information updates and password changes.

## Overview

The company update system provides two main functionalities:
1. **Partial Information Updates** - Update any combination of company fields
2. **Password Changes** - Dedicated secure flow for password updates

## Authentication Required

Both endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## 1. Company Information Updates

### Endpoint: `PATCH /companies/me`

Updates company information with partial data support. Only the fields provided in the request will be updated.

### Request Format
```json
{
  "name": "string (optional)",
  "email": "string (optional)", 
  "phone_number": "string (optional)",
  "address": "string (optional)",
  "vat_number": "string (optional)"
}
```

### Response Format
```json
{
  "id": 123,
  "name": "Updated Company Name",
  "email": "updated@company.com",
  "phone_number": "+1234567890",
  "address": "123 Updated Street",
  "vat_number": "VAT123456",
  "login": "12345678",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "players_count": null,
  "courts_count": null,
  "tournaments_count": null
}
```

### Frontend Implementation Examples

#### Update Single Field


#### Update Multiple Fields

### Error Handling

Common error responses:

- **400 Bad Request**: No fields provided or email already exists
- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Company not found



## 2. Password Change

### Endpoint: `POST /companies/me/change-password`

Secure password change flow that requires current password verification.

### Request Format
```json
{
  "current_password": "string (required)",
  "new_password": "string (required, min 8 chars)",
  "confirm_password": "string (required, must match new_password)"
}
```

### Response Format
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

### Password Change Error Handling

Common error responses:

- **400 Bad Request**: 
  - Current password is incorrect
  - Password confirmation mismatch
  - Password too short
- **401 Unauthorized**: Invalid authentication token


## UI/UX Recommendations

### Information Update Form

1. **Progressive Enhancement**: Allow users to edit individual fields inline or use a comprehensive edit form
2. **Real-time Validation**: Validate email format and required fields before submission
3. **Optimistic Updates**: Update UI immediately, rollback on error
4. **Save Indicators**: Show saving status and confirmation messages

### Password Change Form

1. **Separate Form**: Keep password changes in a dedicated, secure section
2. **Current Password First**: Always require current password verification
3. **Password Strength Indicator**: Show password strength as user types
4. **Confirmation Field**: Require password confirmation with real-time matching validation
5. **Security Messaging**: Explain password requirements clearly



## Security Considerations

1. **Always validate on frontend**: Provide immediate feedback to users
2. **Handle token expiration**: Implement proper token refresh or redirect to login
3. **Secure password handling**: Never log or store passwords in plain text
4. **Rate limiting awareness**: Implement appropriate retry mechanisms
5. **HTTPS only**: Ensure all requests are made over HTTPS in production

## Integration Notes

- Both endpoints integrate with the existing authentication system
- Email updates are validated for uniqueness across the system  
- Password changes invalidate existing sessions (users may need to re-login)
- All updates trigger the `updated_at` timestamp automatically
- Field validation follows the same patterns as user registration 