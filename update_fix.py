def orchestrate_request_stream(self, user_input: str, thread_id: Optional[str] = None):
    """Stream version with agent-by-agent updates"""
    
    if not self.active_orchestration:
        yield "Error: No active orchestration configuration set"
        return

    try:
        yield f"🎯 **Orchestrator ({self.active_orchestration.orchestrator_profile})**: Processing request...\n\n"
        
        # Get orchestrator's decision
        orchestrator = self.initialize_agent_with_profile(
            self.active_orchestration.orchestrator_profile,
            self.active_orchestration.orchestrator_engine
        )
        
        orchestration_prompt = self._build_orchestration_prompt(user_input)
        
        full_response = ""
        for chunk in orchestrator.get_response_stream(orchestration_prompt)():
            full_response += chunk
            yield chunk
        
        yield "\n\n"
        
        # Check for delegation
        if self._check_for_delegation(full_response):
            target_profile = self._extract_delegate_profile(full_response)
            yield f"↪️ **Delegating to {target_profile}**...\n\n"
            
            delegated_response = self._handle_delegation(
                user_input,
                full_response,
                self.active_orchestration.orchestrator_profile
            )
            
            yield f"📋 **{target_profile} Response**:\n{delegated_response}\n\n"
            
            # Final synthesis
            yield f"🎯 **Orchestrator Synthesis**:\n"
            synthesis_prompt = f"""Based on:
Original: {user_input}
Your analysis: {full_response}
{target_profile} result: {delegated_response}

Final response:"""
            
            for chunk in orchestrator.get_response_stream(synthesis_prompt)():
                yield chunk

    except Exception as e:
        yield f"Error: {str(e)}"
