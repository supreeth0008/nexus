import time, random
from dataclasses import dataclass
from typing import Callable, TypeVar
T=TypeVar("T")
@dataclass
class RetryConfig:
    max_attempts:int=5; initial_delay:float=0.5; max_delay:float=30.0; multiplier:float=2.0; jitter:float=0.2
def default_retry_config()->RetryConfig: return RetryConfig()
def retry(cfg:RetryConfig, fn:Callable[[],T])->T:
    delay=cfg.initial_delay; last_err=None
    for attempt in range(1,cfg.max_attempts+1):
        try: return fn()
        except Exception as e:
            last_err=e
            if attempt==cfg.max_attempts: break
            time.sleep(delay+random.random()*cfg.jitter*delay)
            delay=min(delay*cfg.multiplier,cfg.max_delay)
    raise RuntimeError(f"all {cfg.max_attempts} attempts failed: {last_err}") from last_err
