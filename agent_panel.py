import streamlit as st

from nexus.streamlit_ui.options import create_options_ui


def agent_panel(chat):
    st.title("Agent Settings")

    # Add orchestration mode toggle
    use_orchestration = st.toggle(
        "Enable Agent Orchestration (A2A)",
        value=False,
        help="Enable multi-agent orchestration mode"
    )

    if use_orchestration:
        # Orchestration mode
        st.subheader("🤝 Orchestration Mode")

        orchestrations = chat.get_orchestration_names()

        if not orchestrations:
            st.warning(
                "No orchestration configurations found. Please create a configuration YAML file in nexus_orchestrations/")
            st.info("Example: Create 'main_orchestrator.yaml' with agent network definitions")
            return None

        selected_orchestration = st.selectbox(
            "Choose orchestration configuration:",
            orchestrations,
            key="orchestration_config",
            help="Select which orchestration setup to use"
        )

        if selected_orchestration:
            chat.set_active_orchestration(selected_orchestration)
            orchestration_config = chat.get_active_orchestration()

            # Display orchestration details
            with st.expander("Orchestration Details", expanded=True):
                st.write(f"**Description:** {orchestration_config.description}")
                st.write(f"**Main Orchestrator:** {orchestration_config.orchestrator_agent}")
                st.write(f"**Profile:** {orchestration_config.orchestrator_profile}")

                st.write("**Agent Network:**")
                for agent_cfg in orchestration_config.agent_network:
                    st.write(f"- **{agent_cfg['agent_name']}** ({agent_cfg['role']})")
                    st.write(f"  Capabilities: {', '.join(agent_cfg.get('capabilities', []))}")
                    if agent_cfg.get('can_delegate_to'):
                        st.write(f"  Can delegate to: {', '.join(agent_cfg['can_delegate_to'])}")

            # Show A2A conversation history
            with st.expander("A2A Conversation History", expanded=False):
                history = chat.get_a2a_conversation_history()
                if history:
                    for idx, conv in enumerate(history):
                        st.write(f"**{idx + 1}. {conv['from']} → {conv['to']}** (Depth: {conv['depth']})")
                        st.write(f"Request: {conv['request'][:100]}...")
                        st.write(f"Response: {conv['response'][:100]}...")
                        st.divider()

                    if st.button("Clear A2A History"):
                        chat.clear_a2a_conversation_history()
                        st.rerun()
                else:
                    st.info("No agent-to-agent interactions yet")

            return "orchestration"  # Return special marker for orchestration mode

    else:
        # Standard single-agent mode
        st.subheader("🤖 Single Agent Mode")

        agents = chat.get_agent_names()
        selected_agent = st.selectbox(
            "Choose an agent engine:",
            agents,
            key="agents",
            help="Choose an agent to chat with.",
        )
        chat_agent = chat.get_agent(selected_agent)

        with st.expander("Agent Options:", expanded=False):
            options = chat_agent.get_attribute_options()
            if options:
                selected_options = create_options_ui(options)
                for key, value in selected_options.items():
                    setattr(chat_agent, key, value)

        profiles = chat.get_profile_names()

        def format_agent_profile(agent_name):
            profile = chat.get_profile(agent_name)
            return f"{profile.avatar} : {profile.name}"

        selected_profile = st.selectbox(
            "Choose an agent profile:",
            profiles,
            key="profiles",
            help="Choose a profile for your agent.",
            format_func=format_agent_profile,
        )

        chat_agent.actions = []
        if chat_agent.supports_actions:
            action_names = chat.get_action_names()
            selected_action_names = st.multiselect(
                "Select actions:",
                action_names,
                key="actions",
                help="Choose the actions the agent can use.",
            )
            selected_actions = chat.get_actions(selected_action_names)
            chat_agent.actions = selected_actions

        chat_agent.knowledge_store = "None"
        if chat_agent.supports_knowledge:
            knowledge_stores = chat.get_knowledge_store_names()
            selected_knowledge_store = st.selectbox(
                "Select a knowledge store:",
                ["None"] + knowledge_stores,
                key="knowledge_store",
                help="Choose the knowledge store to use.",
            )
            chat_agent.knowledge_store = selected_knowledge_store

        chat_agent.memory_store = "None"
        if chat_agent.supports_memory:
            memory_stores = chat.get_memory_store_names()
            selected_memory_store = st.selectbox(
                "Select a memory store:",
                ["None"] + memory_stores,
                key="memory_store",
                help="Choose the memory store to use.",
            )
            chat_agent.memory_store = selected_memory_store

        chat_agent.profile = chat.get_profile(selected_profile)

        return chat_agent
