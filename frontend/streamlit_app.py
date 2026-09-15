import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="AI Document Intelligence", layout="wide")
st.title("AI Document Intelligence & Editor")
st.caption("Evidence-grounded document analysis with reviewable AI edits")

with st.sidebar:
    st.header("Document Library")
    uploaded = st.file_uploader("Upload PDF, DOCX, TXT, or Markdown", type=["pdf", "docx", "txt", "md"])
    if uploaded and st.button("Upload"):
        response = requests.post(f"{API_URL}/api/v1/documents/upload", files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)})
        st.session_state["message"] = response.json() if response.ok else response.text
    documents_response = requests.get(f"{API_URL}/api/v1/documents")
    documents = documents_response.json() if documents_response.ok else []
    selected = st.selectbox("Select document", documents, format_func=lambda d: d["title"]) if documents else None

if st.session_state.get("message"):
    st.success(str(st.session_state.pop("message")))

if selected:
    document_id = selected["id"]
    detail = requests.get(f"{API_URL}/api/v1/documents/{document_id}").json()
    tabs = st.tabs(["Editor", "Analysis", "Ask", "Versions"])
    with tabs[0]:
        content = st.text_area("Document content", detail["content"], height=420)
        if st.button("Save version"):
            st.success(requests.post(f"{API_URL}/api/v1/documents/{document_id}/versions", json={"content": content, "change_summary": "Saved from editor"}).json())
        selected_text = st.text_area("Text for AI suggestion", height=100)
        operation = st.selectbox("Operation", ["professional", "improve", "shorten", "expand", "bullets", "summarize", "heading", "explain"])
        if st.button("Generate suggestion"):
            st.session_state["suggestion"] = requests.post(f"{API_URL}/api/v1/documents/{document_id}/edit", json={"text": selected_text, "operation": operation}).json()
        if st.session_state.get("suggestion"):
            st.json(st.session_state["suggestion"])
    with tabs[1]:
        if st.button("Run analysis"):
            st.session_state["analysis"] = requests.post(f"{API_URL}/api/v1/documents/{document_id}/analyze").json()
        analysis = st.session_state.get("analysis")
        if analysis:
            st.subheader("Executive summary")
            st.write(analysis["executive_summary"])
            for label in ["key_points", "decisions", "action_items", "risks", "missing_information", "contradictions"]:
                st.subheader(label.replace("_", " ").title())
                st.json(analysis[label])
    with tabs[2]:
        question = st.text_input("Ask a question about this document")
        if question and st.button("Ask"):
            st.json(requests.post(f"{API_URL}/api/v1/documents/{document_id}/ask", json={"question": question}).json())
    with tabs[3]:
        st.json(requests.get(f"{API_URL}/api/v1/documents/{document_id}/versions").json())
