# 🧠 EY Query Management Agent

A role-based **Query & Ticket Management Dashboard** built with **Flask**, **Pandas**, **Matplotlib**, and a modern **Bootstrap UI**.

This application provides:

* 🔐 Secure Login System
* 👤 Role-based access (Admin / Manager / Employee)
* 📊 Advanced Manager Dashboard with analytics & filters
* 🧾 Invoice & Ticket insights from Excel data
* 💬 Chat UI (frontend ready for future AI integration)
* 👥 Admin user management

---

## ✨ Features

### 👨‍💼 Admin

* Add and manage users
* Assign roles (Manager / Employee)
* View all users in the system

### 📈 Manager

* Full analytics dashboard
* Filter tickets by **Team / User / Type**
* KPI cards for tickets and invoices
* Charts for:

  * Ticket status distribution
  * Tickets by team & type
  * Invoice payment status

### 🧑‍💻 Employee

* View only their assigned open tickets
* Clean ticket table with priority, status, and category

### 💬 Chat Interface

* Dedicated chat UI
* Session-ready layout for future AI integration

---

## 🗂️ Project Structure

```
.
├── backend/
│   ├── app.py           (Flask routes & logic)
│   ├── config.py        (Azure OpenAI Config)
│   ├── table_db.py      (Excel data utilities)
│   ├── user.json        (User database)
│   ├── requirements.txt (Dependencies)
│   └── QMT Data New.xlsx (Data Source)
├── frontend/
│   ├── templates/       (HTML Jinja2 templates)
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── admin_dashboard.html
│   │   ├── manager_dashboard.html
│   │   ├── employee_dashboard.html
│   │   └── chat.html
│   └── static/          (CSS, JS, Images)
└── README.md
```

---

## 🧩 Key Files

* Main Flask app and routing: 
* Admin UI: 
* Base layout and theme: 
* Chat UI: 
* Employee tickets view: 
* Login page: 
* Manager analytics dashboard: 

---

## 🛠️ Tech Stack

* **Backend**: Flask, Pandas
* **Frontend**: Bootstrap 5, HTML, CSS, FontAwesome
* **Visualization**: Matplotlib
* **Data Source**: Excel → Pandas DataFrames
* **Auth**: Session-based login with role control

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repo

```bash
git clone https://github.com/your-username/ey-query-agent.git
cd ey-query-agent
```

### 2️⃣ Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3️⃣ Setup Environment

Create a `.env` file in the `backend/` directory with your Azure OpenAI credentials.

### 4️⃣ Run the app

```bash
cd backend
python app.py
```

App runs on:

```
http://localhost:5000/login
```

---

## 👤 Default Users (if `user.json` not present)

| Role     | Email                                   | Password |
| -------- | --------------------------------------- | -------- |
| Admin    | [admin@ey.com](mailto:admin@ey.com)     | 123      |
| Manager  | [manager@ey.com](mailto:manager@ey.com) | 123      |
| Employee | [robert@ey.com](mailto:robert@ey.com)   | 123      |

---

## 📊 Dashboard Capabilities

* Ticket KPIs (Open, Closed, Auto-resolved, AP vs AR)
* Invoice KPIs (Paid, Unpaid, Overdue, Total Amount)
* Interactive filtering
* Auto-generated charts from live data

---

## 🚀 Future Scope

* Connect Chat UI with AI backend
* Replace JSON users with database
* Add ticket drill-down pages
* Export dashboard reports

---

## 🧠 Note on Data Schema Update

The data schema was **recently updated** because the structure of the Excel file changed significantly.
All dashboards and filters are aligned with the **new data format**.

---

## 📸 Screenshots

> Add screenshots of Login, Admin, Manager, and Employee dashboards here.

---

## 🏁 Author

Built as part of an EY internal query management and analytics system.

---
