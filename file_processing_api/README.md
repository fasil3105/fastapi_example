# File Processing API

A backend file-processing and storage API built with **FastAPI**, **PostgreSQL**, **SQLModel**, and **AWS S3-compatible object storage**.

The primary purpose of this project is to demonstrate a secure, validation-driven file upload workflow where uploaded files pass through multiple validation layers before being stored in object storage.

The API also implements JWT authentication, user-based authorization, presigned URLs for secure downloads, file ownership checks, file deletion, and automated unit/integration testing.

---

# 1. What the Project Does

This project provides a backend API for securely uploading, validating, storing, retrieving, and deleting files.

The application separates:

- **File metadata** → stored in PostgreSQL
- **Actual file objects** → stored in AWS S3-compatible object storage

Before a file is stored, it passes through multiple validation layers to verify that the file is valid and that its content matches the expected file type.

The API also ensures that users can access only files that belong to them.

---

# 2. Why the Project Exists

The project demonstrates how to build a backend file-processing system with a focus on:

- Secure authentication
- User-based authorization
- Defensive file validation
- Object storage integration
- Temporary file access using presigned URLs
- Proper error handling
- Separation of database metadata and file storage
- Automated testing

The primary focus is the **validation-driven file upload workflow** rather than simply accepting a file based on its filename or extension.

---

# 3. Features

- User registration and validation
- Secure password hashing
- JWT-based authentication
- User-based authorization
- File upload API
- Multiple file validation layers
- File extension validation
- File size validation
- Magic-byte validation
- MIME type verification
- File extension/content consistency validation
- PDF integrity validation
- Image integrity validation
- AWS S3-compatible object storage
- Presigned URLs for secure file downloads
- File metadata stored in PostgreSQL
- User-specific file access
- File deletion from object storage and database
- Proper HTTP status codes and error handling
- Unit testing
- API integration testing
- S3 operations mocked during automated tests

---

# 4. Architecture and Request Flow

![File Processing API Architecture](docs/File_validation_architecture.png)


## Architecture Flow

### 1. Client → FastAPI

The client sends HTTP requests to the FastAPI application.

Protected endpoints require a valid JWT bearer token.

### 2. Authentication and Authorization

FastAPI authenticates the user using JWT.

For file-related operations, the API verifies that the authenticated user owns the requested file.

Authentication determines **who the user is**, while authorization determines **whether the user is allowed to access the requested resource**.

### 3. File Validation

Uploaded files pass through multiple validation layers:

- File extension validation
- File size validation
- Magic-byte validation
- MIME type validation
- Extension/content consistency validation
- PDF integrity validation
- Image integrity validation

Only files that successfully pass the validation process are stored.

### 4. PostgreSQL

PostgreSQL stores:

- User information
- File metadata
- File ownership information

The actual file content is not stored in PostgreSQL.

### 5. AWS S3 / Floci

The actual file object is stored in S3-compatible object storage.

The application communicates with S3 using `boto3`.

For local development, an S3-compatible local storage service such as Floci can be used.

### 6. Presigned Download URL

When an authorized user requests a file download:

1. FastAPI authenticates the user.
2. The API checks file ownership.
3. A temporary presigned S3 URL is generated.
4. The URL is returned to the client.
5. The client uses the presigned URL to download the file directly from S3-compatible storage.

---

# 5. Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Backend programming language |
| **FastAPI** | REST API framework |
| **Pydantic** | Request and response validation |
| **SQLModel** | ORM and database models |
| **PostgreSQL** | Persistent storage for users and file metadata |
| **JWT** | Authentication |
| **bcrypt** | Password hashing |
| **boto3** | Communication with S3-compatible storage |
| **AWS S3** | Object storage |
| **Floci** | Local S3-compatible object storage during development |
| **Pillow** | Image validation |
| **pypdf** | PDF validation |
| **unittest** | Automated unit and integration testing |

---

# 6. Project Structure

![alt text](docs/Project_structure.png.png)
### Core Components

#### `app/core/security.py`

Responsible for security-related functionality such as:

- Password hashing
- Password verification
- JWT creation
- JWT validation
- Current-user authentication

#### `app/core/storage.py`

Contains the S3-compatible object-storage operations, including:

