import streamlit as st
import os
import base64
import time
import random
import pandas as pd
from pathlib import Path
from datetime import datetime
import git  # --- ADVANCED UPDATE: Needs 'GitPython' in requirements.txt ---

# --- NEW: RECOVERY LOGIC (PULL BEFORE START) ---
def pull_from_github():
    """Shutdown logic: Ensures local files match GitHub records on startup."""
    try:
        if "GITHUB_TOKEN" not in st.secrets:
            return False
        
        github_token = st.secrets["GITHUB_TOKEN"]
        repo_url = f"https://{github_token}@github.com/kobicdroid/ProjectSubmit.git"
        
        if os.path.exists(".git"):
            repo = git.Repo(os.getcwd())
            # Shutdown Update: Ensure the remote is always pointing to the right place with the token
            if 'origin' in [r.name for r in repo.remotes]:
                repo.remote('origin').set_url(repo_url)
            else:
                repo.create_remote('origin', repo_url)
            
            repo.remote(name='origin').pull()
            return True
        return False
    except Exception as e:
        log_security_event("Pull Error", str(e))
        return False

# --- CORE LOGIC FUNCTIONS (STRICTLY PRESERVED) ---

def push_to_github():
    """Advanced Logic: Pushes local changes back to your GitHub repository."""
    try:
        if "GITHUB_TOKEN" not in st.secrets:
            return False 
        
        github_token = st.secrets["GITHUB_TOKEN"]
        repo_url = f"https://{github_token}@github.com/kobicdroid/ProjectSubmit.git"
        
        if not os.path.exists(".git"):
            repo = git.Repo.init(os.getcwd())
        else:
            repo = git.Repo(os.getcwd())

        # Ensure origin is correctly configured
        if 'origin' not in [r.name for r in repo.remotes]:
            repo.create_remote('origin', repo_url)
        else:
            repo.remote('origin').set_url(repo_url)

        repo.git.add(all=True)
        # Shutdown Check: Only commit if there are changes to avoid errors
        if repo.is_dirty(untracked_files=True):
            repo.index.commit(f"New Submission Synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            repo.remote(name='origin').push()
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
        
        save_folder = Path("Results") / s_class
        save_folder.mkdir(parents=True, exist_ok=True)
        file_ext = uploaded_file.name.split('.')[-1]
        file_name = f"{name.replace(' ', '_')}_{serial}.{file_ext}"
        final_path = save_folder / file_name
        with open(final_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        push_to_github()
        return True
    except PermissionError:
        st.error("❌ Access Denied: Please close 'Project_Results.xlsx' and try again!")
        return False

# --- AUTO-SYNC ON STARTUP ---
if 'startup_synced' not in st.session_state:
    pull_from_github()
    st.session_state['startup_synced'] = True

# --- CONFIG & PASSWORDS ---
st.set_page_config(page_title="RSC Portal | Shutdown", page_icon="🎓", layout="wide")
SUPER_ADMIN_KEY = "SUMI"

CLASS_PASSWORDS = {
    "JSS 1": "JSS1 ACCESS", "JSS 2": "JSS2 ACCESS", "JSS 3": "JSS3 ACCESS",
    "SS 1": "SS1 ACCESS", "SS 2": "SS2 ACCESS", "SS 3": "SS3 ACCESS"
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

# --- ADMIN PAGE ---
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
                    df.columns = [str(c).strip() for c in df.columns]
                    st.dataframe(df, use_container_width=True)
                    
                    st.write("---")
                    st.subheader("👁️ Project Live Preview")
                    
                    name_col = next((c for c in df.columns if c.lower() == 'full name'), None)
                    adm_col = next((c for c in df.columns if c.lower() == 'admission no'), None)

                    if name_col and adm_col:
                        student_list = df[name_col].dropna().unique().tolist()
                        selected_student = st.selectbox("Select Student to Preview", options=student_list)
                        if selected_student:
                            student_data = df[df[name_col] == selected_student].iloc[0]
                            s_name = str(student_data[name_col]).replace(' ', '_')
                            s_adm = str(student_data[adm_col])
                            search_path = Path("Results") / sel_tab
                            found = list(search_path.glob(f"{s_name}_{s_adm}.*"))
                            if found:
                                file_path = found[0]
                                with open(file_path, "rb") as f:
                                    file_bytes = f.read()
                                if file_path.suffix.lower() == ".pdf":
                                    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
                                    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
                                    st.markdown(pdf_display, unsafe_allow_html=True)
                                    st.download_button("📂 View/Download Full PDF", file_bytes, file_name=file_path.name)
                                else:
                                    st.info("Download to view Word file.")
                                    st.download_button(f"📥 Download Project", file_bytes, file_name=file_path.name)
                            else:
                                st.warning("File not found.")

                    st.write("---")
                    st.download_button(f"📥 Export CSV", df.to_csv(index=False), file_name=f"{sel_tab}.csv")

    with tab2:
        if super_key == SUPER_ADMIN_KEY:
            st.subheader("🕵️ System Security Audit")
            
            st.markdown("### 🔄 Cloud Synchronization")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📥 RECOVER DATA FROM GITHUB"):
                    if pull_from_github():
                        st.success("Oshey! Data recovered.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Recovery failed. Check your GITHUB_TOKEN.")
            
            with col_b:
                if st.button("📤 PUSH LOCAL DATA TO CLOUD"):
                    if push_to_github():
                        st.success("Data backed up to GitHub!")
                    else:
                        st.error("Push failed.")

            st.write("---")
            if os.path.exists("security_audit.csv"):
                audit_df = pd.read_csv("security_audit.csv")
                st.dataframe(audit_df.sort_index(ascending=False), use_container_width=True)
            
            st.subheader("📤 Bulk Student Import")
            import_classes = ([f"JSS 1{c}" for c in "ABCDEFG"] + [f"JSS 2{c}" for c in "ABCDEF"] + [f"JSS 3{c}" for c in "ABCDEF"] + [f"SS 1{c}" for c in "ABCDEF"] + [f"SS 2{c}" for c in "ABCDEF"] + [f"SS 3{c}" for c in "ABC"])
            target_class = st.selectbox("Select Target Class", options=import_classes)
            import_file = st.file_uploader("Upload Completed List (CSV)", type=['csv'])
            if import_file and st.button("EXECUTE IMPORT"):
                try:
                    import_df = pd.read_csv(import_file)
                    if "Full Name" in import_df.columns and "Admission No" in import_df.columns:
                        excel_file = "Project_Results.xlsx"
                        import_df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        import_df["AI Score"] = "Pending"
                        mode = 'a' if os.path.exists(excel_file) else 'w'
                        with pd.ExcelWriter(excel_file, engine='openpyxl', mode=mode, if_sheet_exists='overlay') as writer:
                            import_df.to_excel(writer, sheet_name=target_class, index=False)
                        push_to_github() 
                        st.success(f"Imported and synced {len(import_df)} students.")
                except Exception as e:
                    st.error(f"Error: {e}")

            st.write("---")
            st.subheader("📥 Master Sheet Download")
            if os.path.exists("Project_Results.xlsx"):
                with open("Project_Results.xlsx", "rb") as f:
                    st.download_button("💾 Download Full Excel Database", f, file_name="RSC_Master_Results.xlsx")
        else:
            st.warning("🔒 Restricted: Enter the Master Audit Key to view tools.")

    if st.sidebar.button("🚪 Exit Admin Mode"):
        st.session_state['admin_mode'] = False
        st.rerun()

# --- STUDENT PAGES ---
def login_page():
    if st.sidebar.button("🔒 Staff Access"):
        st.session_state['admin_mode'] = True
        st.rerun()
    st.markdown("<h1 style='text-align: center; color: #2e7d32;'>RUBY SPRINGFIELD COLLEGE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: -15px;'><i>A Citadel of Supreme Excellence</i></p>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.write("---")
        with st.expander("🛡️ Submission Guide"):
            st.markdown("""
            **How to Submit Your Project:**
            1. **Enter Details**: Type your full name and admission number exactly as they appear on your ID.
            2. **Select Class**: Choose your correct arm (e.g., JSS 1A).
            3. **Upload File**: Select your PDF or Word document (Ensure it is not larger than 200MB).
            4. **Final Submission**: Click the button once and wait for the 'Success' message.
            """)
        name = st.text_input("Full Name", placeholder="Enter your full name")
        adm = st.text_input("Admission Number", placeholder="e.g. Class Serial No")
        classes = ([f"JSS 1{c}" for c in "ABCDEFG"] + [f"JSS 2{c}" for c in "ABCDEF"] + [f"JSS 3{c}" for c in "ABCDEF"] + [f"SS 1{c}" for c in "ABCDEF"] + [f"SS 2{c}" for c in "ABCDEF"] + [f"SS 3{c}" for c in "ABC"])
        sel_class = st.selectbox("Class", options=classes, index=None, placeholder="Choose class...")
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
        st.subheader("Submit Your Project")
        file = st.file_uploader("Upload Document (PDF/Docx)", type=['pdf', 'docx'])
        if file and st.button("FINAL SUBMISSION"):
            if save_submission_data(st.session_state['user'], st.session_state['serial_no'], st.session_state['class'], random.randint(7,10), file):
                st.success("✅ Submission Recorded & Saved to Cloud.")
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
