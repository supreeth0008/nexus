from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field
class ProjectConfig(BaseModel):
    name: str="nexus-project"; environment: str="dev"
class AutonomyConfig(BaseModel):
    level: int=Field(0, ge=0, le=4)
    def level_name(self) -> str:
        return {0:"observe only",1:"recommend",2:"auto-fix low risk",3:"auto-fix with policy gate",4:"full autonomy"}.get(self.level,"unknown")
class DatabaseConfig(BaseModel):
    dsn: str=""
class EngineConfig(BaseModel):
    cycle_interval: str="5m"; http_port: int=Field(8080, ge=1, le=65535)
class TargetConfig(BaseModel):
    name: str; provider: str; endpoint: str; region: str=""
class Settings(BaseModel):
    project: ProjectConfig=Field(default_factory=ProjectConfig)
    autonomy: AutonomyConfig=Field(default_factory=AutonomyConfig)
    database: DatabaseConfig=Field(default_factory=DatabaseConfig)
    engine: EngineConfig=Field(default_factory=EngineConfig)
    targets: List[TargetConfig]=Field(default_factory=list)
VALID_PROVIDERS={"aws","azure","gcp","kubernetes","localstack","prometheus"}
def validate_settings(s: Settings) -> None:
    if not s.project.name: raise ValueError("project.name must not be empty")
    if not (0 <= s.autonomy.level <= 4): raise ValueError("autonomy.level must be 0-4")
    seen=set()
    for i,t in enumerate(s.targets):
        if not t.name: raise ValueError(f"targets[{i}].name empty")
        if t.name in seen: raise ValueError(f"duplicate target {t.name}")
        seen.add(t.name)
        if t.provider not in VALID_PROVIDERS: raise ValueError(f"unknown provider {t.provider}")
        if not t.endpoint: raise ValueError(f"targets[{i}] endpoint empty")
def load_config(path: Optional[str]=None) -> Settings:
    cfg_path=path or "nexus.yaml"
    data={}
    if Path(cfg_path).exists():
        with open(cfg_path) as f: data=yaml.safe_load(f) or {}
    # env overrides
    mapping={"NEXUS_PROJECT_NAME":("project","name"),"NEXUS_AUTONOMY_LEVEL":("autonomy","level"),"NEXUS_DATABASE_DSN":("database","dsn"),"NEXUS_ENGINE_HTTP_PORT":("engine","http_port")}
    for ek,kp in mapping.items():
        if ek in os.environ:
            cur=data
            for k in kp[:-1]: cur=cur.setdefault(k,{})
            v=os.environ[ek]
            if kp[-1] in ("level","http_port"):
                try: v=int(v)
                except: pass
            cur[kp[-1]]=v
    s=Settings(**data)
    validate_settings(s)
    return s
def default_yaml(project_name: str) -> str:
    return f"""project:\n  name: {project_name}\n  environment: dev\nautonomy:\n  level: 0\ndatabase:\n  dsn: ""\nengine:\n  cycle_interval: 5m\n  http_port: 8080\ntargets: []\n"""
def redacted_dsn(dsn: str) -> str:
    if not dsn: return "(not configured)"
    try:
        from urllib.parse import urlparse, urlunparse
        u=urlparse(dsn)
        if u.password:
            netloc=u.netloc.replace(f":{u.password}@",":REDACTED@",1)
            return urlunparse(u._replace(netloc=netloc))
        return dsn
    except Exception:
        return dsn