- Uploading objects
- Deleting objects
- Generating presigned download URLs
- Interacting with the configured S3 bucket

#### `app/db/database.py`

Contains the database configuration and session management used by the application.

#### `app/models/`

Contains database models representing users and file metadata.

#### `app/routes/`

Contains the API endpoints.

- `auth.py` — authentication-related endpoints
- `files.py` — file upload, access, download, and deletion endpoints

#### `app/schemas/`

Contains request and response schemas used for API validation.

#### `tests/`

Contains automated unit and API integration tests.

---

# 7. Authentication and Authorization

The API uses **JWT Bearer Authentication** to protect user-specific endpoints.

## Registration

http
POST /auth/register


The registration process performs the following steps:

1. Validate the request data.
2. Validate the email and password.
3. Check whether the email already exists.
4. Hash the password.
5. Store the user in PostgreSQL.

Passwords are not stored as plaintext.

## Login

http
POST /auth/login


The user provides their email and password.

After successful authentication, the API generates and returns a JWT access token.

Example response:

json
{
    "access_token": "<JWT_TOKEN>",
    "token_type": "bearer"
}


The token is then supplied to protected endpoints:

http
Authorization: Bearer <JWT_TOKEN>

## Authorization

Authentication identifies the user.

Authorization verifies whether the authenticated user is allowed to access a specific file.

For file-related operations, ownership is checked using the authenticated user's ID.


file.user_id == current_user.id


If a user attempts to access another user's file, the API returns:

http
403 Forbidden

This ownership check is applied to operations such as:

- Viewing file metadata
- Downloading files
- Deleting files

---

# 8. File Upload
http
POST /files/uploadfile/


The upload endpoint requires authentication.

Before a file is stored, it passes through multiple validation layers.


Client
   |
   | File + JWT
   v
FastAPI
   |
   v
Extension Validation
   |
   v
File Size Validation
   |
   v
Magic Byte Validation
   |
   v
MIME Type Validation
   |
   v
Extension/Content Validation
   |
   v
File Integrity Validation
   |
   v
S3 Object Storage
   |
   v
PostgreSQL Metadata


Only files that pass the validation pipeline are accepted.

---

# 9. File Validation Layers

The project does not rely only on the file extension supplied by the client.

Multiple validation layers are used to verify that the uploaded file is actually the expected file type.

## 1. Extension Validation

The API checks whether the uploaded file has an allowed extension.

For example:


.pdf
.png
.jpg


Unsupported extensions are rejected.

## 2. File Size Validation

The API determines the size of the uploaded file.

The following files are rejected:

- Empty files
- Files exceeding the configured maximum file size

An oversized file results in:
http
413 Payload Too Large


## 3. Magic-Byte Validation

The API reads the beginning of the file and checks its binary signature.

Magic bytes provide information about the actual file format instead of relying only on the filename.

For example, a file named:


document.png


must contain the expected PNG file signature.

## 4. MIME Type Validation

The detected file type is compared against the expected MIME type.

Examples:


.pdf  → application/pdf
.png  → image/png
.jpg  → image/jpeg


This provides another layer of protection against incorrectly labelled files.

## 5. Extension/Content Consistency

The API verifies that the file extension matches the detected file content.

For example:


image.png
    |
    +-- Extension: .png
    |
    +-- Detected type: image/png
    |
    +-- Valid


A PDF file renamed as `.png` will fail this validation.

## 6. PDF Integrity Validation

PDF files are parsed using `pypdf`.

The application verifies that:

- The PDF can be parsed.
- The PDF contains at least one page.
- PDF pages can be accessed.

Corrupted or invalid PDF files are rejected.

## 7. Image Integrity Validation

PNG and JPEG files are validated using Pillow.

The application verifies that the image can be opened and validated successfully.

Corrupted image files are rejected.

---

# 10. AWS S3 Storage Architecture

The application separates **file metadata** from the **actual file content**.

PostgreSQL stores metadata, while S3-compatible object storage stores the actual file.


                 PostgreSQL
                     |
          +----------+----------+
          |          |          |
        User     File Metadata Ownership


              AWS S3 / Floci
                     |
                     |
              Actual File Object


The application uses `boto3` to communicate with S3-compatible object storage.

## S3 Storage Key

Each uploaded file is assigned a unique storage filename.

