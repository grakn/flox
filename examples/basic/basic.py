import asyncio
import secrets
from grox import *

def generate_id():
    secrets.token_urlsafe(20)

async def main():

    secrets = {
        # this parameter in secrets, because in production url can have password
        "redis_endpoint": "redis://localhost:6379/0",
    }

    app = GroxAppConfig.load_yaml("app.yaml")
    # first call should be with app
    GroxContext(app).register_all_projects(secrets)

    if not GroxContext().has_project(tenant_id="tenantA",
        project_code="project_a"):
        print("Error: Project not initialized")
        return

    # GroxContext - is the global context, you should additionally
    # Create per-request/per-execution context
    ctx = GroxContext().create_execution_context(
        tenant_id="tenantA",
        project_code="project_a",
        input = {
            "param1": "1",
            "param2": "2"
        },
        correlation_id="corr-1234",
        user_id="user-5678"
    )

    session_id = generate_id()

    all_messages = []
    def output_handler(event:dict):
        messages = event.get('agent', {}).get('messages', [])
        all_messages.extend(messages)

    # create Grox graph system that would serve the stream of Agents
    grox = Grox(ctx)
    await grox.handle_event({"session_id": session_id, "prompt": "What is the weather today?"}, output_handler)
    await grox.handle_event({"session_id": session_id, "prompt": "In SF"}, output_handler)

    if all_messages:
        last_message = all_messages[-1]
        grox.print("last_message:", last_message.content)
    else:
        grox.print("No messages received.")

if __name__ == "__main__":
    asyncio.run(main())
