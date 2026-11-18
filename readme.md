# Student Timetable Optimizer – Algorithm Explorer

A full-stack Python Flask and Design & Analysis of Algorithms (DAA) web application that solves the student study-scheduling optimization problem using four classical algorithmic paradigms: **Brute Force**, **Greedy Algorithm**, **Dynamic Programming**, and **Backtracking**.

---

## 1. How to Run Locally in VS Code

1. **Create & Open the Project Folder:**
   - Open **Visual Studio Code**.
   - Click **File → Open Folder...** and select `student_timetable_optimizer`.

2. **Open Integrated Terminal:**
   - Press `` Ctrl + ` `` (or **Terminal → New Terminal**).

3. **Create and Activate a Python Virtual Environment:**
   - **Windows (PowerShell / CMD):**
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the Flask Server:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

## Troubleshooting

- If dependencies are missing, activate the virtual environment and run `pip install -r requirements.txt`.
- If port 5000 is already in use, stop the other process using it before starting this app.
- The comparison charts require an internet connection to load Chart.js from its CDN.