Example:


uploads/8f3a21c4.pdf


The storage key identifies the object inside the S3 bucket.

The original filename is stored separately as file metadata.

## Upload to S3

After successful validation:

1. A unique filename is generated.
2. An S3 storage key is created.
3. The validated file is stored in the configured S3 bucket.
4. File metadata is stored in PostgreSQL.

## Download from S3

The API does not expose permanent public access to stored objects.

Instead, it generates a temporary presigned URL.


Client
   |
   | Request Download
   v
FastAPI
   |
   | Authenticate
   |
   | Check Ownership
   |
   | Generate Presigned URL
   v
Client
   |
   | Temporary URL
   v
S3
   |
   v
File


The client can then use the presigned URL to download the file directly from S3.

## Delete from S3

When a user deletes a file:

1. The API retrieves the file metadata.
2. The API verifies file ownership.
3. The S3 object is deleted.
4. The corresponding database metadata is deleted.

If the S3 deletion fails, the database metadata is preserved rather than being removed prematurely.

This prevents the database from indicating that a file was deleted when the storage operation actually failed.

---

# 11. Presigned Download URLs

The API uses presigned URLs instead of making stored files publicly accessible.

When a user requests a download:


1. Authenticate user
       ↓
2. Find file metadata
       ↓
3. Verify ownership
       ↓
4. Generate temporary S3 URL
       ↓
5. Return URL to client
       ↓
6. Client downloads directly from S3


The URL is temporary and provides access to the specific object without exposing the entire S3 bucket.

---

# 12. API Endpoints

## Authentication Endpoints

### Register

http
POST /auth/register


Creates a new user account.

### Login

http
POST /auth/login


Authenticates the user and returns a JWT access token.

---

## File Endpoints

### Upload File

http
POST /files/uploadfile/


Validates and stores an uploaded file.

**Authentication:** Required

---

### List Files

http
GET /files/files


Returns file metadata belonging to the authenticated user.

**Authentication:** Required

---

### Get File Metadata

http
GET /files/files/{file_id}


Returns metadata for a specific file.

The API verifies that the requested file belongs to the authenticated user.

**Authentication:** Required

Possible responses:


200 OK
403 Forbidden
404 Not Found


---

### Download File

http
GET /files/files/{file_id}/download


Generates a temporary presigned URL for the requested file.

The API performs:

1. Authentication
2. File lookup
3. Ownership verification
4. Presigned URL generation

**Authentication:** Required

---

### Delete File

http
DELETE /files/delete/{file_id}


Deletes the file from S3-compatible storage and removes its corresponding metadata from PostgreSQL.

**Authentication:** Required

Deletion flow:


Find File Metadata
        |
        v
Check Ownership
        |
        v
Delete S3 Object
        |
        v
Delete Database Metadata
        |
        v
Return Success


---

# 13. Error Handling

The API uses appropriate HTTP exceptions for different failure scenarios.

| Status Code | Meaning |
|---|---|
| `200` | Request completed successfully |
| `400` | Invalid input or invalid file |
| `401` | Authentication failed |
| `403` | User is not authorized to access the resource |
| `404` | Resource was not found |
| `409` | Resource already exists |
| `413` | File exceeds the maximum allowed size |
| `500` | Internal or storage-related error |

The delete operation also handles storage failures separately.

If deletion from S3 fails, the database metadata is not removed. This prevents the database and object storage from becoming inconsistent.

---

# 14. Testing

The project contains both **unit tests** and **API integration tests**.

The test suite verifies authentication, authorization, file validation, storage interaction, and error-handling behavior.

## Unit Tests

Unit tests cover individual pieces of application logic.

Examples include:

- Password hashing
- Password verification
- Strong password validation
- Weak password rejection
- Invalid email validation

## API Integration Tests

Integration tests verify complete API workflows.

### Authentication Tests

- User registration
- Duplicate registration
- Login
- Invalid login
- Missing authentication token
- Invalid authentication token

### File Upload Tests

- Valid PDF upload
- Valid image upload
- Unsupported file type
- Empty file
- Oversized file
- Corrupted file
- Extension/content mismatch
- Storage failure handling

### File Access Tests

- User accessing their own file
- User attempting to access another user's file
- Missing file returning `404`

### Download Tests

