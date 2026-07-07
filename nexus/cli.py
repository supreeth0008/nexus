import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from .config.settings import default_yaml, load_config, redacted_dsn
from .utils.logging import init_logger
from .utils.version import build_info
app=typer.Typer(help="Nexus is an autonomous infrastructure control plane", no_args_is_help=True)
console=Console()
@app.callback()
def main(ctx: typer.Context, config: Optional[str]=typer.Option(None,"--config","-c"), log_level: str=typer.Option("info","--log-level"), log_format: str=typer.Option("text","--log-format")):
    init_logger(log_level, log_format)
    ctx.obj={"config_path":config}
def get_cfg(cp):
    try: return load_config(cp)
    except Exception: 
        from .config.settings import Settings
        return Settings()
@app.command()
def init(name: str=typer.Option("my-project","--name","-n")):
    p=Path("nexus.yaml")
    if p.exists(): console.print(f"[red]{p} exists[/red]"); raise typer.Exit(1)
    p.write_text(default_yaml(name))
    console.print(f"Created {p} for project \"{name}\"")
@app.command()
def status(ctx: typer.Context):
    cfg=get_cfg(ctx.obj.get("config_path"))
    console.print(f"Project:        {cfg.project.name}")
    console.print(f"Autonomy level: {cfg.autonomy.level} ({cfg.autonomy.level_name()})")
    console.print(f"Database:       {redacted_dsn(cfg.database.dsn)}")
    if not cfg.targets:
        console.print("Targets:        No targets configured"); return
    console.print(f"Targets:        {len(cfg.targets)} configured")
    for t in cfg.targets: console.print(f"  - {t.name} ({t.provider}) {t.endpoint}")
@app.command()
def version():
    i=build_info()
    console.print(f"Nexus {i['version']}")
    console.print(f"  commit:     {i['commit']}")
    console.print(f"  built:      {i['date']}")
    console.print(f"  python:     {i['python_version']}")
@app.command()
def observe(ctx: typer.Context, target: Optional[str]=typer.Option(None,"--target","-t")):
    cfg=get_cfg(ctx.obj.get("config_path"))
    from .observe.runner import observe_all
    results=observe_all(cfg, target)
    table=Table(title="Observe Results")
    for col in ["Target","Provider","Status","Signals","Duration ms"]: table.add_column(col)
    for r in results: table.add_row(r.target_name, r.provider, r.status, str(len(r.signals)), str(r.duration_ms))
    console.print(table)
@app.command()
def cycle(ctx: typer.Context, trigger: str=typer.Option("manual")):
    cfg=get_cfg(ctx.obj.get("config_path"))
    from .observe.runner import run_cycle
    c=run_cycle(cfg, trigger)
    console.print(f"Cycle {c.id} completed: {c.incidents_detected} incidents detected")
@app.command()
def migrate(ctx: typer.Context):
    cfg=get_cfg(ctx.obj.get("config_path"))
    if not cfg.database.dsn: console.print("[red]database.dsn not configured[/red]"); raise typer.Exit(1)
    from .db.base import Database
    db=Database(cfg.database.dsn)
    db.migrate(); console.print("[green]Migrations applied[/green]"); db.close()
if __name__=="__main__": app()
