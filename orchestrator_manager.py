import os
import yaml
from typing import Dict, List, Optional, Any
import asyncio
import re


class OrchestrationConfig:
    """Represents an orchestration configuration"""

    def __init__(
            self,
            name: str,
            orchestrator_profile: str,
            orchestrator_engine: str,
            description: str,
            agent_network: List[Dict],
            orchestration_rules: List[Dict],
            communication: Dict
    ):
        self.name = name
        self.orchestrator_profile = orchestrator_profile
        self.orchestrator_engine = orchestrator_engine
        self.description = description
        self.agent_network = agent_network
        self.orchestration_rules = orchestration_rules
        self.communication = communication

        # Build quick lookup structures based on profiles
        self.profile_capabilities = {}
        self.profile_delegation_map = {}
        self.profile_to_engine = {}

        for agent_config in agent_network:
            profile_name = agent_config.get('profile')
            if profile_name:
                self.profile_capabilities[profile_name] = agent_config.get('capabilities', [])
                self.profile_delegation_map[profile_name] = agent_config.get('can_delegate_to', [])
                self.profile_to_engine[profile_name] = agent_config.get('engine', 'AzureOpenAIAgent')


class AgentMessage:
    """Represents a message between agents"""

    def __init__(
            self,
            from_profile: str,
            to_profile: str,
            content: str,
            message_type: str = "request",
            context: Optional[Dict] = None,
            depth: int = 0
    ):
        self.from_profile = from_profile
        self.to_profile = to_profile
        self.content = content
        self.message_type = message_type  # request, response, consultation
        self.context = context or {}
        self.depth = depth

    def to_dict(self):
        return {
            "from_profile": self.from_profile,
            "to_profile": self.to_profile,
            "content": self.content,
            "message_type": self.message_type,
            "context": self.context,
            "depth": self.depth
        }


