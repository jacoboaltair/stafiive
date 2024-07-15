import json

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from main import create_tree
from zingtree_final import run_script


def _max_width_():
    max_width_str = f"max-width: 1800px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_icon="✂️", page_title="Zoho to zingtree converter")
st.image(
    "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/apple/285/scissors_2702-fe0f.png",
    width=100,
)

st.title("Zoho to zingtree converter")

c29, c30, c31 = st.columns([1, 6, 1])

with c30:
    uploaded_file: list[UploadedFile] = st.file_uploader(
        "asdds",
        key="2",
        help="To activate 'wide mode', go to the hamburger menu > Settings > turn on 'wide mode'",
        accept_multiple_files=True
    )

    if len(uploaded_file) >= 1:
        files = {element.type: element for element in uploaded_file}

        # in intake form questionaire
        if 'text/csv' in files and False:
            file_container = st.expander("Check your uploaded .csv")

            result = create_tree(
                files.get('text/csv'),
                files.get('application/json')
            )
            href = st.download_button(data=json.dumps(result), file_name='zintree_form.json', label='Download')

        elif 'text/csv' in files:
            file_container = st.expander("Check your uploaded .csv")
            raw_data: UploadedFile = files.get('text/csv')
            result, file_name = run_script(raw_data.read())

            href = st.download_button(data=result, file_name=file_name, label='Download')

        else:
            st.info(
                f"""
                 Select a valid Json and CSV file
                """
            )
    else:
        st.info(
            f"""
                👆 Upload a .csv file first. Sample to try: [biostats.csv](https://people.sc.fsu.edu/~jburkardt/data/csv/biostats.csv)
                """
        )

        st.stop()
