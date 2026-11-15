"""MindEase Streamlit edition.

Runs alongside the existing Flask app and uses the same MongoDB database/collections.
The Flask app, templates, and Procfile are intentionally left untouched.
"""
import os
from datetime import datetime, date, timedelta
from collections import Counter

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import check_password_hash
from openai import OpenAI

load_dotenv()

st.set_page_config(page_title="MindEase", page_icon="🌿", layout="wide")

# Keep the familiar MindEase planner/dashboard palette.
GREEN = "#477b67"
GREEN_DARK = "#315e4d"
MINT = "#e9f3ed"
CREAM = "#faf8f2"
INK = "#263b32"
MUTED = "#728078"
LINE = "#e5eae4"
ROSE = "#f9e8e5"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; color: {INK}; }}
.stApp {{ background: linear-gradient(135deg,#edf4ed,#faf6ed); }}
[data-testid="stSidebar"] {{ background: #f7faf6; border-right:1px solid {LINE}; }}
h1,h2,h3 {{ color:{INK}; }}
div[data-testid="stMetric"] {{ background:white; border:1px solid {LINE}; padding:18px; border-radius:18px; }}
div.stButton > button, div.stFormSubmitButton > button {{ background:{GREEN}; color:white; border:0; border-radius:12px; font-weight:600; }}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {{ background:{GREEN_DARK}; color:white; }}
div[data-testid="stForm"] {{ background:white; border:1px solid {LINE}; padding:20px; border-radius:18px; }}
.mindease-hero {{ background:linear-gradient(120deg,#dceee1,#f5f1df); padding:26px 30px; border-radius:24px; margin-bottom:18px; }}
.mindease-card {{ background:white; border:1px solid {LINE}; border-radius:18px; padding:18px; margin-bottom:12px; }}
.small-muted {{ color:{MUTED}; font-size:13px; }}
.tag {{ display:inline-block; padding:5px 10px; background:{MINT}; border-radius:20px; color:{GREEN_DARK}; font-size:12px; }}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    # Streamlit Cloud stores app secrets in st.secrets; local development
    # can continue using the MONGO_URI variable from .env.
    uri = ""
    try:
        uri = str(st.secrets.get("MONGO_URI", "")).strip()
    except Exception:
        # st.secrets may be unavailable when running outside Streamlit Cloud.
        pass

    if not uri:
        uri = os.environ.get("MONGO_URI", "").strip()

    if not uri:
        return None

    client = MongoClient(uri, serverSelectionTimeoutMS=7000)
    client.admin.command("ping")
    return client["mindease"]

try:
    db = get_db()
except Exception as exc:
    db = None
    st.error("MindEase couldn't connect to MongoDB. Check the MONGO_URI setting.")
    st.caption(str(exc))

def logged_in():
    return bool(st.session_state.get("username"))

def page_header(title, subtitle=""):
    st.markdown(f'<div class="mindease-hero"><div style="color:{GREEN_DARK};font-size:12px;font-weight:700;letter-spacing:1.3px;">MINDEASE · YOUR SPACE</div><h1 style="margin:8px 0 4px;">{title}</h1><div style="color:#52685c;">{subtitle}</div></div>', unsafe_allow_html=True)

def login_page():
    page_header("A softer space to reset 🌿", "A little support for your mind, mood and studies.")
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Welcome back")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            user = db["users"].find_one({"username": username.strip()}) if db is not None else None
            valid = False
            if user:
                saved = str(user.get("password", ""))
                try:
                    valid = check_password_hash(saved, password)
                except (ValueError, TypeError):
                    valid = False
                # Compatibility with accounts created by the existing Flask app.
                valid = valid or saved == password
            if valid:
                st.session_state.username = username.strip()
                st.rerun()
            else:
                st.error("Those login details don't match.")
    with right:
        st.subheader("New to MindEase?")
        with st.form("signup_form"):
            new_user = st.text_input("Choose a username")
            new_pass = st.text_input("Create a password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            create = st.form_submit_button("Create account", use_container_width=True)
        if create:
            if db is None:
                st.error("MongoDB is not connected.")
            elif not new_user.strip() or len(new_user.strip()) > 40 or len(new_pass) < 6:
                st.warning("Enter a username (up to 40 characters) and a password of at least 6 characters.")
            elif new_pass != confirm:
                st.warning("The passwords do not match.")
            elif db["users"].find_one({"username": new_user.strip()}):
                st.warning("That username already exists.")
            else:
                # Keep the same account document shape so Flask can still read the account.
                db["users"].insert_one({"username":new_user.strip(),"password":new_pass,"login_count":0,"last_login":None,"created_at":datetime.now()})
                st.success("Account created. You can now log in from either version.")
    st.info("The Streamlit edition is running separately. Your existing Flask website remains unchanged.")

def sidebar():
    st.sidebar.markdown("## 🌿 MindEase")
    st.sidebar.caption("STUDENT WELLNESS")
    st.sidebar.write(f"Hello, **{st.session_state.username}**")
    options = ["Dashboard","Mood Tracker","My Journal","Insights","Study Planner","Study Session","Music Therapy","Breathing Space","Stress Buster","MindEase AI"]
    selected = st.sidebar.radio("YOUR SPACE", options, label_visibility="collapsed")
    st.sidebar.divider()
    if st.sidebar.button("Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    return selected

def dashboard():
    page_header("Your space to feel better", "Small steps count. Take today at your own pace.")
    username = st.session_state.username
    moods = list(db["moods"].find({"username":username}).sort("_id",-1).limit(7))
    tasks = list(db["study_tasks"].find({"username":username}))
    journals = db["journals"].count_documents({"username":username})
    done = sum(bool(t.get("completed")) for t in tasks)
    a,b,c,d = st.columns(4)
    a.metric("Moods tracked", db["moods"].count_documents({"username":username}))
    b.metric("Journal entries", journals)
    c.metric("Study tasks", len(tasks))
    d.metric("Tasks completed", done)
    st.subheader("A gentle check-in")
    if moods:
        latest=moods[0]
        st.success(f"Your latest mood was **{latest.get('mood','').title()}** · {latest.get('time','')}")
    else:
        st.info("You haven't logged a mood yet. Start with a quick check-in.")
    col1,col2,col3 = st.columns(3)
    with col1:
        st.markdown("### ♡ Mood Tracker")
        st.write("Pause and notice how you're feeling.")
    with col2:
        st.markdown("### ▦ Study Planner")
        st.write("Make a small, manageable plan.")
    with col3:
        st.markdown("### ✎ Journal")
        st.write("Give your thoughts a little space.")

def mood_tracker():
    page_header("How are you feeling today?", "No feeling is wrong. Choose the one that feels closest.")
    choices={"😊":"Happy","🥺":"Sad","😫":"Stressed","😡":"Angry","😌":"Calm"}
    cols=st.columns(len(choices))
    for (emoji,label),col in zip(choices.items(),cols):
        with col:
            st.markdown(f"<div class='mindease-card' style='text-align:center'><div style='font-size:40px'>{emoji}</div><b>{label}</b></div>",unsafe_allow_html=True)
            if st.button(f"Select {label}",key=f"mood_{label}",use_container_width=True):
                st.session_state.chosen_mood=label.lower()
    selected=st.session_state.get("chosen_mood")
    if selected:
        st.success(f"You selected **{selected.title()}**.")
        note=st.text_input("Anything you'd like to note? (optional)",key="mood_note")
        if st.button("Save my mood"):
            db["moods"].insert_one({"username":st.session_state.username,"mood":selected,"note":note,"time":datetime.now().strftime("%B %d, %Y - %I:%M %p"),"created_at":datetime.utcnow()})
            st.session_state.pop("chosen_mood",None)
            st.success("Your check-in has been saved.")
            st.rerun()

def journal_page():
    page_header("My Journal ✎", "A quiet place for your thoughts. Write as much or as little as you like.")
    with st.form("journal_entry"):
        title=st.text_input("Entry title")
        mood=st.selectbox("How did today feel?",["","happy","calm","sad","stressed","angry"])
        left=st.text_area("Page one · What's on your mind?",height=170)
        right=st.text_area("Page two · What would you like to remember?",height=170)
        save=st.form_submit_button("Save journal entry")
    if save:
        if not left.strip() and not right.strip():
            st.warning("Write a little something before saving.")
        else:
            now=datetime.utcnow()
            db["journals"].insert_one({"username":st.session_state.username,"title":title[:120],"mood":mood,"leftText":left,"rightText":right,"text":f"{left} | {right}","date":now.strftime("%B %d, %Y - %I:%M %p"),"created_at":now,"decorations":[]})
            st.success("Your entry is safely saved.")
    st.subheader("Past entries")
    entries=list(db["journals"].find({"username":st.session_state.username}).sort("_id",-1).limit(30))
    if not entries:
        st.caption("Your saved entries will appear here.")
    for entry in entries:
        label=entry.get("title") or entry.get("date") or "Journal entry"
        with st.expander(f"📖 {label}"):
            st.caption(entry.get("date",""))
            if entry.get("mood"): st.markdown(f"**Mood:** {entry['mood'].title()}")
            st.write(entry.get("leftText") or entry.get("text",""))
            if entry.get("rightText"): st.write(entry["rightText"])

def insights_page():
    page_header("Your Journey 📊", "A gentle summary of your wellness progress.")
    username=st.session_state.username
    moods=list(db["moods"].find({"username":username}).sort("_id",-1).limit(7))
    journals=list(db["journals"].find({"username":username}).sort("_id",-1).limit(20))
    counts=Counter(x.get("mood","") for x in moods if x.get("mood"))
    common=counts.most_common(1)[0][0].title() if counts else "No mood data yet"
    a,b,c=st.columns(3)
    a.metric("Moods tracked",db["moods"].count_documents({"username":username}))
    b.metric("Journals written",db["journals"].count_documents({"username":username}))
    c.metric("Most frequent recent mood",common)
    st.subheader("Recent mood check-ins")
    if moods:
        st.dataframe([{"Mood":m.get("mood","").title(),"When":m.get("time","")} for m in moods],use_container_width=True,hide_index=True)
    else: st.info("Your mood check-ins will appear here.")
    st.subheader("Recent journal activity")
    for entry in journals:
        st.markdown(f"<div class='mindease-card'><b>{entry.get('title') or 'Journal entry'}</b><div class='small-muted'>{entry.get('date','')}</div><p>{(entry.get('text') or entry.get('leftText',''))[:180]}</p></div>",unsafe_allow_html=True)

def study_planner():
    page_header("Your Study Planner", "A little structure, with room to breathe.")
    username=st.session_state.username
    tasks=list(db["study_tasks"].find({"username":username}).sort([("completed",1),("due_date",1),("created_at",-1)]))
    today=date.today().isoformat()
    total=len(tasks); completed=sum(bool(t.get("completed")) for t in tasks)
    overdue=sum(1 for t in tasks if not t.get("completed") and t.get("due_date") and t["due_date"]<today)
    a,b,c,d=st.columns(4)
    a.metric("All tasks",total); b.metric("In progress",total-completed); c.metric("Completed",completed); d.metric("Overdue",overdue)
    st.subheader("Your week at a glance")
    chosen=st.date_input("Choose a day",value=date.today())
    day_tasks=[t for t in tasks if t.get("due_date")==chosen.isoformat()]
    if day_tasks:
        for t in day_tasks: st.write(f"• {t.get('study_time') or 'Any time'} — {t.get('title')}")
    else: st.info("No tasks planned for this day.")
    left,right=st.columns([1,1.8])
    with left:
        st.subheader("＋ Add a study task")
        with st.form("add_task"):
            title=st.text_input("Task title *")
            subject=st.text_input("Subject")
            due=st.date_input("Due date",value=None)
            study_time=st.text_input("Study time (optional)",placeholder="e.g. 5:00 PM")
            task_type=st.selectbox("Task type",["assignment","exam","revision","project","other"])
            priority=st.selectbox("Priority",["low","medium","high"],index=1)
            minutes=st.number_input("Estimated minutes",min_value=5,max_value=600,value=30,step=5)
            add=st.form_submit_button("Add task",use_container_width=True)
        if add:
            if not title.strip(): st.error("Please enter a task title.")
            else:
                db["study_tasks"].insert_one({"username":username,"title":title.strip()[:120],"subject":subject.strip()[:80],"due_date":due.isoformat() if due else "","study_time":study_time.strip(),"priority":priority,"task_type":task_type,"estimated_minutes":int(minutes),"completed":False,"created_at":datetime.utcnow()})
                st.success("Task added to your planner.")
                st.rerun()
    with right:
        st.subheader("My study tasks")
        filter_by=st.selectbox("Filter tasks",["all","pending","completed","overdue"])
        visible=tasks
        if filter_by=="pending": visible=[t for t in tasks if not t.get("completed")]
        elif filter_by=="completed": visible=[t for t in tasks if t.get("completed")]
        elif filter_by=="overdue": visible=[t for t in tasks if not t.get("completed") and t.get("due_date") and t["due_date"]<today]
        if not visible: st.info("No tasks in this view yet.")
        for task in visible:
            oid=str(task["_id"])
            with st.container(border=True):
                st.markdown(("~~"+task.get("title","")+"~~") if task.get("completed") else f"**{task.get('title','')}**")
                st.caption(f"{task.get('subject') or 'No subject'} · {task.get('task_type','').title()} · {task.get('priority','medium').title()} priority · {task.get('estimated_minutes',30)} min")
                st.caption(f"Due: {task.get('due_date') or 'No due date'}")
                x,y=st.columns(2)
                with x:
                    if st.button("Mark pending" if task.get("completed") else "Complete",key=f"toggle_{oid}",use_container_width=True):
                        db["study_tasks"].update_one({"_id":task["_id"],"username":username},{"$set":{"completed":not task.get("completed",False)}})
                        st.rerun()
                with y:
                    if st.button("Delete",key=f"delete_{oid}",use_container_width=True):
                        db["study_tasks"].delete_one({"_id":task["_id"],"username":username})
                        st.rerun()

def study_session_page():
    page_header("Study & Reflect", "Focus gently, then check in with yourself.")
    username=st.session_state.username
    tasks=list(db["study_tasks"].find({"username":username}).sort("due_date",1))
    with st.form("start_study"):
        task_options={"Independent study":""}
        task_options.update({f"{t.get('title','Task')} · {t.get('due_date') or 'No due date'}":str(t["_id"]) for t in tasks})
        task_label=st.selectbox("What will you work on?",list(task_options))
        stress_before=st.slider("How stressed do you feel right now?",1,10,5)
        duration=st.select_slider("Focus duration",options=[15,25,45,60],value=25)
        start=st.form_submit_button("Start a study session")
    if start:
        now=datetime.utcnow()
        res=db["study_sessions"].insert_one({"username":username,"task_id":task_options[task_label] or None,"task_title":task_label.split(" · ")[0],"duration_minutes":int(duration),"stress_before":int(stress_before),"stress_after":None,"reflection":"","started_at":now,"finished_at":None,"completed":False})
        st.session_state.active_study_session=str(res.inserted_id)
        st.success("Session started. Keep this page open and use your own timer.")
    active_id=st.session_state.get("active_study_session")
    active=db["study_sessions"].find_one({"_id":ObjectId(active_id),"username":username,"completed":False}) if active_id else None
    if active:
        st.info(f"Current focus: **{active.get('task_title')}** · {active.get('duration_minutes')} minutes")
        st.write("When your focus time is over, finish your session and reflect.")
        with st.form("finish_study"):
            after=st.slider("How stressed do you feel now?",1,10,4)
            reflection=st.text_area("A small reflection (optional)",max_chars=500)
            finish=st.form_submit_button("Finish session")
        if finish:
            db["study_sessions"].update_one({"_id":active["_id"],"username":username},{"$set":{"stress_after":int(after),"reflection":reflection,"finished_at":datetime.utcnow(),"completed":True}})
            if active.get("task_id"):
                try: db["study_tasks"].update_one({"_id":ObjectId(active["task_id"]),"username":username},{"$set":{"last_study_session":datetime.utcnow()}})
                except Exception: pass
            st.session_state.pop("active_study_session",None)
            st.success("Session saved. Well done for showing up.")
            st.rerun()
    st.subheader("Recent sessions")
    history=list(db["study_sessions"].find({"username":username,"completed":True}).sort("finished_at",-1).limit(20))
    if not history: st.caption("Completed study sessions will appear here.")
    for item in history:
        st.markdown(f"<div class='mindease-card'><b>{item.get('task_title','Study session')}</b><div class='small-muted'>{item.get('duration_minutes')} min · Stress: {item.get('stress_before')} → {item.get('stress_after')}</div><p>{item.get('reflection','')}</p></div>",unsafe_allow_html=True)

def music_page():
    page_header("Music Therapy 🎵", "Choose a mood and open a playlist that suits the moment.")
    playlists={
      "happy":{"English":"0jrlHA5UmxRxJjoykf7qRY","Hindi":"37i9dQZF1DWTwbZHrJRIgD","Punjabi":"0xawH3WmFz4PdLGYYn3gpT","South Indian":"0dPzC4kI939RwZFiMHHDHl"},
      "sad":{"English Mood Booster":"37i9dQZF1DX3rxVfibe1L0","Hindi Mood Booster":"37i9dQZF1DX5q67ZpWyRrZ","South Indian Feel Good":"3NF0iDKGPhSfB5tfRpkVlQ"},
      "stressed":{"Nature Sounds":"37i9dQZF1DX4PP3DA4J0N8","Relaxation":"37i9dQZF1DXebxttQCq0zA","Devotional":"7gFVfcFKRzeOH1cfhVdj0A","Instrumental":"37i9dQZF1DX4sWSpwq3LiO"},
      "angry":{"Calm Down":"37i9dQZF1DWU0ScTcjJBdj","Lo-fi":"37i9dQZF1DWYoYGBbGKurt","Meditation":"37i9dQZF1DWZqd5JICZI0u"}}
    mood=st.selectbox("Choose your current mood",list(playlists))
    for label,pid in playlists[mood].items():
        st.markdown(f"**{label}**")
        st.components.v1.iframe(f"https://open.spotify.com/embed/playlist/{pid}",height=152,scrolling=False)

def breathing_page():
    page_header("Let's take a breath.", "Relax your shoulders. Breathe gently, and follow a comfortable pace.")
    st.markdown("<div class='mindease-card' style='text-align:center'><div style='font-size:48px'>🌿</div><h2>Inhale · 4 sec &nbsp; Hold · 2 sec &nbsp; Exhale · 6 sec</h2><p>Repeat gently for a few minutes. If holding your breath feels uncomfortable, skip the hold and breathe normally.</p></div>",unsafe_allow_html=True)
    st.info("Try this simple cycle: breathe in for 4 seconds, pause for 2, then breathe out slowly for 6. Stop if you feel dizzy or uncomfortable.")

def stress_buster_page():
    page_header("Your little stress break 🫧", "Take a breath, pause for a moment, and give yourself permission to reset.")
    st.write("A tiny reset: unclench your jaw, relax your shoulders, and take three comfortable breaths.")
    if "bubble_score" not in st.session_state: st.session_state.bubble_score=0
    a,b=st.columns(2)
    a.metric("Bubbles popped",st.session_state.bubble_score)
    if b.button("Reset score"): st.session_state.bubble_score=0; st.rerun()
    st.caption("A simple mindful interaction for this first Streamlit version.")
    cols=st.columns(5)
    for i,col in enumerate(cols):
        with col:
            if st.button("🫧",key=f"bubble_{i}"):
                st.session_state.bubble_score+=1
                st.rerun()

def ai_page():
    page_header("MindEase AI", "A calm companion for everyday study stress and reflection.")
    api_key=os.environ.get("OPENAI_API_KEY","").strip()
    if not api_key:
        st.warning("AI chat needs OPENAI_API_KEY configured in the Streamlit service environment.")
        return
    if "chat_history" not in st.session_state: st.session_state.chat_history=[]
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]): st.write(item["content"])
    prompt=st.chat_input("What's on your mind?")
    if prompt:
        st.session_state.chat_history.append({"role":"user","content":prompt})
        with st.chat_message("user"): st.write(prompt)
        try:
            client=OpenAI(api_key=api_key)
            system=("You are MindEase AI, a kind and concise student-wellbeing companion. Offer practical support for everyday study stress and reflection. You are not a therapist or emergency service. Do not diagnose or prescribe. If someone is in immediate danger, encourage contacting local emergency services and a trusted person nearby.")
            messages=[{"role":"system","content":system}]+st.session_state.chat_history[-12:]
            response=client.chat.completions.create(model=os.environ.get("OPENAI_MODEL","gpt-4o-mini"),messages=messages,max_tokens=450,temperature=.7)
            answer=(response.choices[0].message.content or "").strip()
            st.session_state.chat_history.append({"role":"assistant","content":answer})
            with st.chat_message("assistant"): st.write(answer)
        except Exception:
            st.error("MindEase AI is temporarily unavailable. Check the API key and account API credits.")

if db is None:
    st.title("🌿 MindEase")
    st.warning("Add MONGO_URI to your local .env file or Streamlit service environment to continue.")
elif not logged_in():
    login_page()
else:
    selected=sidebar()
    routes={"Dashboard":dashboard,"Mood Tracker":mood_tracker,"My Journal":journal_page,"Insights":insights_page,"Study Planner":study_planner,"Study Session":study_session_page,"Music Therapy":music_page,"Breathing Space":breathing_page,"Stress Buster":stress_buster_page,"MindEase AI":ai_page}
    routes[selected]()
