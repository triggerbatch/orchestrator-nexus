def get_filtered_tools_for_profile(self):
    """Get only the MCP tools that are assigned to this agent's profile"""
    all_mcp_tools = asyncio.run(self.get_tools())
    
    if not self.actions or len(self.actions) == 0:
        return []
    
    # Handle actions as either strings or dicts
    profile_action_names = set()
    for action in self.actions:
        if isinstance(action, str):
            profile_action_names.add(action)
        elif isinstance(action, dict) and "name" in action:
            profile_action_names.add(action["name"])
    
    print(f"[{self.profile.name}] Looking for tools: {profile_action_names}")
    
    # Filter MCP tools
    filtered = [
        tool for tool in all_mcp_tools 
        if tool.get("function", {}).get("name") in profile_action_names
    ]
    
    print(f"[{self.profile.name}] Found {len(filtered)} matching tools")
    
    return filtered


def initialize_agent_with_profile(self, profile_name: str, engine_name: str = None):
    try:
        # ... existing code to get agent and profile ...
        
        # Load actions from profile
        if hasattr(profile, 'actions') and profile.actions and agent.supports_actions:
            # Handle both string list and dict list formats
            action_names = []
            for action in profile.actions:
                if isinstance(action, str):
                    action_names.append(action)
                elif isinstance(action, dict) and 'name' in action:
                    action_names.append(action['name'])
            
            # Get full action objects from nexus
            agent.actions = self.nexus.get_actions(action_names)
            print(f"Loaded {len(agent.actions)} actions for {profile_name}: {action_names}")
        else:
            agent.actions = []
        
        # ... rest of code ...
