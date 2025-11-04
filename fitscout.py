"""
Sports Connect - Streamlit app v2.0 (upgraded)
Retains 100% of the original functionality and adds:
- Charts (matplotlib) for athlete progress and distributions
- Performance tracking over time (metrics_history.csv)
- Simple team-athlete matching score
- Admin analytics / leaderboard
- Search & filter for athletes
- CSV export / download buttons

Single-file app. Save as sports_connect.py and run with Streamlit.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, Any, List
import matplotlib.pyplot as plt

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="Sports Connect v2.0", layout="wide")
DATA_DIR = "app_data"
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
TEAMS_CSV = os.path.join(DATA_DIR, "teams.csv")
APPLICATIONS_CSV = os.path.join(DATA_DIR, "applications.csv")
HISTORY_CSV = os.path.join(DATA_DIR, "metrics_history.csv")
ADMIN_PASSWORD = "admin123"

# -------------------------
# Utility functions (must stay at top)
# -------------------------

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    try:
        h_m = float(height_cm) / 100.0
        bmi = float(weight_kg) / (h_m * h_m)
        return round(bmi, 2)
    except Exception:
        return float('nan')


def vo2_estimate(weight_kg: float, height_cm: float, pace_kmph: float) -> float:
    try:
        vo2 = (pace_kmph * 3.5) + (height_cm / 100.0) * 2.0 - (weight_kg / 50.0)
        return round(vo2, 2)
    except Exception:
        return float('nan')


def pace_from_time(distance_km: float, time_min: float) -> float:
    if distance_km <= 0 or time_min <= 0:
        return float('nan')
    hours = float(time_min) / 60.0
    return round(distance_km / hours, 2)


def fatigue_recovery_rate(training_load: float, sleep_hours: float, age: int) -> float:
    base = max(0, 10 - float(training_load) / 10.0)
    sleep_factor = min(1.5, float(sleep_hours) / 8.0)
    age_penalty = max(0, (int(age) - 25) / 100.0)
    score = (base * sleep_factor) - age_penalty
    return round(score, 2)


def bmi_category(bmi: float) -> str:
    try:
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"
    except Exception:
        return "Unknown"

# -------------------------
# History/helper for tracking metrics over time
# -------------------------

def append_history(username: str, metrics: Dict[str, Any]):
    ensure_data_dir()
    cols = ["timestamp","username","bmi","vo2","pace_kmph","training_load","sleep_hours","recovery_score"]
    row = {
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "bmi": metrics.get('bmi'),
        "vo2": metrics.get('vo2'),
        "pace_kmph": metrics.get('pace_kmph'),
        "training_load": metrics.get('training_load'),
        "sleep_hours": metrics.get('sleep_hours'),
        "recovery_score": metrics.get('recovery_score')
    }
    if not os.path.exists(HISTORY_CSV):
        pd.DataFrame([row])[cols].to_csv(HISTORY_CSV, index=False)
    else:
        df = pd.read_csv(HISTORY_CSV)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(HISTORY_CSV, index=False)


def load_history() -> pd.DataFrame:
    ensure_data_dir()
    if os.path.exists(HISTORY_CSV):
        return pd.read_csv(HISTORY_CSV)
    return pd.DataFrame(columns=["timestamp","username","bmi","vo2","pace_kmph","training_load","sleep_hours","recovery_score"])

# -------------------------
# Seed data helper (uses above functions)
# -------------------------

def seed_data():
    ensure_data_dir()
    # Users
    if not os.path.exists(USERS_CSV):
        users = pd.DataFrame([
            {"username": "ravi23", "name": "Ravi Kumar", "age": 23, "weight_kg": 70.0, "height_cm": 175.0,
             "bmi": calculate_bmi(70.0,175.0), "vo2_est": vo2_estimate(70,175,12.0), "active": True, "created_at": datetime.now().isoformat()},
            {"username": "anita20", "name": "Anita Sharma", "age": 20, "weight_kg": 60.0, "height_cm": 165.0,
             "bmi": calculate_bmi(60.0,165.0), "vo2_est": vo2_estimate(60,165,10.0), "active": True, "created_at": datetime.now().isoformat()}
        ])
        users.to_csv(USERS_CSV, index=False)

    # Teams
    if not os.path.exists(TEAMS_CSV):
        teams = pd.DataFrame([
            {"team_id": 1, "team_name": "Speedsters FC", "requirement": "Sprinter/Speed-focused; 100m < 11s desirable"},
            {"team_id": 2, "team_name": "Enduro Runners", "requirement": "High VO2 endurance; 10km performance"},
            {"team_id": 3, "team_name": "PowerHouse", "requirement": "Strength & power athletes"},
            {"team_id": 4, "team_name": "Aqua Pros", "requirement": "Swimmers: 400m+ specialists"},
            {"team_id": 5, "team_name": "Trail Blazers", "requirement": "Trail endurance; ankle stability"},
            {"team_id": 6, "team_name": "City Cyclers", "requirement": "Cyclists with high FTP"},
            {"team_id": 7, "team_name": "Court Kings", "requirement": "Court-sport agility & vertical"},
            {"team_id": 8, "team_name": "Marathoners United", "requirement": "Marathon pacing specialists"},
            {"team_id": 9, "team_name": "Rowing Elite", "requirement": "Rowers: erg scores & height"},
            {"team_id": 10, "team_name": "Scouts Collective", "requirement": "General scouting team"}
        ])
        teams.to_csv(TEAMS_CSV, index=False)

    # Applications
    if not os.path.exists(APPLICATIONS_CSV):
        apps = pd.DataFrame(columns=["app_id","username","team_id","team_name","status","applied_at","admin_note"])
        apps.to_csv(APPLICATIONS_CSV, index=False)

    # History - create empty if not exists
    if not os.path.exists(HISTORY_CSV):
        pd.DataFrame(columns=["timestamp","username","bmi","vo2","pace_kmph","training_load","sleep_hours","recovery_score"]).to_csv(HISTORY_CSV, index=False)

# -------------------------
# Data load/save functions
# -------------------------

def load_users() -> pd.DataFrame:
    ensure_data_dir()
    if os.path.exists(USERS_CSV):
        return pd.read_csv(USERS_CSV)
    return pd.DataFrame(columns=["username","name","age","weight_kg","height_cm","bmi","vo2_est","active","created_at"])


def save_users(df: pd.DataFrame):
    ensure_data_dir()
    df.to_csv(USERS_CSV, index=False)


def load_teams() -> pd.DataFrame:
    ensure_data_dir()
    if os.path.exists(TEAMS_CSV):
        return pd.read_csv(TEAMS_CSV)
    return pd.DataFrame(columns=["team_id","team_name","requirement"])


def save_teams(df: pd.DataFrame):
    ensure_data_dir()
    df.to_csv(TEAMS_CSV, index=False)


def load_applications() -> pd.DataFrame:
    ensure_data_dir()
    if os.path.exists(APPLICATIONS_CSV):
        return pd.read_csv(APPLICATIONS_CSV)
    return pd.DataFrame(columns=["app_id","username","team_id","team_name","status","applied_at","admin_note"])


def save_applications(df: pd.DataFrame):
    ensure_data_dir()
    df.to_csv(APPLICATIONS_CSV, index=False)

# -------------------------
# CRUD operations
# -------------------------

def add_user(user: Dict[str, Any]) -> bool:
    df = load_users()
    if user.get("username") in df["username"].values:
        return False
    df = pd.concat([df, pd.DataFrame([user])], ignore_index=True)
    save_users(df)
    return True


def update_user(username: str, updates: Dict[str, Any]) -> bool:
    df = load_users()
    if username not in df["username"].values:
        return False
    idx = df.index[df["username"] == username][0]
    for k, v in updates.items():
        df.at[idx, k] = v
    # Recalculate bmi if needed
    try:
        df.at[idx, 'bmi'] = calculate_bmi(float(df.at[idx, 'weight_kg']), float(df.at[idx, 'height_cm']))
    except Exception:
        pass
    save_users(df)
    return True


def delete_user(username: str) -> bool:
    df = load_users()
    if username not in df["username"].values:
        return False
    df = df[df["username"] != username]
    save_users(df)
    return True


def add_team(team_name: str, requirement: str) -> bool:
    df = load_teams()
    if team_name in df["team_name"].values:
        return False
    next_id = int(df["team_id"].max()) + 1 if not df.empty else 1
    new = {"team_id": int(next_id), "team_name": team_name, "requirement": requirement}
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    save_teams(df)
    return True


def delete_team(team_id: int) -> bool:
    df = load_teams()
    if int(team_id) not in df["team_id"].values:
        return False
    df = df[df["team_id"] != int(team_id)]
    save_teams(df)
    return True


def apply_to_team(username: str, team_id: int) -> bool:
    users = load_users()
    teams = load_teams()
    apps = load_applications()
    if username not in users["username"].values:
        return False
    if int(team_id) not in teams["team_id"].values:
        return False
    team_name = teams.loc[teams["team_id"] == int(team_id), "team_name"].values[0]
    next_id = int(apps["app_id"].max()) + 1 if (not apps.empty and apps["app_id"].notnull().any()) else 1
    new_app = {"app_id": int(next_id), "username": username, "team_id": int(team_id), "team_name": team_name,
               "status": "Pending", "applied_at": datetime.now().isoformat(), "admin_note": ""}
    apps = pd.concat([apps, pd.DataFrame([new_app])], ignore_index=True)
    save_applications(apps)
    return True


def admin_send_to_team(app_id: int, note: str = "") -> bool:
    apps = load_applications()
    if int(app_id) not in apps["app_id"].values:
        return False
    idx = apps.index[apps["app_id"] == int(app_id)][0]
    apps.at[idx, "status"] = "Sent to Team"
    apps.at[idx, "admin_note"] = note
    save_applications(apps)
    return True


def admin_reject_application(app_id: int, reason: str = "") -> bool:
    apps = load_applications()
    if int(app_id) not in apps["app_id"].values:
        return False
    idx = apps.index[apps["app_id"] == int(app_id)][0]
    apps.at[idx, "status"] = "Rejected"
    apps.at[idx, "admin_note"] = reason
    save_applications(apps)
    return True


def compare_clients(usernames: List[str]) -> pd.DataFrame:
    users = load_users()
    sel = users[users["username"].isin(usernames)].copy()
    if not sel.empty:
        sel["bmi_category"] = sel["bmi"].apply(lambda x: bmi_category(x))
    return sel

# -------------------------
# Matching logic (simple)
# -------------------------

def team_match_score(username: str, team_id: int) -> float:
    users = load_users()
    teams = load_teams()
    if username not in users['username'].values or int(team_id) not in teams['team_id'].values:
        return 0.0
    user = users[users['username'] == username].iloc[0]
    # Simple heuristic: favor higher vo2 and 'normal' BMI
    vo2 = float(user.get('vo2_est', 0) or 0)
    bmi = float(user.get('bmi', 0) or 0)
    # Normalize: vo2 (0-60) -> 0-1 ; bmi ideal ~21-25
    vo2_score = min(max((vo2 / 60.0), 0), 1)
    bmi_score = 1 - min(abs(bmi - 22.5) / 20.0, 1)
    score = (vo2_score * 0.7) + (bmi_score * 0.3)
    return round(score * 100, 1)

# -------------------------
# Admin analytics / leaderboard
# -------------------------

def admin_leaderboard(top_n: int = 5) -> Dict[str, pd.DataFrame]:
    users = load_users()
    # Top by vo2
    df_vo2 = users.sort_values('vo2_est', ascending=False).head(top_n)[['username','name','vo2_est']]
    # Best recovery (estimate from history latest)
    hist = load_history()
    if not hist.empty:
        latest = hist.sort_values('timestamp').groupby('username').tail(1)
        best_recovery = latest.sort_values('recovery_score', ascending=False).head(top_n)[['username','recovery_score']]
    else:
        best_recovery = pd.DataFrame(columns=['username','recovery_score'])
    return {"top_vo2": df_vo2, "best_recovery": best_recovery}

# -------------------------
# Initialize seed data
# -------------------------
seed_data()

# -------------------------
# Streamlit session helpers
# -------------------------

if 'client_logged_in' not in st.session_state:
    st.session_state['client_logged_in'] = False
if 'client_username' not in st.session_state:
    st.session_state['client_username'] = None
if 'admin_logged_in' not in st.session_state:
    st.session_state['admin_logged_in'] = False

# -------------------------
# Top-level UI: Choose role
# -------------------------
st.title("Sports Connect — Athletes & Scouts (v2.0)")
st.markdown("A compact platform to showcase athletes, manage teams, route applications, and visualize performance.")

role = st.sidebar.radio("I am a:", ("Athlete / Client", "Admin"))

# -------------------------
# ATHLETE / CLIENT FLOW
# -------------------------
if role == "Athlete / Client":
    # Show login/register only if not logged in
    if not st.session_state['client_logged_in']:
        st.header("Athlete — Login or Register")
        left, right = st.columns(2)
        with left:
            st.subheader("Login (existing users)")
            login_username = st.text_input("Username to login", key="login_username")
            if st.button("Login as Athlete"):
                users = load_users()
                if login_username in users['username'].values:
                    st.session_state['client_logged_in'] = True
                    st.session_state['client_username'] = login_username
                    st.success(f"Logged in as {login_username}")
                    st.rerun()
                else:
                    st.error("Username not found. Please register on the right if you're new.")

        with right:
            st.subheader("Register (only if username not present)")
            reg_username = st.text_input("Choose username", key="reg_username")
            reg_name = st.text_input("Full name", key="reg_name")
            reg_age = st.number_input("Age", min_value=10, max_value=100, value=20, key="reg_age")
            reg_weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0, key="reg_weight")
            reg_height = st.number_input("Height (cm)", min_value=120.0, max_value=250.0, value=170.0, key="reg_height")
            if st.button("Register new athlete"):
                users = load_users()
                if not reg_username:
                    st.error("Provide a username to register.")
                elif reg_username in users['username'].values:
                    st.error("Username already exists — please pick a different one or login.")
                else:
                    user = {"username": reg_username, "name": reg_name or reg_username, "age": int(reg_age),
                            "weight_kg": float(reg_weight), "height_cm": float(reg_height),
                            "bmi": calculate_bmi(float(reg_weight), float(reg_height)),
                            "vo2_est": vo2_estimate(float(reg_weight), float(reg_height), 10.0),
                            "active": True, "created_at": datetime.now().isoformat()}
                    add_user(user)
                    st.success("Registered successfully — now login on the left.")
    else:
        # Athlete dashboard - use tabs for clean layout
        username = st.session_state['client_username']
        users_df = load_users()
        if username not in users_df['username'].values:
            st.error("Logged-in username not found in DB. Please re-login.")
            st.session_state['client_logged_in'] = False
            st.session_state['client_username'] = None
            st.rerun()

        st.header(f"Athlete Dashboard — {username}")
        tabs = st.tabs(["Profile", "Metrics", "Athletes (Dataset)", "Teams & Apply", "Advanced & Feedback"])

        # Profile tab
        with tabs[0]:
            st.subheader("Profile")
            user_row = users_df[users_df['username'] == username].iloc[0]
            col1, col2 = st.columns([2, 3])
            with col1:
                st.write(f"Name: {user_row['name']}")
                st.write(f"Age: {int(user_row['age'])}")
                st.write(f"Weight (kg): {user_row['weight_kg']}")
                st.write(f"Height (cm): {user_row['height_cm']}")
                st.write(f"BMI: {user_row['bmi']} ({bmi_category(user_row['bmi'])})")
                st.write(f"VO2 est (ml/kg/min): {user_row.get('vo2_est', 'N/A')}")
                if st.button("Edit Profile"):
                    with st.form("edit_profile_form"):
                        e_name = st.text_input("Name", value=user_row['name'])
                        e_age = st.number_input("Age", min_value=10, max_value=100, value=int(user_row['age']))
                        e_weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=float(user_row['weight_kg']))
                        e_height = st.number_input("Height (cm)", min_value=120.0, max_value=250.0, value=float(user_row['height_cm']))
                        submitted = st.form_submit_button("Save")
                        if submitted:
                            updates = {"name": e_name, "age": int(e_age), "weight_kg": float(e_weight), "height_cm": float(e_height)}
                            update_user(username, updates)
                            st.success("Profile updated")
                            st.rerun()

            with col2:
                st.subheader("Quick actions")
                if st.button("Logout"):
                    st.session_state['client_logged_in'] = False
                    st.session_state['client_username'] = None
                    st.success("Logged out")
                    st.rerun()

                st.markdown("---")
                st.write("Account created:")
                st.write(user_row.get('created_at', 'Unknown'))

        # Metrics tab
        with tabs[1]:
            st.subheader("Metrics & Calculators")
            mcol1, mcol2 = st.columns(2)
            with mcol1:
                st.write("Pace & VO2")
                test_dist = st.number_input("Test distance (km)", min_value=0.1, max_value=50.0, value=5.0, key="test_dist")
                test_time = st.number_input("Time (minutes)", min_value=1.0, max_value=500.0, value=25.0, key="test_time")
                pace = pace_from_time(test_dist, test_time)
                st.write(f"Pace (km/h): {pace}")
                vo2 = vo2_estimate(user_row['weight_kg'], user_row['height_cm'], pace)
                st.write(f"Estimated VO2 (ml/kg/min): {vo2}")
                if st.button("Save metrics to profile"):
                    update_user(username, {"vo2_est": vo2, "bmi": calculate_bmi(user_row['weight_kg'], user_row['height_cm'])})
                    # append to history (track progress)
                    recov_score = fatigue_recovery_rate(0, 7, int(user_row['age']))
                    append_history(username, {"bmi": calculate_bmi(user_row['weight_kg'], user_row['height_cm']), "vo2": vo2, "pace_kmph": pace, "training_load": 0, "sleep_hours": 7, "recovery_score": recov_score})
                    st.success("Metrics saved and history updated")
                    st.rerun()

            with mcol2:
                st.write("Fatigue & Recovery")
                sleep_hours = st.number_input("Last night sleep (hours)", min_value=0.0, max_value=24.0, value=7.0, key="sleep_hours")
                training_load = st.number_input("Recent training load (0-100)", min_value=0.0, max_value=500.0, value=40.0, key="training_load")
                recov_score = fatigue_recovery_rate(training_load, sleep_hours, int(user_row['age']))
                st.write(f"Fatigue/Recovery score: {recov_score}")
                if st.button("Save recovery snapshot"):
                    append_history(username, {"bmi": user_row['bmi'], "vo2": user_row.get('vo2_est', np.nan), "pace_kmph": pace_from_time(test_dist, test_time), "training_load": training_load, "sleep_hours": sleep_hours, "recovery_score": recov_score})
                    st.success("Snapshot saved to history")
                    st.rerun()

        # Athletes dataset tab
        with tabs[2]:
            st.subheader("Active Athletes on Platform")
            all_users = load_users()
            # Filters
            fcol1, fcol2, fcol3 = st.columns([2,2,2])
            with fcol1:
                search_name = st.text_input("Search name (contains)")
            with fcol2:
                min_age, max_age = st.slider("Age range", 10, 100, (10,100))
            with fcol3:
                bmi_filter = st.selectbox("BMI category", options=["All","Underweight","Normal","Overweight","Obese"], index=1)

            filtered = all_users.copy()
            if search_name:
                filtered = filtered[filtered['name'].str.contains(search_name, case=False, na=False)]
            filtered = filtered[(filtered['age'] >= min_age) & (filtered['age'] <= max_age)]
            if bmi_filter != "All":
                filtered = filtered[filtered['bmi'].apply(lambda x: bmi_category(x) == bmi_filter)]

            st.dataframe(filtered.reset_index(drop=True))
            st.markdown("Export filtered data")
            csv = filtered.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", data=csv, file_name='filtered_athletes.csv')

        # Teams & Apply tab
        with tabs[3]:
            st.subheader("Teams & Applications")
            teams = load_teams()
            apps = load_applications()
            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.write("Available teams — select and apply")
                teams = teams.sort_values('team_id')
                teams['label'] = teams['team_id'].astype(str) + ' - ' + teams['team_name']
                team_map = dict(zip(teams['team_id'], teams['label']))
                selected = st.multiselect("Select team(s)", options=list(team_map.keys()), format_func=lambda x: team_map[x])
                if st.button("Apply to selected team(s)"):
                    if not selected:
                        st.warning("Select at least one team")
                    else:
                        for tid in selected:
                            apply_to_team(username, int(tid))
                        st.success("Applications submitted — pending admin review")
                        st.rerun()

                st.markdown("---")
                st.write("Team requirements & match scores")
                for _, row in teams.iterrows():
                    score = team_match_score(username, int(row['team_id']))
                    st.write(f"{int(row['team_id'])} — {row['team_name']}: {row['requirement']} — Match: {score}%")

            with col_right:
                st.write("Your applications and feedback")
                user_apps = apps[apps['username'] == username]
                if user_apps.empty:
                    st.info("No applications yet")
                else:
                    st.table(user_apps[['app_id','team_name','status','applied_at','admin_note']])

        # Advanced & Feedback tab
        with tabs[4]:
            st.subheader("Advanced Metrics & Admin Feedback")
            a1, a2 = st.columns(2)
            with a1:
                st.write("Example Advanced Metrics & Progress Charts")
                hist = load_history()
                user_hist = hist[hist['username'] == username].sort_values('timestamp')
                if user_hist.empty:
                    st.info("No history yet — save snapshots in Metrics tab to create charts.")
                else:
                    st.write("BMI over time")
                    fig1, ax1 = plt.subplots()
                    ax1.plot(pd.to_datetime(user_hist['timestamp']), user_hist['bmi'])
                    ax1.set_xlabel('Time')
                    ax1.set_ylabel('BMI')
                    ax1.set_title('BMI Progress')
                    st.pyplot(fig1)

                    st.write("VO2 over time")
                    fig2, ax2 = plt.subplots()
                    ax2.plot(pd.to_datetime(user_hist['timestamp']), user_hist['vo2'])
                    ax2.set_xlabel('Time')
                    ax2.set_ylabel('VO2 (ml/kg/min)')
                    ax2.set_title('VO2 Progress')
                    st.pyplot(fig2)

            with a2:
                st.write("Admin feedback / scout notes")
                apps = load_applications()
                notes = apps[(apps['username'] == username) & (apps['admin_note'].notnull()) & (apps['admin_note'] != "")]
                if notes.empty:
                    st.write("No feedback yet")
                else:
                    for _, r in notes.iterrows():
                        st.info(f"From Admin for {r['team_name']}: {r['admin_note']}")

# -------------------------
# ADMIN FLOW
# -------------------------
else:
    st.header("Admin Portal")
    if not st.session_state['admin_logged_in']:
        pwd = st.text_input("Admin password", type="password")
        if st.button("Login as Admin"):
            if pwd == ADMIN_PASSWORD:
                st.session_state['admin_logged_in'] = True
                st.success("Admin logged in")
                st.rerun()
            else:
                st.error("Incorrect password")
    else:
        st.header("Admin Dashboard")
        tabs = st.tabs(["Users DB","Teams DB","Manage","Requests","Analytics & Compare"])

        with tabs[0]:
            st.subheader("Users Database")
            u = load_users()
            st.dataframe(u)
            st.markdown("Download users CSV")
            st.download_button("Download users.csv", data=u.to_csv(index=False).encode('utf-8'), file_name='users.csv')

        with tabs[1]:
            st.subheader("Teams Database")
            t = load_teams()
            st.dataframe(t)
            st.markdown("Add a new team")
            t_name = st.text_input("Team name", key="new_team_name")
            t_req = st.text_area("Requirement / description", key="new_team_req")
            if st.button("Add Team"):
                if not t_name:
                    st.error("Please provide a team name")
                else:
                    ok = add_team(t_name, t_req)
                    if ok:
                        st.success("Team added")
                        st.rerun()
                    else:
                        st.error("Team already exists")

        with tabs[2]:
            st.subheader("Add / Delete Athletes & Teams")
            colA, colB = st.columns(2)
            with colA:
                st.write("Add Athlete")
                au_username = st.text_input("Username to add", key="admin_add_user_un")
                au_name = st.text_input("Full name", key="admin_add_user_name")
                au_age = st.number_input("Age", min_value=10, max_value=100, value=20, key="admin_add_user_age")
                au_w = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0, key="admin_add_user_w")
                au_h = st.number_input("Height (cm)", min_value=120.0, max_value=250.0, value=170.0, key="admin_add_user_h")
                if st.button("Add Athlete to DB"):
                    if not au_username:
                        st.error("Provide username")
                    else:
                        ok = add_user({"username": au_username, "name": au_name or au_username, "age": int(au_age),
                                       "weight_kg": float(au_w), "height_cm": float(au_h),
                                       "bmi": calculate_bmi(float(au_w), float(au_h)), "vo2_est": vo2_estimate(float(au_w), float(au_h), 10.0),
                                       "active": True, "created_at": datetime.now().isoformat()})
                        if ok:
                            st.success("Athlete added")
                            st.rerun()
                        else:
                            st.error("Username already exists")

            with colB:
                st.write("Delete Athlete")
                del_un = st.text_input("Username to delete", key="admin_del_un")
                if st.button("Delete Athlete"):
                    if not del_un:
                        st.error("Provide username")
                    else:
                        ok = delete_user(del_un)
                        if ok:
                            st.success("Deleted")
                            st.rerun()
                        else:
                            st.error("User not found")

            st.markdown("---")
            st.write("Delete Team")
            teams_list = load_teams()
            if teams_list.empty:
                st.info("No teams to manage")
            else:
                tid = st.selectbox("Select team id to delete", options=teams_list['team_id'].tolist(), key="admin_del_team")
                if st.button("Delete Team from DB"):
                    ok = delete_team(int(tid))
                    if ok:
                        st.success("Team deleted")
                        st.rerun()
                    else:
                        st.error("Failed to delete team")

        with tabs[3]:
            st.subheader("Applications / Requests")
            apps = load_applications()
            if apps.empty:
                st.info("No applications yet")
            else:
                st.dataframe(apps)
                st.markdown("Review application")
                aid = st.number_input("Application ID", min_value=1, value=int(apps['app_id'].min()), key="admin_aid")
                action = st.selectbox("Action", ["No action","Send to Team","Reject"], key="admin_action")
                note = st.text_area("Admin note (optional)", key="admin_note")
                if st.button("Apply action to application"):
                    if action == "Send to Team":
                        admin_send_to_team(int(aid), note)
                        st.success("Application forwarded to team (status updated)")
                        st.rerun()
                    elif action == "Reject":
                        admin_reject_application(int(aid), note)
                        st.success("Application rejected")
                        st.rerun()
                    else:
                        st.info("No action taken")

        with tabs[4]:
            st.subheader("Analytics & Compare")
            # Summary metrics
            users = load_users()
            st.metric("Active Athletes", len(users))
            st.metric("Teams", len(load_teams()))
            st.metric("Pending Applications", len(load_applications()[load_applications()['status']=='Pending']))

            st.markdown("---")
            st.write("Leaderboard & Trends")
            lb = admin_leaderboard(top_n=5)
            st.write("Top VO2")
            st.dataframe(lb['top_vo2'])
            st.write("Best Recovery (latest snapshots)")
            st.dataframe(lb['best_recovery'])

            st.markdown("---")
            st.write("Compare clients (select multiple)")
            opts = users['username'].tolist()
            picked = st.multiselect("Pick clients to compare", options=opts, key="admin_compare")
            if st.button("Compare selected"):
                comp = compare_clients(picked)
                if comp.empty:
                    st.info("No clients selected")
                else:
                    st.dataframe(comp)

        if st.button("Logout Admin"):
            st.session_state['admin_logged_in'] = False
            st.success("Admin logged out")
            st.rerun()

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.caption("Sports Connect v2.0 — charts, tracking, matching, and analytics added. Modify further for production.")
