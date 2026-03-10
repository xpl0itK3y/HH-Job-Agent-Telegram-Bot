import streamlit as st


def dataframe_section(title: str, rows: list[dict]) -> None:
    st.markdown(f"#### {title}")
    if not rows:
        st.info("No data yet.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)
