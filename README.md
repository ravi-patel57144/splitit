# Split It - Expense Splitting API

A Django REST API for splitting expenses among groups of people. This application allows users to create occasions, events, and track expenditures with automatic expense splitting functionality.

## Features

- **JWT Authentication**: Secure API access using JSON Web Tokens
- **Occasion Management**: Group related events and expenses
- **Event Management**: Create and manage expense events
- **Expense Splitting**: 
  - Equal split among participants
  - Custom amount distribution
  - Automatic calculation and validation
- **Payment Tracking**: Track payments between users
- **Balance Management**: View user balances and settlement status
- **Comprehensive API Documentation**: Swagger/OpenAPI documentation

## Installation

### Prerequisites

- Python 3.8+
- Django 5.2+
- SQLite (default database)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SplitIt
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Authentication

- `POST /api/auth/token/` - Obtain JWT token
- `POST /api/auth/token/refresh/` - Refresh JWT token

### Occasions

- `GET /api/occasions/` - List all occasions
- `POST /api/occasions/` - Create new occasion
- `GET /api/occasions/{id}/` - Get occasion details
- `PUT /api/occasions/{id}/` - Update occasion
- `DELETE /api/occasions/{id}/` - Delete occasion
- `GET /api/occasions/{id}/summary/` - Get occasion summary

### Events

- `GET /api/events/` - List all events
- `POST /api/events/` - Create new event
- `GET /api/events/{id}/` - Get event details
- `PUT /api/events/{id}/` - Update event
- `DELETE /api/events/{id}/` - Delete event
- `GET /api/events/{id}/expenditures/` - Get event expenditures

### Expenditures

- `GET /api/expenditures/` - List all expenditures
- `POST /api/expenditures/` - Create new expenditure
- `GET /api/expenditures/{id}/` - Get expenditure details
- `PUT /api/expenditures/{id}/` - Update expenditure
- `DELETE /api/expenditures/{id}/` - Delete expenditure

### Payments

- `GET /api/payments/` - List all payments
- `POST /api/payments/` - Create new payment
- `GET /api/payments/{id}/` - Get payment details
- `PUT /api/payments/{id}/` - Update payment
- `DELETE /api/payments/{id}/` - Delete payment
- `POST /api/expenditure-splits/{id}/settle/` - Settle an expenditure split

### User

- `GET /api/user/balance/` - Get user balance

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/api/docs/`
- Schema: `http://localhost:8000/api/schema/`

## Usage Examples

### 1. Authentication

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

### 2. Create an Occasion

```bash
curl -X POST http://localhost:8000/api/occasions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Weekend Trip", "description": "Splitting expenses for weekend trip"}'
```

### 3. Create an Event

```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Dinner", "description": "Group dinner", "occasion": 1}'
```

### 4. Create an Expenditure with Equal Split

```bash
curl -X POST http://localhost:8000/api/expenditures/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event": 1,
    "amount": "120.00",
    "description": "Restaurant bill",
    "split_type": "equal",
    "split_user_ids": [2, 3, 4]
  }'
```

### 5. Create an Expenditure with Custom Split

```bash
curl -X POST http://localhost:8000/api/expenditures/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event": 1,
    "amount": "100.00",
    "description": "Custom split expense",
    "split_type": "custom",
    "split_user_ids": [2, 3],
    "custom_amounts": ["60.00", "40.00"]
  }'
```

### 6. Create a Payment

```bash
curl -X POST http://localhost:8000/api/payments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_user_id": 2,
    "amount": "40.00",
    "description": "Settlement payment"
  }'
```

### 7. Settle an Expenditure Split

```bash
curl -X POST http://localhost:8000/api/expenditure-splits/123/settle/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8. Get User Balance

```bash
curl -X GET http://localhost:8000/api/user/balance/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Database Models

### Occasion
- Groups related events and expenses
- Fields: name, description, created_by, created_at, updated_at

### Event
- Individual expense events that can be grouped under occasions
- Fields: name, description, occasion, created_by, created_at, updated_at

### Expenditure
- Individual expenses within an event
- Fields: event, amount, description, paid_by, split_type, created_at, updated_at

### ExpenditureSplit
- Tracks how an expenditure is split among users
- Fields: expenditure, user, amount, is_paid, created_at, updated_at

### Payment
- Tracks payments between users
- Fields: from_user, to_user, amount, description, status, created_at, updated_at

## Testing

Run the test suite:

```bash
python manage.py test
```

The test suite includes:
- Authentication tests
- CRUD operations for all models
- Expense splitting logic validation
- Payment settlement functionality
- Balance calculation accuracy

## Business Logic

### Expense Splitting

1. **Equal Split**: Amount is divided equally among all specified users
2. **Custom Split**: Users specify exact amounts for each participant
   - Total of custom amounts must equal the expenditure amount
   - Validation ensures accuracy

### Payment Settlement

- Users can create payments to settle debts
- Payments can be marked as completed
- Balance calculations consider both expenditures and payments

### Balance Calculation

- **Total Owed**: Amount user owes to others
- **Total Owes**: Amount others owe to user
- **Balance**: Total Owes - Total Owed

## Security

- JWT-based authentication
- All API endpoints require authentication
- User can only access their own data
- Input validation and sanitization

## Error Handling

The API provides comprehensive error handling:
- Validation errors for invalid data
- Authentication errors for unauthorized access
- Not found errors for non-existent resources
- Business logic errors for invalid operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.
