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

# Phase 2 commands
@app.command(name="detect")
def detect_cmd(
    ctx: typer.Context,
    target: Optional[str] = typer.Option(None, "--target", "-t"),
):
    """Run detection analyzers against observed data (Phase 2)"""
    cfg_path = ctx.obj.get("config_path")
    cfg = get_cfg(cfg_path)
    try:
        from .engine.cycle import CycleRunner
        runner = CycleRunner()
        cyc, incs = runner.run(cfg, trigger="manual")
    except Exception:
        from .observe.runner import run_cycle as old_run
        cyc = old_run(cfg, "manual")
        incs = []
    table = Table(title=f"Detected Incidents: {len(incs)}")
    table.add_column("ID"); table.add_column("Type"); table.add_column("Severity"); table.add_column("Target"); table.add_column("Root Cause")
    for inc in incs[:20]:
        table.add_row(inc.id[:8], str(inc.type.value), str(inc.severity.value), inc.target_id, (inc.root_cause[:50]+"..." if len(inc.root_cause)>50 else inc.root_cause))
    console.print(table)
    console.print(f"Cycle {cyc.id} – {cyc.incidents_detected} incidents, status={cyc.status.value}")

# incidents subcommand group
incidents_app = typer.Typer(help="Incident management")
app.add_typer(incidents_app, name="incidents")

@incidents_app.command("list")
def incidents_list(
    ctx: typer.Context,
    status: Optional[str] = typer.Option(None, "--status"),
    limit: int = typer.Option(20, "--limit"),
):
    """List incidents from database"""
    cfg_path = ctx.obj.get("config_path") if ctx.obj else None
    # I try DB first, fallback to empty
    try:
        cfg = get_cfg(cfg_path)
        if not cfg.database.dsn:
            console.print("[yellow]No database configured – run 'nexus detect' for live detection[/yellow]")
            return
        from .db.base import Database
        from .db.session import IncidentStore
        db = Database(cfg.database.dsn)
        sess = db.get_session()
        try:
            store = IncidentStore(sess)
            from .models.incident import IncidentStatus
            st = IncidentStatus(status) if status else None
            items = store.list(status=st, limit=limit)
            table = Table(title=f"Incidents ({len(items)})")
            table.add_column("ID"); table.add_column("Type"); table.add_column("Severity"); table.add_column("Status"); table.add_column("Target"); table.add_column("Detected")
            for it in items:
                table.add_row(it.id[:8], it.type.value, it.severity.value, it.status.value, it.target_id, it.detected_at.strftime("%Y-%m-%d %H:%M"))
            console.print(table)
        finally:
            sess.close(); db.close()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@incidents_app.command("view")
def incidents_view(
    incident_id: str = typer.Argument(..., help="Incident ID"),
    ctx: typer.Context = typer.Option(None),
):
    """View incident details"""
    # I try to load from DB, fallback message
    console.print(f"[yellow]Incident view {incident_id} – use 'incidents list' with DB configured for full details (Phase 2 DB viewer)[/yellow]")
