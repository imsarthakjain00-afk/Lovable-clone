# OpenAPI & Endpoint Specifications

Design requirements for APIs.

---

## 🌐 API Routes

### 1. `POST /api/v1/auth/register`
* **Purpose**: Register a new user account.
* **Headers**: `Content-Type: application/json`
* **Request Schema (JSON)**:
```json
{
  "email": "string (format: email)",
  "password": "string (min_length: 8)"
}
```
* **Success Response (201 Created)**:
```json
{
  "user_id": "integer",
  "status": "active"
}
```
* **Error Response (400 Bad Request)**:
```json
{
  "error": "Email already exists"
}
```
