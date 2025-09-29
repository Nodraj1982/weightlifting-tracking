import streamlit as st
import altair as alt
from utils import ensure_session_keys
from db import get_workouts

st.header("Workout History")
ensure_session_keys()

if st.session_state.get("user_id"):
    df = get_workouts(st.session_state.user_id)
    if not df.empty:
        # Format Success as ✅ / ❌ for readability
        df["Success"] = df["Success"].apply(lambda x: "✅" if x else "❌")

        # Compute training volume (sets × reps × weight)
        df["Volume"] = df["Sets"] * df["Achieved Reps"] * df["Weight"]

        st.subheader("Workout Log")
        st.dataframe(
            df[
                [
                    "Date",
                    "Exercise",
                    "Weight",
                    "Sets",
                    "Target Reps",
                    "Achieved Reps",
                    "Success",
                    "Scheme",
                    "Volume",
                ]
            ],
            use_container_width=True,
        )

        # --- Per-exercise summary ---
        st.subheader("Progression Summary")
        summary = (
            df.groupby(["Exercise", "Scheme"])
            .agg(
                Best_Weight=("Weight", "max"),
                Last_Weight=("Weight", "last"),
                Last_Success=("Success", "last"),
                Avg_Volume=("Volume", "mean"),
            )
            .reset_index()
        )
        st.dataframe(summary, use_container_width=True)

        # --- Visual progression ---
        st.subheader("Progression Charts")

        # Dropdown to pick an exercise
        exercise_list = df["Exercise"].unique().tolist()
        selected_ex = st.selectbox("Select Exercise", exercise_list)

        ex_df = df[df["Exercise"] == selected_ex]

        # Line chart of weight over time
        weight_chart = (
            alt.Chart(ex_df)
            .mark_line(point=True)
            .encode(
                x="Date:T",
                y="Weight:Q",
                color="Scheme:N",
                tooltip=[
                    "Date",
                    "Weight",
                    "Sets",
                    "Target Reps",
                    "Achieved Reps",
                    "Success",
                    "Scheme",
                ],
            )
            .properties(title=f"Weight Progression for {selected_ex}")
        )
        st.altair_chart(weight_chart, use_container_width=True)

        # Bar chart of achieved vs target reps
        reps_chart = (
            alt.Chart(ex_df)
            .mark_bar()
            .encode(
                x="Date:T",
                y="Achieved Reps:Q",
                color="Scheme:N",
                tooltip=["Date", "Sets", "Target Reps", "Achieved Reps", "Success"],
            )
            .properties(title=f"Reps Achieved vs Target for {selected_ex}")
        )
        target_line = (
            alt.Chart(ex_df)
            .mark_line(color="red", strokeDash=[4, 4])
            .encode(x="Date:T", y="Target Reps:Q")
        )
        st.altair_chart(reps_chart + target_line, use_container_width=True)

        # Line chart of training volume
        volume_chart = (
            alt.Chart(ex_df)
            .mark_line(point=True, color="green")
            .encode(
                x="Date:T",
                y="Volume:Q",
                tooltip=[
                    "Date",
                    "Weight",
                    "Sets",
                    "Achieved Reps",
                    "Volume",
                    "Scheme",
                ],
            )
            .properties(title=f"Training Volume for {selected_ex}")
        )
        st.altair_chart(volume_chart, use_container_width=True)

    else:
        st.info("No workouts logged yet.")
else:
    st.warning("Please log in on the Home page first.")