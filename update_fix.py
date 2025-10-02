# Check if we're in orchestration mode or single-agent mode
is_orchestration = chat_agent == "orchestration"

if is_orchestration:
    # Orchestration mode
    chat_avatar = "🤝"
    chat_name = "Orchestrator"
    
    # Ensure Orchestrator participant exists in database
    orchestrator_participant = chat.get_participant("Orchestrator")
    if orchestrator_participant is None:
        chat.add_participant(
            "Orchestrator",
            participant_type="orchestrator",
            display_name="Orchestrator",
            avatar="🤝"
        )
else:
    # Single-agent mode
    chat_agent.chat_history = messages
    chat_avatar = chat_agent.profile.avatar
    chat_name = chat_agent.name
