def get_filtered_tools_for_profile(self):
    """Get only the MCP tools that are assigned to this agent's profile"""
    try:
        print(f"\n[FILTER] === ENTERED get_filtered_tools_for_profile ===")
        
        all_mcp_tools = asyncio.run(self.get_tools())
        
        print(f"[FILTER] all_mcp_tools retrieved: {len(all_mcp_tools)}")
        
        # Debug: show actual tool names
        print(f"[FILTER] DEBUG - Actual tool names from MCP:")
        for tool in all_mcp_tools:
            # Handle Tool objects
            if hasattr(tool, 'name'):
                print(f"  - {tool.name}")
            elif isinstance(tool, dict):
                if 'name' in tool:
                    print(f"  - {tool['name']}")
                elif 'function' in tool and isinstance(tool['function'], dict):
                    print(f"  - {tool['function'].get('name')}")
        
        if not self.actions or len(self.actions) == 0:
            print(f"[FILTER] No actions configured - returning empty list")
            return []
        
        # Get action names from self.actions
        profile_action_names = set()
        for action in self.actions:
            if isinstance(action, str):
                profile_action_names.add(action)
            elif isinstance(action, dict) and "name" in action:
                profile_action_names.add(action["name"])
        
        print(f"[{self.profile.name}] Looking for tools: {profile_action_names}")
        
        # Filter MCP tools
        filtered = []
        for tool in all_mcp_tools:
            tool_name = None
            
            # Handle Tool objects from MCP (YOUR CASE)
            if hasattr(tool, 'name'):
                tool_name = tool.name
                
                if tool_name in profile_action_names:
                    # Convert Tool object to OpenAI format
                    tool_dict = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": getattr(tool, 'description', ''),
                            "parameters": getattr(tool, 'inputSchema', {})
                        }
                    }
                    filtered.append(tool_dict)
                    print(f"[{self.profile.name}] ✓ Added tool: {tool_name}")
            
            # Handle dict format (backup)
            elif isinstance(tool, dict):
                if 'name' in tool:
                    tool_name = tool['name']
                elif 'function' in tool and isinstance(tool['function'], dict):
                    tool_name = tool['function'].get('name')
                
                if tool_name and tool_name in profile_action_names:
                    filtered.append(tool)
                    print(f"[{self.profile.name}] ✓ Added tool: {tool_name}")
        
        print(f"[{self.profile.name}] Found {len(filtered)} matching tools")
        
        return filtered
        
    except Exception as e:
        print(f"[FILTER] EXCEPTION in get_filtered_tools_for_profile: {e}")
        import traceback
        traceback.print_exc()
        return []
