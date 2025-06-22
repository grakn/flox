import asyncio
from flox.config import FloxConfig
from flox.context import FloxContext
from flox.logger import setup_logging
from flox.projects import Project
from flox.flox import Flox

async def main():
    config = FloxConfig.load_from_file("flox.yaml")
    setup_logging(config)

    flox_ctx = FloxContext(config)

    # Register some projects
    for tenant_id, projects in config.projects.items():
        for project_code, proj_conf in projects.items():
            project = Project(tenant_id=tenant_id, project_code=project_code, config=proj_conf)
            flox_ctx.register_project(project)

    # Create per-request context
    ctx = flox_ctx.create_request_context(
        tenant_id="tenantA",
        project_code="projectX",
        correlation_id="corr-1234",
        user_id="user-5678"
    )

    flox = Flox(ctx, correlation_id="corr-1234", user_id="user-5678")
    await flox.handle_event({"some": "data"})

if __name__ == "__main__":
    asyncio.run(main())
