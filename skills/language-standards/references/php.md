# PHP

## Toolchain (use what composer.json and the project declare)
- PHP version from `composer.json` (`require.php`). Check: `php -l <file>` for syntax, `phpstan analyse` (or `psalm`) at the strictest level the project allows, `phpcs` or `php-cs-fixer` against PSR-12, `phpunit` or `pest` for tests, `composer validate`, `composer audit` for dependency advisories.
- Commit `composer.lock`. Autoload with PSR-4; no manual `require` chains.

## Idioms that prevent defects
- Start every file with `declare(strict_types=1);`. Type every parameter, return value and property. Use enums, `readonly` properties and constructor promotion, `match` instead of `switch`, and the nullsafe operator `?->`.
- Use `===` and `!==`. Loose `==` converts types (`"abc" == 0` changed in PHP 8, but `"1" == "01"` and `"10" == "1e1"` are still true). Pass `true` as the third argument to `in_array` and `array_search`.
- Handle errors with exceptions; set `error_reporting(E_ALL)` in development, `display_errors=0` and logging on in production. Do not use the `@` operator.
- Do not rely on globals or superglobals deep in the code: read `$_GET`, `$_POST`, `$_SERVER` once at the edge, validate, and pass typed values inward.
- `DateTimeImmutable` with explicit timezones. Integers or a decimal library (`bcmath`) for money.

## Security
- Database: PDO with prepared statements and bound parameters (`PDO::ATTR_EMULATE_PREPARES => false`, `PDO::ERRMODE_EXCEPTION`). Never interpolate input into SQL.
- Output: `htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')` for HTML, or a template engine that escapes by default (Twig, Blade `{{ }}`).
- Passwords: `password_hash` and `password_verify`. Tokens: `random_bytes` / `bin2hex`. Compare secrets with `hash_equals`. Never `md5`/`sha1` for passwords.
- Never `eval`, `extract` on request data, `include`/`require` with a user-controlled path (allowlist it), `unserialize` on untrusted data (use `json_decode`), or `system`/`exec`/`shell_exec` with input (`escapeshellarg` at minimum, an argument array with `proc_open` preferred).
- Uploads: check size, detect type with `finfo` (not the client-supplied type or extension), generate the stored name, store outside the web root, never execute them.
- Sessions: `session.cookie_httponly`, `cookie_secure`, `cookie_samesite=Lax` or `Strict`, `session_regenerate_id(true)` on login, CSRF token on state-changing forms.
- Frameworks: Laravel guards against mass assignment with `$fillable`, validates with Form Requests, keeps `APP_DEBUG=false` and `APP_KEY` secret in production, and uses `with()` to avoid N+1 queries. Symfony validates with constraints and uses the Security component for access control.

## Testing
- PHPUnit or Pest with an in-memory or disposable database, fake the clock and HTTP client, test validation with invalid input, run static analysis in CI.
