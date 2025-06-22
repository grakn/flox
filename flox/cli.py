import shutil
from pathlib import Path
import click
import shutil
import os
import sys
import importlib.util
from flox.config import FloxConfig
from flox.logger import setup_logging
from flox.context import FloxContext
from flox.projects import Project


@click.group()
def cli():
    """Flox CLI: project lifecycle manager"""
    pass

CODE_TEMPLATE = """from flox import FloxContext, Flox

async def main():
    cfg = FloxConfig(service="test", environment="test", projects={})
    flox_ctx = FloxContext(cfg)
    ctx = flox_ctx.create_request_context(
        tenant_id="{project_code}",
        project_code="{project_code}",
        correlation_id="sample-correlation-id"
        )
    flox = Flox(ctx)
    flox.logger.info("project started")

    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())
"""

@cli.command()
@click.argument("project_code")
@click.option("--path", "-p", default=".", help="Target directory for the project")
def create(project_code: str, path: str):
    """Create a new flox project in the given directory."""
    target_dir = Path(path) / project_code

    if target_dir.exists():
        click.confirm(
            f"Directory '{target_dir}' already exists. Do you want to override it?",
            abort=True,
            default=False,
        )
        # User confirmed: remove directory before recreating
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True, exist_ok=False)

    # Create basic structure
    (target_dir / "main.py").write_text(CODE_TEMPLATE)

    (target_dir / "flox.yaml").write_text(
        f"""service: {project_code}
environment: development
log_level: DEBUG
projects:
  {project_code}:
    {project_code}:
      model_path: "./model"
"""
    )

    click.echo(f"✅ Project '{project_code}' created at {target_dir}")


@cli.command()
@click.argument("project_code")
@click.option("--path", "-p", default=".", help="Project directory (defaults to current dir)")
def run(project_code: str, path: str):
    """Run the given flox project (calls main.py in the project folder)."""
    project_dir = Path(path) / project_code
    main_path = project_dir / "main.py"
    config_path = project_dir / "flox.yaml"

    if not main_path.exists():
        click.echo(f"❌ main.py not found in {project_dir}")
        sys.exit(1)

    if not config_path.exists():
        click.echo(f"❌ flox.yaml not found in {project_dir}")
        sys.exit(1)

    sys.path.insert(0, str(project_dir))

    # Dynamically load main.py and run main()
    spec = importlib.util.spec_from_file_location("main", str(main_path))
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)

    if hasattr(main_module, "main"):
        import asyncio
        asyncio.run(main_module.main())
    else:
        click.echo("❌ main.py does not define an async 'main' function")
        sys.exit(1)
