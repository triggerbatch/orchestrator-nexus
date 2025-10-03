def initialize_agent_with_profile(self, profile_name: str, engine_name: str = None):
    """Initialize an agent with a specific profile and load all configurations"""
    try:
        # Determine engine name
        if engine_name is None:
            engine_name = self.active_orchestration.profile_to_engine.get(
                profile_name,
                'AzureOpenAIAgent'
            )
        
        print(f"\n[INIT] Initializing agent with profile: {profile_name}, engine: {engine_name}")
        
        # Get agent and profile
        agent = self.nexus.get_agent(engine_name)
        profile = self.nexus.get_profile(profile_name)
        agent.profile = profile
        
        # Get agent configuration from orchestration network
        agent_config = next(
            (cfg for cfg in self.active_orchestration.agent_network 
             if cfg.get('profile') == profile_name),
            None
        )
        
        # ===== ACTIONS ===== THIS IS THE FIX
        if agent.supports_actions:
            action_names = []
            
            # Priority 1: Actions from orchestration config
            if agent_config and 'actions' in agent_config and agent_config['actions']:
                print(f"[INIT] Loading actions from orchestration config")
                action_names = agent_config['actions']
            # Priority 2: Actions from profile
            elif hasattr(profile, 'actions') and profile.actions:
                print(f"[INIT] Loading actions from profile")
                for action in profile.actions:
                    if isinstance(action, str):
                        action_names.append(action)
                    elif isinstance(action, dict) and 'name' in action:
                        action_names.append(action['name'])
            
            if action_names:
                print(f"[INIT] Requesting actions: {action_names}")
                
                # CRITICAL FIX: Store action names as string list, not dict objects
                # The agent will use these names to filter MCP tools
                agent.actions = action_names
                
                print(f"[INIT] Set agent.actions = {agent.actions}")
                print(f"[INIT] Configured {len(agent.actions)} action names for {profile_name}")
            else:
                agent.actions = []
                print(f"[INIT] No actions configured for {profile_name}")
        else:
            agent.actions = []
            print(f"[INIT] Agent engine {engine_name} does not support actions")
        
        # ===== KNOWLEDGE STORE =====
        if agent.supports_knowledge:
            knowledge_store = None
            
            if agent_config and 'knowledge' in agent_config:
                knowledge_store = agent_config['knowledge']
            elif hasattr(profile, 'knowledge') and profile.knowledge:
                if isinstance(profile.knowledge, list):
                    knowledge_store = profile.knowledge[0] if profile.knowledge else None
                else:
                    knowledge_store = profile.knowledge
            
            if knowledge_store and knowledge_store != "None":
                agent.knowledge_store = knowledge_store
                print(f"[INIT] Set knowledge store: {knowledge_store}")
            else:
                agent.knowledge_store = "None"
                print(f"[INIT] No knowledge store configured")
        else:
            agent.knowledge_store = "None"
        
        # ===== MEMORY STORE =====
        if agent.supports_memory:
            memory_store = None
            
            if agent_config and 'memory' in agent_config:
                memory_store = agent_config['memory']
            elif hasattr(profile, 'memory') and profile.memory:
                if isinstance(profile.memory, list):
                    memory_store = profile.memory[0] if profile.memory else None
                else:
                    memory_store = profile.memory
            
            if memory_store and memory_store != "None":
                agent.memory_store = memory_store
                print(f"[INIT] Set memory store: {memory_store}")
            else:
                agent.memory_store = "None"
                print(f"[INIT] No memory store configured")
        else:
            agent.memory_store = "None"
        
        # ===== RESET MESSAGES =====
        if hasattr(agent, 'messages'):
            agent.messages = []
            print(f"[INIT] Reset message history")
        
        if hasattr(agent, 'chat_history'):
            agent.chat_history = []
            print(f"[INIT] Reset chat history")
        
        print(f"[INIT] Agent initialization complete for {profile_name}\n")
        
        return agent

    except Exception as e:
        print(f"[INIT] ERROR initializing agent with profile {profile_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
