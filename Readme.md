
## FastApi







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


uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

