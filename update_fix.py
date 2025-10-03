def load_actions(self):
    """Load actions - handles both static and MCP tools"""
    print(f"[LOAD_ACTIONS] Loading actions")
    self.tools = []
    
    for action in self.actions:
        # Skip if action is just a string (MCP action name)
        if isinstance(action, str):
            print(f"[LOAD_ACTIONS] Skipping MCP action name: {action}")
            continue
            
        # Handle dict-based static actions
        if isinstance(action, dict) and "agent_action" in action:
            self.tools.append(action["agent_action"])
            print(f"[LOAD_ACTIONS] Added static tool: {action.get('name')}")
    
    print(f"[LOAD_ACTIONS] Loaded {len(self.tools)} static tools")