class OrchestrationManager:
    """Manages agent-to-agent orchestration based on profiles"""

    def __init__(self, nexus_instance):
        self.nexus = nexus_instance
        self.directory = os.path.join(
            os.path.dirname(__file__),
            "nexus_orchestrations"
        )
        self.orchestration_configs = []
        self.active_orchestration = None
        self.conversation_history = []
        self.load_orchestrations()

    def load_orchestrations(self):
        """Load all orchestration configurations from YAML files"""
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            print(f"Created orchestrations directory: {self.directory}")
            return

        loaded_count = 0
        for filename in os.listdir(self.directory):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(self.directory, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        config_data = yaml.safe_load(file)
                        self.create_orchestration_config(config_data)
                        loaded_count += 1
                except Exception as e:
                    print(f"Error loading orchestration from {filename}: {str(e)}")

        print(f"Loaded {loaded_count} orchestration configurations.")

    def create_orchestration_config(self, config_data: Dict):
        """Create an orchestration config from YAML data"""
        try:
            if "orchestrationConfig" in config_data:
                config = config_data["orchestrationConfig"]
                orchestration = OrchestrationConfig(
                    name=config.get("name", "Unnamed"),
                    orchestrator_profile=config.get("orchestrator_profile", ""),
                    orchestrator_engine=config.get("orchestrator_engine", "AzureOpenAIAgent"),
                    description=config.get("description", ""),
                    agent_network=config.get("agent_network", []),
                    orchestration_rules=config.get("orchestration_rules", []),
                    communication=config.get("communication", {})
                )
                self.orchestration_configs.append(orchestration)
            else:
                print("Warning: YAML file missing 'orchestrationConfig' key")
        except Exception as e:
            print(f"Error creating orchestration config: {str(e)}")

    def get_orchestration_names(self) -> List[str]:
        """Get all orchestration configuration names"""
        return [config.name for config in self.orchestration_configs]

    def get_orchestration(self, name: str) -> Optional[OrchestrationConfig]:
        """Get orchestration by name"""
        for config in self.orchestration_configs:
            if config.name == name:
                return config
        return None

    def set_active_orchestration(self, name: str) -> bool:
        """Set the active orchestration configuration"""
        config = self.get_orchestration(name)
        if config:
            self.active_orchestration = config
            self.conversation_history = []  # Clear history when switching
            print(f"Active orchestration set to: {name}")
            return True
        print(f"Orchestration '{name}' not found")
        return False

    def initialize_agent_with_profile(self, profile_name: str, engine_name: str = None):
        """Initialize an agent with a specific profile"""
        try:
            # Get the engine to use
            if engine_name is None:
                engine_name = self.active_orchestration.profile_to_engine.get(
                    profile_name,
                    'AzureOpenAIAgent'
                )

            # Get the agent instance
            agent = self.nexus.get_agent(engine_name)

            # Apply profile
            profile = self.nexus.get_profile(profile_name)
            agent.profile = profile

            # Apply actions if profile has them and agent supports them
            if hasattr(profile, 'actions') and profile.actions and agent.supports_actions:
                agent.actions = self.nexus.get_actions(profile.actions)
            elif agent.supports_actions:
                agent.actions = []

            # Apply knowledge store if profile has it and agent supports it
            if hasattr(profile, 'knowledge') and profile.knowledge and agent.supports_knowledge:
                agent.knowledge_store = profile.knowledge[0] if isinstance(profile.knowledge, list) else profile.knowledge
            elif agent.supports_knowledge:
                agent.knowledge_store = "None"

            # Apply memory store if profile has it and agent supports it
            if hasattr(profile, 'memory') and profile.memory and agent.supports_memory:
                agent.memory_store = profile.memory[0] if isinstance(profile.memory, list) else profile.memory
            elif agent.supports_memory:
                agent.memory_store = "None"

            # Clear chat history for clean processing
            if hasattr(agent, 'messages'):
                agent.messages = []

            return agent

        except Exception as e:
            print(f"Error initializing agent with profile {profile_name}: {str(e)}")
            raise

    def get_best_profile_for_task(self, task: str, required_capabilities: List[str] = None) -> Optional[str]:
        """Determine which profile is best suited for a task"""
        if not self.active_orchestration:
            return None

        if not required_capabilities:
            return self.active_orchestration.orchestrator_profile

        # Find profiles with matching capabilities
        matching_profiles = []
        for profile_name, capabilities in self.active_orchestration.profile_capabilities.items():
            match_count = sum(1 for cap in required_capabilities if cap in capabilities)
            if match_count > 0:
                matching_profiles.append((profile_name, match_count))

        if matching_profiles:
            # Return profile with most matching capabilities
            matching_profiles.sort(key=lambda x: x[1], reverse=True)
            return matching_profiles[0][0]

        return self.active_orchestration.orchestrator_profile

    def can_delegate(self, from_profile: str, to_profile: str) -> bool:
        """Check if one profile can delegate to another"""
        if not self.active_orchestration:
            return False

        allowed_delegates = self.active_orchestration.profile_delegation_map.get(from_profile, [])
        return to_profile in allowed_delegates

    async def delegate_to_profile(
            self,
            message: AgentMessage
    ) -> str:
        """Delegate a task to a specific profile"""
        try:
            # Check depth limit
            max_depth = self.active_orchestration.communication.get('max_delegation_depth', 3)
            if message.depth >= max_depth:
                return "Maximum delegation depth reached. Unable to process request."

            # Check if delegation is allowed
            if not self.can_delegate(message.from_profile, message.to_profile):
                return f"Delegation from {message.from_profile} to {message.to_profile} not allowed by configuration."

            # Initialize the target agent with the profile
            agent = self.initialize_agent_with_profile(message.to_profile)

            # Prepare the message context
            context_prompt = ""
            if self.active_orchestration.communication.get('include_context', True):
                context_prompt = f"\n\nContext: You are receiving this request from {message.from_profile}. "
                if message.context:
                    context_prompt += f"Previous context: {message.context.get('summary', '')}"

            # Build the full prompt
            full_prompt = f"{message.content}{context_prompt}"

            # Get response from delegated agent
            response = agent.get_response_stream(full_prompt)

            # Collect the streamed response
            full_response = ""
            for chunk in response():
                full_response += chunk

            # Record in conversation history
            self.conversation_history.append({
                "from": message.from_profile,
                "to": message.to_profile,
                "request": message.content,
                "response": full_response,
                "depth": message.depth
            })

            return full_response

        except Exception as e:
            error_msg = f"Error during delegation: {str(e)}"
            print(error_msg)
            return error_msg

    async def orchestrate_request(
            self,
            user_input: str,
            thread_id: Optional[str] = None
    ) -> str:
        """Main orchestration method - coordinates agents based on profiles"""

        if not self.active_orchestration:
            raise ValueError("No active orchestration configuration set")

        try:
            # Initialize the orchestrator with its profile
            orchestrator = self.initialize_agent_with_profile(
                self.active_orchestration.orchestrator_profile,
                self.active_orchestration.orchestrator_engine
            )

            # Build orchestration prompt
            orchestration_prompt = self._build_orchestration_prompt(user_input)

            # Get orchestrator's decision/response
            response = orchestrator.get_response_stream(orchestration_prompt)

            # Collect the response
            full_response = ""
            for chunk in response():
                full_response += chunk

            # Parse if orchestrator wants to delegate
            delegation_needed = self._check_for_delegation(full_response)

            if delegation_needed:
                # Handle delegation to next profile in chain
                delegated_response = await self._handle_delegation(
                    user_input,
                    full_response,
                    self.active_orchestration.orchestrator_profile
                )

                # Synthesize final response
                synthesis_prompt = f"""Based on the following information:
Original request: {user_input}
Your initial processing: {full_response}
Result from {self._extract_delegate_profile(full_response)}: {delegated_response}

Provide a comprehensive final response to the user."""

                final_response = orchestrator.get_response_stream(synthesis_prompt)
                synthesized = ""
                for chunk in final_response():
                    synthesized += chunk

                return synthesized

            return full_response

        except Exception as e:
            error_msg = f"Error during orchestration: {str(e)}"
            print(error_msg)
            return error_msg

    def _build_orchestration_prompt(self, user_input: str) -> str:
        """Build prompt with orchestration context"""

        available_profiles = []
        current_profile = self.active_orchestration.orchestrator_profile

        # Get profiles this orchestrator can delegate to
        can_delegate_to = self.active_orchestration.profile_delegation_map.get(current_profile, [])

        for profile_name in can_delegate_to:
            capabilities = self.active_orchestration.profile_capabilities.get(profile_name, [])
            role = next(
                (cfg['role'] for cfg in self.active_orchestration.agent_network
                 if cfg.get('profile') == profile_name),
                'specialist'
            )
            capabilities_str = ", ".join(capabilities)
            available_profiles.append(
                f"- {profile_name}: {role} (capabilities: {capabilities_str})"
            )

        if available_profiles:
            orchestration_context = f"""You are the orchestrator with profile: {current_profile}. 
You can coordinate with other specialist agents when needed.

Available specialists you can delegate to:
{chr(10).join(available_profiles)}

If you need specialist help, indicate this by starting your response with [DELEGATE: ProfileName] 
followed by the specific question or task for that specialist.

User request: {user_input}

Process this request. If you can handle it completely, respond directly. 
If a specialist would provide better results, delegate to them."""
        else:
            orchestration_context = f"""You are processing this request with profile: {current_profile}.

User request: {user_input}"""

        return orchestration_context

    def _check_for_delegation(self, response: str) -> bool:
        """Check if response indicates delegation is needed"""
        return response.strip().startswith("[DELEGATE:")

    def _extract_delegate_profile(self, response: str) -> str:
        """Extract the profile name from delegation instruction"""
        match = re.search(r'\[DELEGATE:\s*([\w_]+)\]', response)
        if match:
            return match.group(1)
        return "Unknown"

    async def _handle_delegation(
            self,
            original_request: str,
            orchestrator_response: str,
            from_profile: str
    ) -> str:
        """Handle delegation to specialist profiles"""

        try:
            # Parse delegation instruction
            lines = orchestrator_response.split('\n')
            delegation_line = lines[0]

            # Extract target profile name
            match = re.search(r'\[DELEGATE:\s*([\w_]+)\]', delegation_line)
            if not match:
                return "Delegation parsing error: Could not extract profile name"

            target_profile = match.group(1)

            # Check if delegation is allowed
            if not self.can_delegate(from_profile, target_profile):
                return f"Delegation from {from_profile} to {target_profile} not allowed"

            # Extract the actual task for the delegate
            task = '\n'.join(lines[1:]).strip()
            if not task:
                task = original_request

            # Create and send message
            message = AgentMessage(
                from_profile=from_profile,
                to_profile=target_profile,
                content=task,
                message_type="request",
                context={"original_request": original_request, "summary": orchestrator_response[:200]},
                depth=1
            )

            response = await self.delegate_to_profile(message)

            # Check if the delegate wants to delegate further
            if self._check_for_delegation(response):
                response = await self._handle_delegation(original_request, response, target_profile)

            return response

        except Exception as e:
            return f"Error handling delegation: {str(e)}"

    def orchestrate_request_stream(self, user_input: str, thread_id: Optional[str] = None):
        """Stream version of orchestrate_request for UI integration"""

        if not self.active_orchestration:
            yield "Error: No active orchestration configuration set"
            return

        try:
            # Create and run event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.orchestrate_request(user_input, thread_id)
                )

                # Stream the result character by character for UI consistency
                for char in result:
                    yield char

            finally:
                loop.close()

        except Exception as e:
            yield f"Error during orchestration: {str(e)}"

    def get_conversation_history(self) -> List[Dict]:
        """Get the A2A conversation history"""
        return self.conversation_history.copy()

    def clear_conversation_history(self):
        """Clear the A2A conversation history"""
        self.conversation_history = []
        print("A2A conversation history cleared")
