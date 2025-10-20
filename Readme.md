
## FastApi

```
job_portal/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── utils/
│   │   ├── auth.py
│   │   └── helpers.py
│   ├── routers/
│   │   ├── users.py
│   │   ├── jobs.py
│   │   ├── applications.py
│   │   └── auth.py
│   └── schemas/
│       ├── user_schemas.py
│       ├── job_schemas.py
│       └── application_schemas.py
│
└── requirements.txt


-- login as root in shell
sudo mysql

-- create user
CREATE USER 'user'@'localhost' IDENTIFIED BY 'StrongPass123';

-- grant privileges on your database
GRANT ALL PRIVILEGES ON job_portal.* TO 'jobuser'@'localhost';

-- apply changes
FLUSH PRIVILEGES;
```

### run :
 - create : job_portal/app/migrations/dbinit.sql
 -  make install 
 -  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


----------------------------------------------------------------------------


Here’s a clean **table version of all backend APIs** for easy frontend integration:

| HTTP Method | Endpoint                                       | Role      | Description                                                 |
| ----------- | ---------------------------------------------- | --------- | ----------------------------------------------------------- |
| POST        | `/auth/login`                                  | All       | Login user, returns JWT token                               |
| POST        | `/users/register`                              | All       | Register new user (role: applicant/employer)                |
| PUT         | `/users/update_profile`                        | Applicant | Update bio and skills                                       |
| POST        | `/users/upload_resume`                         | Applicant | Upload resume                                               |
| GET         | `/users/me`                                    | All       | Get current user profile                                    |
| GET         | `/jobs/`                                       | All       | List all jobs                                               |
| GET         | `/jobs/search`                                 | All       | Search/filter jobs by title, location, company              |
| POST        | `/jobs/`                                       | Employer  | Create new job                                              |
| PUT         | `/jobs/close/{job_id}`                         | Employer  | Close a job                                                 |
| DELETE      | `/jobs/{job_id}`                               | Employer  | Delete a job                                                |
| POST        | `/applications/apply`                          | Applicant | Apply to a job                                              |
| GET         | `/applications/user/{user_id}`                 | Applicant | View my applications                                        |
| GET         | `/applications/job/{job_id}/applicants`        | Employer  | View applicants for a job (supports pagination & filtering) |
| GET         | `/applications/resume/{applicant_id}`          | Employer  | Download applicant resume                                   |
| PUT         | `/applications/update_status/{application_id}` | Employer  | Update application status (reviewed, shortlisted, rejected) |

---

This table can be used directly for **frontend integration and API documentation**.

Next, we can start building the **frontend skeleton** with login, job listing, and dashboards. Do you want me to start that?


