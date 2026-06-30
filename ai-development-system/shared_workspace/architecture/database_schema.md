# Database Schema Specifications

Table/Collection design schema blueprints.

---

## 🗄️ Database Tables (DDL)

```sql
-- SQL Blueprint DDL Definitions
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hash_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

---

## 👥 Relationships
* `users` has a one-to-many relationship with `projects` via `projects.user_id`.
