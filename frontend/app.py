import streamlit as st
import requests
import json
import time

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AWS Doc Agent", page_icon="🤖", layout="wide")

st.title("AWS Doc Agent 🤖")

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")
    if "api_url" not in st.session_state:
        st.session_state.api_url = API_URL
    
    api_url_input = st.text_input("API URL", value=st.session_state.api_url)
    if api_url_input != st.session_state.api_url:
        st.session_state.api_url = api_url_input

# --- Helper Functions ---
def get_services():
    try:
        response = requests.get(f"{st.session_state.api_url}/services")
        if response.status_code == 200:
            return response.json().get("services", [])
        else:
            st.error(f"Failed to fetch services: {response.text}")
            return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []

def scrape_service(service_name, limit=None):
    payload = {"services": [service_name], "limit": limit}
    try:
        response = requests.post(f"{st.session_state.api_url}/scrape", json=payload)
        return response
    except Exception as e:
        return e

def clear_chat_history():
    st.session_state.messages = []

# --- UI Layout ---
tab_chat, tab_agent, tab_kb = st.tabs(["💬 Chat (RAG)", "🕵️ Agent Search", "📚 Knowledge Base"])

# --- Tab 2: Agent Search ---
with tab_agent:
    st.header("Agentic Search")
    st.info("The Agent can explore multiple services and aggregate information. It shows its reasoning steps.")
    
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = []

    # Display chat
    for message in st.session_state.agent_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "reasoning" in message and message["reasoning"]:
                with st.expander("Reasoning Steps", expanded=False):
                    for step in message["reasoning"]:
                        st.markdown(step)

    if query := st.chat_input("Find info about S3 and Lambda integration", key="agent_input"):
        st.session_state.agent_messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            reasoning_steps = []
            full_response = ""
            
            # Status container for live reasoning
            status_container = st.status("Thinking...", expanded=True)
            
            try:
                payload = {"query": query, "stream": True}
                with requests.post(f"{st.session_state.api_url}/agent", json=payload, stream=True) as response:
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line:
                                try:
                                    event = json.loads(line.decode("utf-8"))
                                    
                                    if event["type"] == "thought":
                                        content = event["content"]
                                        reasoning_steps.append(content)
                                        status_container.markdown(content)
                                        
                                    elif event["type"] == "answer":
                                        full_response += event["content"]
                                        message_placeholder.markdown(full_response + "▌")
                                        
                                except Exception as e:
                                    print(f"Error parsing line: {e}")
                        
                        message_placeholder.markdown(full_response)
                        status_container.update(label="Finished", state="complete", expanded=False)
                    else:
                         st.error(f"API Error: {response.status_code}")
                         full_response = "Error."
                         
            except Exception as e:
                 st.error(f"Error: {e}")
                 full_response = f"Error: {e}"
                 status_container.update(label="Error", state="error")
                 
            st.session_state.agent_messages.append({
                "role": "assistant", 
                "content": full_response,
                "reasoning": reasoning_steps
            })
            st.rerun()

