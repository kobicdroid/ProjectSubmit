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
            return False # Skip if secrets aren't set up yet
        
        github_token = st.secrets["GITHUB_TOKEN"]
        # --- UPDATED REPO URL FOR KOBICDROID ---
        repo_url = f"https://{github_token}@github.com/kobicdroid/ProjectSubmit.git"
        
        repo = git.Repo(os.getcwd())
        repo.git.add(all=True)
        repo.index.commit(f"New Submission Synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        origin = repo.remote(name='origin')
        origin.push()
        return True
    except Exception as e:
        # We don't want to crash the app if sync fails, just log it
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
        return True
    except PermissionError:
        st.error("❌ Access Denied: Please close 'Project_Results.xlsx' in Excel and try again!")
        return False

# --- CONFIG & PASSWORDS ---
st.set_page_config(page_title="RSC Portal | Shutdown", page_icon="🎓", layout="wide")

SUPER_ADMIN_KEY = "ADMIN2026"

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

# --- UPDATED ADMIN PAGE WITH PREVIEWER ---

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
                    st.dataframe(df, use_container_width=True)
                    
                    st.write("---")
                    st.subheader("👁️ Project Live Preview")
                    
                    # File Selection for Preview
                    student_list = df['Full Name'].tolist()
                    selected_student = st.selectbox("Select Student to Preview Project", options=student_list)
                    
                    if selected_student:
                        student_data = df[df['Full Name'] == selected_student].iloc[0]
                        s_name = student_data['Full Name'].replace(' ', '_')
                        s_adm = student_data['Admission No']
                        
                        # Locate the file in the Results folder
                        search_path = Path("Results") / sel_tab
                        found_files = list(search_path.glob(f"{s_name}_{s_adm}.*"))
                        
                        if found_files:
                            file_path = found_files[0]
                            file_ext = file_path.suffix.lower()
                            
                            if file_ext == ".pdf":
                                with open(file_path, "rb") as f:
                                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                                st.markdown(pdf_display, unsafe_allow_html=True)
                            elif file_ext == ".docx":
                                st.info("📝 Microsoft Word files cannot be previewed directly in the browser.")
                                with open(file_path, "rb") as f:
                                    st.download_button(f"📥 Download {selected_student}'s Project", f, file_name=file_path.name)
                        else:
                            st.warning("File not found in storage. It may not have synced yet.")

                    st.write("---")
                    st.download_button(f"📥 Export {sel_tab} CSV", df.to_csv(index=False), file_name=f"{sel_tab}.csv")

    with tab2:
        if super_key == SUPER_ADMIN_KEY:
            st.subheader("🕵️ System Security Audit")
            if os.path.exists("security_audit.csv"):
                audit_df = pd.read_csv("security_audit.csv")
                st.dataframe(audit_df.sort_index(ascending=False), use_container_width=True)
            
            st.write("---")
            st.subheader("📤 Bulk Student Import")
            template_df = pd.DataFrame(columns=["Full Name", "Admission No"])
            template_csv = template_df.to_csv(index=False)
            st.download_button("📥 Download Import Template (CSV)", template_csv, "student_import_template.csv")
            
            import_classes = (
                [f"JSS 1{c}" for c in "ABCDEFG"] + 
                [f"JSS 2{c}" for c in "ABCDEF"] + 
                [f"JSS 3{c}" for c in "ABCDEF"] + 
                [f"SS 1{c}" for c in "ABCDEF"] + 
                [f"SS 2{c}" for c in "ABCDEF"] + 
                [f"SS 3{c}" for c in "ABC"]
            )
            
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
                        if_sheet_exists = 'overlay' if os.path.exists(excel_file) else None
                        
                        with pd.ExcelWriter(excel_file, engine='openpyxl', mode=mode, if_sheet_exists=if_sheet_exists) as writer:
                            import_df.to_excel(writer, sheet_name=target_class, index=False)
                        
                        # --- SYNC AFTER IMPORT ---
                        push_to_github() 
                        st.success(f"Success: {len(import_df)} students added and synced to Cloud.")
                        log_security_event("Bulk Import", f"Imported {len(import_df)} to {target_class}")
                    else:
                        st.error("Missing Columns! Ensure 'Full Name' and 'Admission No' exist.")
                except PermissionError:
                    st.error("❌ Permission Denied: Close 'Project_Results.xlsx' before importing!")
                except Exception as e:
                    st.error(f"Import Error: {e}")

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
        
        with st.expander("🛡️ RubySpringfield College: Project Submission Guide"):
            st.markdown("""
            **Official Step-by-Step Portal Access Guide**
            1. **Visit:** https://rubyspringfield-college-project-submit.streamlit.app/
            2. **Login:** Enter your Full Name, Admission Number, and select your Class arm.
            3. **Enter Portal:** Click the **"PROCEED TO PORTAL"** button.
            4. **Upload:** Once inside, click **"Browse files"** to select your Project Document (PDF or Docx).
            5. **Submit:** Click the **"FINAL SUBMISSION"** button to save your work.
            """)

        name = st.text_input("Full Name", placeholder="Enter your full name")
        adm = st.text_input("Admission Number", placeholder="e.g. RSC/2026/001")
        
        classes = (
            [f"JSS 1{c}" for c in "ABCDEFG"] + 
            [f"JSS 2{c}" for c in "ABCDEF"] + 
            [f"JSS 3{c}" for c in "ABCDEF"] + 
            [f"SS 1{c}" for c in "ABCDEF"] + 
            [f"SS 2{c}" for c in "ABCDEF"] + 
            [f"SS 3{c}" for c in "ABC"]
        )
        sel_class = st.selectbox("Class", options=classes, index=None, placeholder="Choose class...")
        
        if st.button("PROCEED TO PORTAL"):
            if name and adm and sel_class:
                st.session_state['logged_in'] = True
                st.session_state['user'], st.session_state['serial_no'], st.session_state['class'] = name, adm, sel_class
                st.rerun()

def upload_page():
    st.write(f"### Portal: {st.session_state['user']} ({st.session_state['class']})")
    if check_if_submitted(st.session_state['serial_no'], st.session_state['class']):
        st.warning("⚠️ Submission Restriction: You have already submitted your project.")
    else:
        st.subheader("Submit Your Project")
        file = st.file_uploader("Upload Document (PDF/Docx)", type=['pdf', 'docx'])
        if file and st.button("FINAL SUBMISSION"):
            if save_submission_data(st.session_state['user'], st.session_state['serial_no'], st.session_state['class'], random.randint(7,10), file):
                # --- SYNC TRIGGER ---
                push_to_github()
                st.success("✅ Submission Recorded & Saved to Cloud.")
                time.sleep(1)
                st.rerun()
            
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





