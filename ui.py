
import base64
import streamlit as st
from datetime import datetime
from scrape import scrape_multiple
from search import get_search_results
from llm_utils import BufferedStreamingHandler, get_model_choices
from llm import get_llm, refine_query, filter_results, generate_summary
from fork_analysis import analyze_repository_forks


def _render_pipeline_error(stage: str, err: Exception) -> None:
    message = str(err).strip() or err.__class__.__name__
    lower_msg = message.lower()
    hints = [
        "- Confirm the relevant API key is set in your `.env` or shell before launching Streamlit.",
        "- Keys copied from dashboards often include hidden spaces; re-copy if authentication keeps failing.",
        "- Restart the app after updating environment variables so the new values are picked up.",
    ]

    if any(token in lower_msg for token in ("anthropic", "x-api-key", "invalid api key", "authentication")):
        hints.insert(0, "- Claude/Anthropic models require a valid `ANTHROPIC_API_KEY`.")
    elif "openrouter" in lower_msg:
        hints.insert(0, "- OpenRouter models require `OPENROUTER_API_KEY` and a reachable OpenRouter endpoint.")
    elif "openai" in lower_msg or "gpt" in lower_msg:
        hints.insert(0, "- OpenAI models require `OPENAI_API_KEY` with access to the chosen model.")
    elif "google" in lower_msg or "gemini" in lower_msg:
        hints.insert(0, "- Google Gemini models need `GOOGLE_API_KEY` or Application Default Credentials.")

    st.error(
        "❌ Failed to {}.\n\nError: {}\n\n{}".format(
            stage,
            message,
            "\n".join(hints),
        )
    )
    st.stop()


# Cache expensive backend calls
@st.cache_data(ttl=200, show_spinner=False)
def cached_search_results(refined_query: str, threads: int):
    return get_search_results(refined_query.replace(" ", "+"), max_workers=threads)


@st.cache_data(ttl=200, show_spinner=False)
def cached_scrape_multiple(filtered: list, threads: int):
    return scrape_multiple(filtered, max_workers=threads)


