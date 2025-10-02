def orchestrate_request_stream(self, user_input: str, thread_id: Optional[str] = None):
    """Stream version of orchestrate_request for UI integration"""

    if not self.active_orchestration:
        yield "Error: No active orchestration configuration set"
        return

    try:
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, we need to use a different approach
            import concurrent.futures
            
            # Create a new thread to run the async function
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_orchestration_sync, user_input, thread_id)
                result = future.result()
                
        except RuntimeError:
            # No event loop is running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.orchestrate_request(user_input, thread_id)
                )
            finally:
                loop.close()

        # Stream the result character by character for UI consistency
        for char in result:
            yield char

    except Exception as e:
        yield f"Error during orchestration: {str(e)}"


def _run_orchestration_sync(self, user_input: str, thread_id: Optional[str] = None) -> str:
    """Helper method to run orchestration in a new event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            self.orchestrate_request(user_input, thread_id)
        )
        return result
    finally:
        loop.close()
