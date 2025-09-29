import streamlit as st
from utils import ensure_session_keys
from db import get_workouts

st.header("Workout History")
ensure_session_keys()

if st.session_state.get("user_id"):
    df = get_workouts(st.session_state.user_id)
    if not df.empty:
        # Format Success as ✅ / ❌ for readability
        df["Success"] = df["Success"].apply(lambda x: "✅" if x else "❌")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No workouts logged yet.")
else:
    st.warning("Please log in on the Home page first.")