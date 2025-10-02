import asyncio

def orchestrate_request_stream(self, user_input: str, thread_id: Optional[str] = None):
    """Stream version of orchestrate_request for UI integration"""

    if not self.active_orchestration:
        yield "Error: No active orchestration configuration set"
        return

    async def runner():
        return await self.orchestrate_request(user_input, thread_id)

    try:
        try:
            # If an event loop is already running, schedule the task there
            loop = asyncio.get_running_loop()
            future = asyncio.ensure_future(runner())
            result = loop.run_until_complete(future)  # ❌ still risky
        except RuntimeError:
            # No loop running -> safe to call asyncio.run
            result = asyncio.run(runner())
    except RuntimeError:
        # Jupyter/Notebook safe fallback
        import nest_asyncio
        nest_asyncio.apply()
        result = asyncio.get_event_loop().run_until_complete(runner())
    except Exception as e:
        yield f"Error during orchestration: {str(e)}"
        return

    for char in result:
        yield char
