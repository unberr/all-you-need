# Python

## Toolchain (use what pyproject.toml declares; these are the common defaults)
- Version from `requires-python`. Environment manager from the lockfile (`uv.lock`, `poetry.lock`, `Pipfile.lock`, `requirements*.txt`).
- Format: `ruff format` (or `black`). Lint: `ruff check`. Types: `pyright` or `mypy --strict`. Tests: `pytest`.
- Security: `pip-audit` for dependencies, `bandit -r <pkg>` for code patterns.

## Idioms that prevent defects
- Type-hint every public function and class attribute. Use `X | None`, not implicit `None` defaults.
- No mutable default arguments (`def f(x=[])`): default to `None` and create inside.
- `is None` for None checks. Specific exceptions, `raise NewError(...) from err` to keep the cause. No bare `except:`.
- Context managers for files, locks, connections: `with open(path, encoding="utf-8") as f`. Always pass an encoding.
- `pathlib.Path` over string paths. `dataclasses` (or pydantic at input boundaries) over loose dicts. `enum.Enum` over magic strings.
- Generators and iterators for large data instead of building lists. Comprehensions for simple transforms, loops when logic is not simple.
- `logging` with lazy formatting (`logger.info("x %s", x)`), never `print` in library code. No `from x import *`.
- Timezone-aware datetimes: `datetime.now(timezone.utc)`. `datetime.utcnow()` is deprecated.
- `Decimal` for money. `math.isclose` for float comparison.
- Closures in loops capture the variable, not the value: bind with a default argument or `functools.partial`.

## Async
- Never call blocking I/O or `time.sleep` inside `async def`; use async libraries or `asyncio.to_thread`.
- Bound concurrency and set timeouts (`asyncio.timeout`, 3.11+). Prefer `asyncio.TaskGroup` (3.11+) over unmanaged `create_task` so errors are not lost. Keep a reference to every task you create.

## Security
- `subprocess.run([...], check=True)` with an argument list; never `shell=True` with input.
- `yaml.safe_load`, never `pickle` or `marshal` on untrusted data. Parameterized SQL (`cursor.execute(sql, params)`), never f-strings.
- `secrets` module for tokens, `hmac.compare_digest` for secret comparison, a slow password hash (argon2, bcrypt, scrypt) for passwords. `tempfile` for temp files, not predictable names.
- Frameworks: Django keeps `DEBUG=False`, `ALLOWED_HOSTS` set and CSRF on in production; Flask and FastAPI validate request bodies with typed models and set explicit CORS origins.

## Testing
- `pytest` with fixtures and `@pytest.mark.parametrize`. Fake time, network and randomness. Use `tmp_path` for files.
- Property tests with `hypothesis` for parsers, serializers and invariants.
