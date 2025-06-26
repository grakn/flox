import shutil
from pathlib import Path
import click
import shutil
import os
import sys
import importlib.util
from grox.config import GroxAppConfig, GroxProjectConfig
from grox.logger import setup_logging
from grox.context import GroxContext, GroxRequestContext
from grox.project import GroxProject

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("grox", "templates"),
    autoescape=select_autoescape(["j2"])
)

@click.group()
def cli():
    """Grox CLI: project lifecycle manager"""
    pass

@cli.command()
@click.argument("project_code")
@click.option("--path", "-p", default=".", help="Target directory for the project")
def create(project_code: str, path: str):
    """Create a new grox project in the given directory."""
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

    # Render templates
    ctx = {"project_code": project_code}
    (target_dir / "main.py").write_text(
        env.get_template("main.py.j2").render(**ctx)
    )
    (target_dir / "grox.yaml").write_text(
        env.get_template("grox.yaml.j2").render(**ctx)
    )

    click.echo(f"✅ Project '{project_code}' created at {target_dir}")


@cli.command()
@click.argument("project_code")
@click.option("--path", "-p", default=".", help="Project directory (defaults to current dir)")
def run(project_code: str, path: str):
    """Run the given grox project (calls main.py in the project folder)."""
    project_dir = Path(path) / project_code
    main_path = project_dir / "main.py"
    config_path = project_dir / "grox.yaml"

    if not main_path.exists():
        click.echo(f"❌ main.py not found in {project_dir}")
        sys.exit(1)

    if not config_path.exists():
        click.echo(f"❌ grox.yaml not found in {project_dir}")
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
