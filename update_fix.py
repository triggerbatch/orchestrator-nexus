def get_response_stream(self, user_input, thread_id=None):
    self.last_message = ""
    self.messages += [{"role": "user", "content": user_input}]
    
    # Add these debug lines BEFORE calling the method
    print(f"\n[DEBUG] About to call get_filtered_tools_for_profile()")
    print(f"[DEBUG] self.profile = {self.profile}")
    print(f"[DEBUG] self.profile.name = {self.profile.name if self.profile else 'NO PROFILE'}")
    print(f"[DEBUG] self.actions = {self.actions}")
    print(f"[DEBUG] len(self.actions) = {len(self.actions) if self.actions else 0}")
    
    # Get filtered tools based on profile
    filtered_tools = self.get_filtered_tools_for_profile()
    
    print(f"[DEBUG] After call - filtered_tools = {filtered_tools}")
    print(f"[DEBUG] len(filtered_tools) = {len(filtered_tools) if filtered_tools else 0}\n")
    
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
            max_tokens=self.max_tokens,
        )
    
    # ... rest of your code

def get_filtered_tools_for_profile(self):
    """Get only the MCP tools that are assigned to this agent's profile"""
    try:
        print(f"\n[FILTER] === ENTERED get_filtered_tools_for_profile ===")
        
        all_mcp_tools = asyncio.run(self.get_tools())
        
        print(f"[FILTER] all_mcp_tools retrieved: {len(all_mcp_tools)}")
        
        if not self.actions or len(self.actions) == 0:
            print(f"[FILTER] No actions configured - returning empty list")
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
        
    except Exception as e:
        print(f"[FILTER] EXCEPTION in get_filtered_tools_for_profile: {e}")
        import traceback
        traceback.print_exc()
        return []
