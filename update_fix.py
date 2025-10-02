def get_filtered_tools_for_profile(self):
    """Get only the MCP tools that are assigned to this agent's profile"""
    # Get all available MCP tools
    all_mcp_tools = asyncio.run(self.get_tools())
    
    if not self.actions or len(self.actions) == 0:
        return []
    
    # Extract action names from profile
    profile_action_names = {action.get("name") for action in self.actions if "name" in action}
    
    # Filter MCP tools
    filtered = [
        tool for tool in all_mcp_tools 
        if tool.get("function", {}).get("name") in profile_action_names
    ]
    
    print(f"[{self.profile.name}] MCP tools: {len(all_mcp_tools)} available, {len(filtered)} assigned")
    
    return filtered

def get_response_stream(self, user_input, thread_id=None):
    self.last_message = ""
    self.messages += [{"role": "user", "content": user_input}]
    
    # Get filtered tools based on profile
    filtered_tools = self.get_filtered_tools_for_profile()
    
    if filtered_tools and len(filtered_tools) > 0:
        tools_serializable = self.serialize_tools(filtered_tools)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            tools=tools_serializable,
            tool_choice="auto",
        )
    else:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
        )
    
    # ... rest of streaming logic