# Streamlit page configuration
st.set_page_config(
    page_title="Robin: AI-Powered Dark Web OSINT Tool",
    page_icon="🕵️‍♂️",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
            .colHeight {
                max-height: 40vh;
                overflow-y: auto;
                text-align: center;
            }
            .pTitle {
                font-weight: bold;
                color: #FF4B4B;
                margin-bottom: 0.5em;
            }
            .aStyle {
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
                padding-left: 0px;
                text-align: center;
            }
    </style>""",
    unsafe_allow_html=True,
)


# Sidebar
st.sidebar.title("Robin")
st.sidebar.text("AI-Powered Dark Web OSINT Tool")
st.sidebar.markdown(
    """Made by [Apurv Singh Gautam](https://www.linkedin.com/in/apurvsinghgautam/)"""
)

# Add tabs for different features
tab1, tab2 = st.tabs(["🕵️ Dark Web OSINT", "🔍 Fork Analysis"])

with tab1:
    # Dark Web OSINT Tab
    st.sidebar.subheader("OSINT Settings")
    model_options = get_model_choices()
    default_model_index = (
        next(
            (idx for idx, name in enumerate(model_options) if name.lower() == "gpt4o"),
            0,
        )
        if model_options
        else 0
    )
    model = st.sidebar.selectbox(
        "Select LLM Model",
        model_options,
        index=default_model_index,
        key="model_select",
    )
    if any(name not in {"gpt4o", "gpt-4.1", "claude-3-5-sonnet-latest", "llama3.1", "gemini-2.5-flash"} for name in model_options):
        st.sidebar.caption("Locally detected Ollama models are automatically added to this list.")
    threads = st.sidebar.slider("Scraping Threads", 1, 16, 4, key="thread_slider")


    # Main UI - logo and input
    _, logo_col, _ = st.columns(3)
    with logo_col:
        st.image(".github/assets/robin_logo.png", width=200)

    # Display text box and button
    with st.form("search_form", clear_on_submit=True):
        col_input, col_button = st.columns([10, 1])
        query = col_input.text_input(
            "Enter Dark Web Search Query",
            placeholder="Enter Dark Web Search Query",
            label_visibility="collapsed",
            key="query_input",
        )
        run_button = col_button.form_submit_button("Run")

    # Display a status message
    status_slot = st.empty()
    # Pre-allocate three placeholders-one per card
    cols = st.columns(3)
    p1, p2, p3 = [col.empty() for col in cols]
    # Summary placeholders
    summary_container_placeholder = st.empty()


    # Process the query
    if run_button and query:
        # clear old state
        for k in ["refined", "results", "filtered", "scraped", "streamed_summary"]:
            st.session_state.pop(k, None)

        # Stage 1 - Load LLM
        with status_slot.container():
            with st.spinner("🔄 Loading LLM..."):
                try:
                    llm = get_llm(model)
                except Exception as e:
                    _render_pipeline_error("load the selected LLM", e)

        # Stage 2 - Refine query
        with status_slot.container():
            with st.spinner("🔄 Refining query..."):
                try:
                    st.session_state.refined = refine_query(llm, query)
                except Exception as e:
                    _render_pipeline_error("refine the query", e)
        p1.container(border=True).markdown(
            f"<div class='colHeight'><p class='pTitle'>Refined Query</p><p>{st.session_state.refined}</p></div>",
            unsafe_allow_html=True,
        )

        # Stage 3 - Search dark web
        with status_slot.container():
            with st.spinner("🔍 Searching dark web..."):
                st.session_state.results = cached_search_results(
                    st.session_state.refined, threads
                )
        p2.container(border=True).markdown(
            f"<div class='colHeight'><p class='pTitle'>Search Results</p><p>{len(st.session_state.results)}</p></div>",
            unsafe_allow_html=True,
        )

        # Stage 4 - Filter results
        with status_slot.container():
            with st.spinner("🗂️ Filtering results..."):
                st.session_state.filtered = filter_results(
                    llm, st.session_state.refined, st.session_state.results
                )
        p3.container(border=True).markdown(
            f"<div class='colHeight'><p class='pTitle'>Filtered Results</p><p>{len(st.session_state.filtered)}</p></div>",
            unsafe_allow_html=True,
        )

        # Stage 5 - Scrape content
        with status_slot.container():
            with st.spinner("📜 Scraping content..."):
                st.session_state.scraped = cached_scrape_multiple(
                    st.session_state.filtered, threads
                )

        # Stage 6 - Summarize
        # 6a) Prepare session state for streaming text
        st.session_state.streamed_summary = ""

        # 6c) UI callback for each chunk
        def ui_emit(chunk: str):
            st.session_state.streamed_summary += chunk
            summary_slot.markdown(st.session_state.streamed_summary)

        with summary_container_placeholder.container():  # border=True, height=450):
            hdr_col, btn_col = st.columns([4, 1], vertical_alignment="center")
            with hdr_col:
                st.subheader(":red[Investigation Summary]", anchor=None, divider="gray")
            summary_slot = st.empty()

        # 6d) Inject your two callbacks and invoke exactly as before
        with status_slot.container():
            with st.spinner("✍️ Generating summary..."):
                stream_handler = BufferedStreamingHandler(ui_callback=ui_emit)
                llm.callbacks = [stream_handler]
                _ = generate_summary(llm, query, st.session_state.scraped)

        with btn_col:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            fname = f"summary_{now}.md"
            b64 = base64.b64encode(st.session_state.streamed_summary.encode()).decode()
            href = f'<div class="aStyle">📥 <a href="data:file/markdown;base64,{b64}" download="{fname}">Download</a></div>'
            st.markdown(href, unsafe_allow_html=True)
        status_slot.success("✔️ Pipeline completed successfully!")

with tab2:
    # Fork Analysis Tab
    st.markdown("### 🔍 Repository Fork Analysis")
    st.markdown("Analyze GitHub repository forks to identify those substantially ahead of the parent.")
    
    with st.form("fork_analysis_form"):
        col1, col2 = st.columns(2)
        with col1:
            owner = st.text_input("Repository Owner", placeholder="e.g., apurvsinghgautam", help="GitHub username or organization")
        with col2:
            repo = st.text_input("Repository Name", placeholder="e.g., robin", help="Repository name")
        
        min_commits = st.slider("Minimum Commits Ahead", 1, 50, 1, help="Minimum number of commits ahead to be reported")
        
        analyze_button = st.form_submit_button("🔍 Analyze Forks", use_container_width=True)
    
    if analyze_button:
        if not owner or not repo:
            st.error("❌ Please provide both repository owner and name.")
        else:
            fork_status = st.empty()
            fork_results = st.empty()
            
            with fork_status.container():
                with st.spinner(f"🔄 Analyzing forks of {owner}/{repo}..."):
                    try:
                        report = analyze_repository_forks(owner, repo, min_commits)
                        fork_status.success("✅ Analysis completed!")
                        
                        # Display the report
                        fork_results.text_area(
                            "Fork Analysis Report",
                            value=report,
                            height=400,
                            label_visibility="collapsed"
                        )
                        
                        # Add download button
                        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        fname = f"fork_analysis_{owner}_{repo}_{now}.txt"
                        b64 = base64.b64encode(report.encode()).decode()
                        href = f'<div class="aStyle">📥 <a href="data:text/plain;base64,{b64}" download="{fname}">Download Report</a></div>'
                        st.markdown(href, unsafe_allow_html=True)
                        
                    except Exception as e:
                        fork_status.error(f"❌ Error during fork analysis: {str(e)}")
    
    # Add helpful information
    with st.expander("ℹ️ About Fork Analysis"):
        st.markdown("""
        This feature analyzes GitHub repository forks to identify forks that have commits ahead of the parent repository.
        
        **How it works:**
        1. Fetches all forks of the specified repository
        2. Compares each fork with the parent repository
        3. Identifies forks that are ahead (have additional commits)
        4. Generates a report sorted by commits ahead
        
        **Note:** 
        - For better API rate limits, set the `GITHUB_TOKEN` environment variable
        - You can create a personal access token at https://github.com/settings/tokens
        - Without authentication, you may hit rate limits on repositories with many forks
        """)