- Presigned URL generation
- Authentication checks
- Ownership checks
- File-not-found handling

### Delete Tests

- Successful deletion
- S3 object deletion
- Database metadata deletion
- Unauthorized deletion
- Storage deletion failure
- Database metadata preservation when storage deletion fails

## S3 Mocking During Tests

S3 operations are mocked during automated tests.

This allows the test suite to verify application behavior without requiring every test to interact with the actual S3 storage service.

This makes the tests:

- Faster
- More deterministic
- Independent of external storage availability

## Running Tests

Run the complete test suite from the project root:

bash
python -m unittest discover -s tests -v


Current test suite:


Ran 16 tests

OK


---

# 15. How to Run the Project

## Prerequisites

Make sure the following are available:

- Python
- PostgreSQL
- S3-compatible object storage
- Required environment variables

## 1. Clone the Repository

bash
git clone <repository-url>


Navigate to the project:

bash
cd file_processing_api


## 2. Create a Virtual Environment

bash
python -m venv .venv


### Windows PowerShell

powershell
.venv\Scripts\Activate.ps1


### Linux / macOS

bash
source .venv/bin/activate


## 3. Install Dependencies

bash
pip install -r requirements.txt


## 4. Configure Environment Variables

Create a `.env` file containing the required configuration.

Example:

env
DATABASE_URL=postgresql://username:password@localhost/database

AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

AWS_ENDPOINT_URL=http://localhost:4566

S3_BUCKET_NAME=file-upload

JWT_SECRET_KEY=your-jwt-secret


Do not commit real credentials or secrets to GitHub.

Make sure `.env` is included in `.gitignore`.

## 5. Start the Application

Run the FastAPI application using:

bash
uvicorn app.main:app --reload


The application will be available at:


http://127.0.0.1:8000


---

# 16. Swagger / ReDoc

FastAPI automatically provides interactive API documentation.

## Swagger UI


http://127.0.0.1:8000/docs


Swagger UI can be used to:

- View available endpoints
- Inspect request and response schemas
- Authenticate using the JWT bearer token
- Test API endpoints

## ReDoc


http://127.0.0.1:8000/redoc


ReDoc provides another interface for exploring the generated API documentation.

---

# 17. Security Considerations, Design Decisions and Future Improvements

## Security Considerations

The project applies security controls at multiple levels.

### Authentication

JWT authentication protects private API endpoints.

### Password Security

Passwords are hashed before being stored in the database.

### Authorization

File ownership is checked before allowing users to access, download, or delete files.

### File Validation

Uploaded files are checked using multiple validation mechanisms rather than trusting the supplied filename.

### Object Storage

Files are stored in object storage rather than being exposed directly through the application server.

### Presigned URLs

Download access is provided through temporary presigned URLs rather than permanent public object URLs.

### Credentials

Storage credentials and application secrets are configured through environment variables.

---

## Design Decisions

### PostgreSQL for Metadata

The database stores structured information such as:

- Users
- File metadata
- File ownership

The database is not used to store the actual binary file content.

This keeps metadata management separate from object storage.

### S3 for File Storage

Object storage is used for the actual file objects and provides operations for:

- Uploading objects
- Retrieving objects
- Deleting objects
- Generating temporary access URLs

### Multiple File Validation Layers

The project does not rely only on file extensions.

The validation pipeline combines:


Extension
    +
File Size
    +
Magic Bytes
    +
MIME Type
    +
Extension/Content Consistency
    +
File Integrity


This provides multiple checks before a file is accepted.

### Ownership-Based Authorization

Every stored file is associated with a user.

This allows the API to enforce:


Authenticated User
        |
        v
File Ownership Check
        |
        +---- Own File ----> Allow
        |
        +---- Other User --> 403 Forbidden


---

## Future Improvements

Possible future improvements include:

- Refresh token support
- Rate limiting
- Pagination for large file lists
- Antivirus/malware scanning
- Background file processing
- File versioning
- Soft deletion
- CI/CD pipeline
- Docker containerization
- Production deployment
- Centralized logging
- Application monitoring

---

# Author

**Muhammad Fasil**

Backend / Software Engineering Project

**Technologies:** Python · FastAPI · PostgreSQL · SQLModel · AWS S3 · boto3