# --- Tab 1: Chat ---
with tab_chat:
    st.header("Ask about AWS Services")
    
    # Service Selection
    params = st.query_params
    default_index = 0
    services = get_services()
    
    selected_service = st.selectbox(
        "Select AWS Service context:",
        options=services if services else ["No services found"],
        index=0,
        on_change=clear_chat_history
    )
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("How do I configure bucket logging?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            if not services or selected_service == "No services found":
                st.error("Please select a valid service first. Go to 'Knowledge Base' to add services.")
            else:
                message_placeholder = st.empty()
                full_response = ""
                
                try:
                    # RAG Request to /ask
                    # Exclude the last message (current prompt) from history to avoid duplication in context
                    history = st.session_state.messages[:-1]
                    
                    payload = {
                        "question": prompt,
                        "service_name": selected_service,
                        "stream": True,
                        "history": history
                    }
                    
                    with requests.post(
                        f"{st.session_state.api_url}/ask", 
                        json=payload, 
                        stream=True
                    ) as response:
                        if response.status_code == 200:
                            for chunk in response.iter_content(chunk_size=None):
                                if chunk:
                                    chunk_text = chunk.decode("utf-8")
                                    full_response += chunk_text
                                    message_placeholder.markdown(full_response + "▌")
                            
                            message_placeholder.markdown(full_response)
                        else:
                            st.error(f"API Error: {response.status_code} - {response.text}")
                            full_response = "Error generating response."
                            
                except Exception as e:
                    st.error(f"Error: {e}")
                    full_response = f"Error: {e}"

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()

# --- Helper Functions ---
def get_scrapeable_services():
    try:
        response = requests.get(f"{st.session_state.api_url}/services/available")
        if response.status_code == 200:
            return response.json().get("services", [])
        return []
    except Exception:
        return []

# ... (existing functions) ...

# --- Tab 3: Knowledge Base ---
with tab_kb:
    st.header("Manage Knowledge Base")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        scrapeable_services = get_scrapeable_services()
        selected_scrape_service = st.selectbox(
            "Select Service to Scrape",
            options=scrapeable_services if scrapeable_services else ["No services found"],
            index=0,
            key="scrape_select"
        )
        
        # Option to add custom if needed, but for now just the list
        new_service_name = selected_scrape_service
    
    with col2:
        limit_pages = st.slider("Limit Pages (Optional)", min_value=0, max_value=10, value=10, step=1, help="Limit number of pages to scrape for testing.")
        max_jobs = st.slider("Concurrency (Threads)", min_value=1, max_value=4, value=4, step=1, help="Number of pages to scrape in parallel.")

    if st.button("Scrape & Index Service"):
        if not new_service_name or new_service_name == "No services found":
            st.warning("Please select a valid service.")
        else:
            # Create UI elements
            status_container = st.status("Initializing...", expanded=True)
            progress_bar = st.progress(0)
            log_area = st.empty()
            
            try:
                payload = {
                    "services": [new_service_name], 
                    "limit": limit_pages,
                    "max_jobs": max_jobs
                }
                
                # Stream the response
                with requests.post(f"{st.session_state.api_url}/scrape", json=payload, stream=True) as response:
                    if response.status_code == 200:
                        status_container.write("Connected to scraper...")
                        
                        for line in response.iter_lines():
                            if not line: continue
                            
                            try:
                                event = json.loads(line.decode("utf-8"))
                                type_ = event.get("type")
                                
                                if type_ == "log":
                                    msg = event.get("message", "")
                                    status_container.write(f"🔹 {msg}")
                                    log_area.caption(msg)
                                    
                                elif type_ == "progress":
                                    current = event.get("current", 0)
                                    total = event.get("total", 1)
                                    msg = event.get("message", "")
                                    if total > 0:
                                        progress_bar.progress(min(current / total, 1.0))
                                    log_area.caption(f"{msg} ({current}/{total})")
                                    
                                elif type_ == "index_result":
                                    status_container.write("✅ Indexing Complete")
                                    st.json(event.get("stats"))
                                    
                                elif type_ == "error":
                                    status_container.error(event.get("message"))
                                    st.error(event.get("message"))
                                    
                            except Exception as e:
                                print(f"Error parse: {e}")
                        
                        progress_bar.progress(100)
                        status_container.update(label="Process Complete", state="complete", expanded=False)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error: {response.text}")
                        status_container.update(label="Failed", state="error", expanded=False)
                        
            except Exception as e:
                    st.error(f"Error: {e}")
                    status_container.update(label="Error", state="error")

    st.divider()
    st.subheader("Indexed Services")
    if st.button("Refresh List"):
        st.rerun()
    
    # List indexed services

    for service in services:
        col_svc, col_del = st.columns([4, 1])
        with col_svc:
            st.markdown(f"📚 **{service}**")
        with col_del:
            if st.button("🗑️ Delete", key=f"del_{service}"):
                    with st.spinner(f"Deleting {service}..."):
                        del_resp = requests.delete(f"{st.session_state.api_url}/services/{service}")
                        if del_resp.status_code == 200:
                            st.success(f"Deleted {service}")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete: {del_resp.text}")
    
