import asyncio
from grox import *

async def main():
    app = GroxAppConfig.load_yaml("app.yaml")
    # first call should be with app
    GroxContext(app).register_all_projects()

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

    # create Grox graph system that would serve the stream of Agents
    grox = Grox(ctx)
    await grox.handle_event({"thread_id": "1"})
    await grox.handle_event({"thread_id": "1"})

if __name__ == "__main__":
    asyncio.run(main())
