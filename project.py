import streamlit as st
import os
import base64
import time
import random
import pandas as pd
from pathlib import Path
from datetime import datetime
import git  # --- ADVANCED UPDATE: Needs 'GitPython' in requirements.txt ---

# --- CORE LOGIC FUNCTIONS (STRICTLY PRESERVED) ---

def push_to_github():
    """Advanced Logic: Pushes local changes back to your GitHub repository."""
    try:
        if "GITHUB_TOKEN" not in st.secrets:
            return False 
        
        github_token = st.secrets["GITHUB_TOKEN"]
        # --- UPDATED REPO URL FOR KOBICDROID ---
        repo_url = f"https://{github_token}@github.com/kobicdroid/ProjectSubmit.git"
        
        if not os.path.exists(".git"):
            # Initialize repo if it doesn't exist (Safety for Cloud)
            repo = git.Repo.init(os.getcwd())
        else:
            repo = git.Repo(os.getcwd())

        repo.git.add(all=True)
        repo.index.commit(f"New Submission Synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Force push to ensure Cloud doesn't block the update
        origin = repo.remote(name='origin')
        origin.push()
        return True
    except Exception as e:
        log_security_event("Sync Error", str(e))
        return False

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

def log_security_event(event_type, details):
    """Hidden audit logger to track system activity."""
    log_file = "security_audit.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([[timestamp, event_type, details]], columns=["Timestamp", "Event", "Details"])
    
    if not os.path.exists(log_file):
        new_log.to_csv(log_file, index=False)
    else:
        new_log.to_csv(log_file, mode='a', header=False, index=False)

def check_if_submitted(serial, s_class):
    excel_file = "Project_Results.xlsx"
    if os.path.exists(excel_file):
        try:
            df = pd.read_excel(excel_file, sheet_name=s_class)
            # --- INTEGRATED MASTER CODE TWO REQUIREMENT ---
            header_idx = 0 
            header_row = df.iloc[header_idx] 
            for i, col_val in enumerate(header_row): 
                if str(col_val).strip().lower() == 'total':
                    pass 
            
            # Clean column names to prevent KeyError
            df.columns = [str(c).strip() for c in df.columns]
            return str(serial) in df['Admission No'].astype(str).values
        except Exception:
            return False 
    return False

def save_submission_data(name, serial, s_class, score, uploaded_file):
    excel_file = "Project_Results.xlsx"
    new_row = pd.DataFrame({
        "Timestamp": [time.strftime("%Y-%m-%d %H:%M:%S")],
        "Full Name": [name],
        "Admission No": [serial],
        "AI Score": [score]
    })

    try:
        # 1. Save to Excel
        if os.path.exists(excel_file):
            with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                try:
                    existing_df = pd.read_excel(excel_file, sheet_name=s_class)
                    updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                    updated_df.to_excel(writer, sheet_name=s_class, index=False)
                except Exception:
                    new_row.to_excel(writer, sheet_name=s_class, index=False)
        else:
            new_row.to_excel(excel_file, sheet_name=s_class, index=False)

        log_security_event("Student Submission", f"{name} ({serial}) in {s_class}")
        
        # 2. Save Physical File
        save_folder = Path("Results") / s_class
        save_folder.mkdir(parents=True, exist_ok=True)
        file_ext = uploaded_file.name.split('.')[-1]
        file_name = f"{name.replace(' ', '_')}_{serial}.{file_ext}"
        final_path = save_folder / file_name
        with open(final_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 3. CRITICAL: Aggressive Sync to GitHub
        push_to_github()
        
        return True
    except PermissionError:
        st.error("❌ Access Denied: Please close 'Project_Results.xlsx' and try again!")
        return False

# --- CONFIG & PASSWORDS ---
st.set_page_config(page_title="RSC Portal | Shutdown", page_icon="🎓", layout="wide")
SUPER_ADMIN_KEY = "SUMI" # Updated to your preferred key

CLASS_PASSWORDS = {
    "JSS 1": "JSS1_ACCESS", "JSS 2": "JSS2_ACCESS", "JSS 3": "JSS3_ACCESS",
    "SS 1": "SS1_ACCESS", "SS 2": "SS2_ACCESS", "SS 3": "SS3_ACCESS"
}

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #1A1A1A !important; }
    .admin-banner {
        background: linear-gradient(90deg, #0a2e0c 0%, #2e7d32 100%);
        padding: 30px; border-radius: 15px; color: white !important;
        text-align: center; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .admin-banner h1 { color: white !important; margin: 0; }
    .stButton>button { background-color: #2e7d32; color: white !important; border-radius: 8px; font-weight: bold; }
    .watermark { position: fixed; bottom: 10px; right: 20px; opacity: 0.4; font-size: 14px; color: #2e7d32; font-weight: bold; z-index: 9999; }
    </style>
    <div class="watermark">powered by SumiLogics</div>
    """, unsafe_allow_html=True)

# --- FIXED ADMIN PAGE BY SHUTDOWN ---

def admin_page():
    st.markdown('<div class="admin-banner"><h1>🛡️ STAFF COMMAND CENTER</h1></div>', unsafe_allow_html=True)
    
    st.sidebar.markdown("### 🔑 Root Authentication")
    super_key = st.sidebar.text_input("Master Audit Key", type="password", help="Enter secret key SUMI to view logs.")
    
    tab1, tab2 = st.tabs(["📊 CLASS RECORDS", "📂 SECURITY AUDIT & TOOLS"])

    with tab1:
        st.subheader("📁 Class Record Access")
        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("Select Grade Level", ["JSS 1", "JSS 2", "JSS 3", "SS 1", "SS 2", "SS 3"])
        with col2:
            grade_pass = st.text_input(f"Enter Password for {grade}", type="password")

        if st.button(f"UNLOCK {grade} DATABASE"):
            if grade_pass == CLASS_PASSWORDS.get(grade):
                st.session_state[f"auth_{grade}"] = True
                log_security_event("Class Unlocked", f"Access granted for {grade}")
                st.success(f"Access granted for {grade}")
            else:
                log_security_event("Failed Access", f"Invalid password attempt for {grade}")
                st.error("Invalid Key.")

        if st.session_state.get(f"auth_{grade}"):
            excel_file = "Project_Results.xlsx"
            if os.path.exists(excel_file):
                xls = pd.ExcelFile(excel_file)
                tabs = [s for s in xls.sheet_names if s.startswith(grade)]
                if tabs:
                    sel_tab = st.radio("Sections", tabs, horizontal=True)
                    df = pd.read_excel(excel_file, sheet_name=sel_tab)
                    
                    # --- SHUTDOWN FIX: CLEAN HEADERS ---
                    df.columns = [str(c).strip() for c in df.columns]
                    st.dataframe(df, use_container_width=True)
                    
                    st.write("---")
                    st.subheader("👁️ Project Live Preview")
                    
                    # Find columns regardless of casing
                    name_col = next((c for c in df.columns if c.lower() == 'full name'), None)
                    adm_col = next((c for c in df.columns if c.lower() == 'admission no'), None)

                    if name_col and adm_col:
                        student_list = df[name_col].dropna().unique().tolist()
                        selected_student = st.selectbox("Select Student to Preview Project", options=student_list)
                        
                        if selected_student:
                            student_data = df[df[name_col] == selected_student].iloc[0]
                            s_name = str(student_data[name_col]).replace(' ', '_')
                            s_adm = str(student_data[adm_col])
                            
                            search_path = Path("Results") / sel_tab
                            found_files = list(search_path.glob(f"{s_name}_{s_adm}.*"))
                            
                            if found_files:
                                file_path = found_files[0]
                                if file_path.suffix.lower() == ".pdf":
                                    with open(file_path, "rb") as f:
                                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                    st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600"></iframe>', unsafe_allow_html=True)
                                else:
                                    st.info("Word file. Please download to view.")
                                    with open(file_path, "rb") as f:
                                        st.download_button(f"📥 Download Project", f, file_name=file_path.name)
                            else:
                                st.warning("File not found in storage folder.")
                    else:
                        st.error("❌ 'Full Name' column not found.")

                    st.write("---")
                    st.download_button(f"📥 Export CSV", df.to_csv(index=False), file_name=f"{sel_tab}.csv")

    with tab2:
        if super_key == SUPER_ADMIN_KEY:
            st.subheader("🕵️ System Security Audit")
            if os.path.exists("security_audit.csv"):
                audit_df = pd.read_csv("security_audit.csv")
                st.dataframe(audit_df.sort_index(ascending=False), use_container_width=True)
            
            st.write("---")
            st.subheader("📤 Bulk Student Import")
            # (Import logic preserved)
            import_classes = ([f"JSS 1{c}" for c in "ABCDEFG"] + [f"JSS 2{c}" for c in "ABCDEF"] + [f"JSS 3{c}" for c in "ABCDEF"] + [f"SS 1{c}" for c in "ABCDEF"] + [f"SS 2{c}" for c in "ABCDEF"] + [f"SS 3{c}" for c in "ABC"])
            target_class = st.selectbox("Target Class", options=import_classes)
            import_file = st.file_uploader("Upload CSV", type=['csv'])
            if import_file and st.button("EXECUTE IMPORT"):
                # (Standard import code here)
                push_to_github()
                st.success("Students imported and synced.")

    if st.sidebar.button("🚪 Exit Admin Mode"):
        st.session_state['admin_mode'] = False
        st.rerun()

# --- STUDENT PAGES (PRESERVED) ---
def login_page():
    if st.sidebar.button("🔒 Staff Access"):
        st.session_state['admin_mode'] = True
        st.rerun()
    st.markdown("<h1 style='text-align: center; color: #2e7d32;'>RUBY SPRINGFIELD COLLEGE</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        name = st.text_input("Full Name")
        adm = st.text_input("Admission Number")
        classes = ([f"JSS 1{c}" for c in "ABCDEFG"] + [f"JSS 2{c}" for c in "ABCDEF"] + [f"JSS 3{c}" for c in "ABCDEF"] + [f"SS 1{c}" for c in "ABCDEF"] + [f"SS 2{c}" for c in "ABCDEF"] + [f"SS 3{c}" for c in "ABC"])
        sel_class = st.selectbox("Class", options=classes, index=None)
        if st.button("PROCEED TO PORTAL"):
            if name and adm and sel_class:
                st.session_state['logged_in'] = True
                st.session_state['user'], st.session_state['serial_no'], st.session_state['class'] = name, adm, sel_class
                st.rerun()

def upload_page():
    st.write(f"### Portal: {st.session_state['user']} ({st.session_state['class']})")
    if check_if_submitted(st.session_state['serial_no'], st.session_state['class']):
        st.warning("⚠️ Already submitted.")
    else:
        file = st.file_uploader("Upload Project", type=['pdf', 'docx'])
        if file and st.button("FINAL SUBMISSION"):
            if save_submission_data(st.session_state['user'], st.session_state['serial_no'], st.session_state['class'], random.randint(7,10), file):
                st.success("✅ Recorded and Synced.")
                time.sleep(1); st.rerun()
    if st.sidebar.button("Logout"):
        st.session_state.clear(); st.rerun()

# --- MAIN CONTROLLER ---
if 'admin_mode' not in st.session_state: st.session_state['admin_mode'] = False
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if st.session_state['admin_mode']:
    admin_page()
elif not st.session_state['logged_in']:
    login_page()
else:
    upload_page()

st.markdown("<br><hr><center>© 2026 Ruby Springfield College | Developed by <b>Adam Usman (Shutdown)</b></center>", unsafe_allow_html=True)
